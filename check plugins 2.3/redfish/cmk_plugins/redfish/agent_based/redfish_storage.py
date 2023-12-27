#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# License: GNU General Public License v2

from cmk.agent_based.v2 import AgentSection, CheckPlugin, Result, Service, State
from cmk.agent_based.v2.type_defs import CheckResult, DiscoveryResult
from cmk.plugins.redfish.lib import (
    RedfishAPIData,
    parse_redfish_multiple,
    redfish_health_state,
)


agent_section_redfish_storage = AgentSection(
    name="redfish_storage",
    parse_function=parse_redfish_multiple,
    parsed_section_name="redfish_storage",
)


def discovery_redfish_storage(section: RedfishAPIData) -> DiscoveryResult:
    """Discover single controllers"""
    for key in section.keys():
        yield Service(item=section[key]["Id"])


def check_redfish_storage(item: str, section: RedfishAPIData) -> CheckResult:
    """Check single Controller state"""
    data = section.get(item, None)
    if data is None:
        return

    controller_list = data.get("StorageControllers", [])
    if len(controller_list) == 1:
        for ctrl_data in controller_list:
            storage_msg = (
                f"Type: {ctrl_data.get('Model')}, "
                f"RaidLevels: {','.join(ctrl_data.get('SupportedRAIDTypes', []))}, "
                f"DeviceProtocols: {','.join(ctrl_data.get('SupportedDeviceProtocols', []))}"
            )
            dev_state, dev_msg = redfish_health_state(ctrl_data.get("Status", {}))
            yield Result(state=State(dev_state), summary=storage_msg, details=dev_msg)
    elif len(controller_list) > 1:
        global_state = 0
        global_msg = ""
        for ctrl_data in controller_list:
            storage_msg = (
                f"Type: {ctrl_data.get('Model')}, "
                f"RaidLevels: {','.join(ctrl_data.get('SupportedRAIDTypes', []))}, "
                f"DeviceProtocols: {','.join(ctrl_data.get('SupportedDeviceProtocols', []))}"
            )
            dev_state, dev_msg = redfish_health_state(ctrl_data.get("Status", {}))
            global_state = max(global_state, dev_state)
            yield Result(state=State(dev_state), details=storage_msg, notice=dev_msg)
        if global_state != 0:
            global_msg = "One or more controllers with problems"
        else:
            global_msg = "All controllers are working properly"
        yield Result(state=State(global_state), summary=global_msg)
    else:
        dev_state, dev_msg = redfish_health_state(data.get("Status", {}))
        yield Result(state=State(dev_state), notice=dev_msg)


check_plugin_redfish_storate = CheckPlugin(
    name="redfish_storage",
    service_name="Storage controller %s",
    sections=["redfish_storage"],
    discovery_function=discovery_redfish_storage,
    check_function=check_redfish_storage,
)
