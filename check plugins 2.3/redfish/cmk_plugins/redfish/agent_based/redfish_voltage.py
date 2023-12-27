#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# (c) Andreas Doehler <andreas.doehler@bechtle.com/andreas.doehler@gmail.com>

# License: GNU General Public License v2

from cmk.agent_based.v2 import CheckPlugin, Result, Service, State, check_levels_fixed
from cmk.agent_based.v2.type_defs import CheckResult, DiscoveryResult
from cmk.plugins.redfish.lib import (
    RedfishAPIData,
    process_redfish_perfdata,
    redfish_health_state,
)


def discovery_redfish_voltage(section: RedfishAPIData) -> DiscoveryResult:
    data = section.get("Voltages", None)
    if not data:
        return
    for entry in data:
        if not entry.get("ReadingVolts"):
            continue
        yield Service(item=entry["Name"])


def check_redfish_voltage(item: str, section: RedfishAPIData) -> CheckResult:
    voltages = section.get("Voltages", None)
    if voltages is None:
        return

    for voltage in voltages:
        if voltage.get("Name") == item:
            perfdata = process_redfish_perfdata(voltage)

            volt_msg = (f"Location: {voltage.get('PhysicalContext')}, "
                        f"SensorNr: {voltage.get('SensorNumber')}")
            yield Result(state=State(0), summary=volt_msg)

            if perfdata.value is not None:
                yield from check_levels_fixed(
                    perfdata.value,
                    levels_upper=perfdata.levels_upper,
                    levels_lower=perfdata.levels_lower,
                    metric_name="voltage",
                    label="Value",
                    render_func=lambda v: f"{v:.1f} V",
                    boundaries=perfdata.boundaries,
                )

            dev_state, dev_msg = redfish_health_state(voltage["Status"])
            yield Result(state=State(dev_state), notice=dev_msg)


check_plugin_redfish_voltage = CheckPlugin(
    name="redfish_voltage",
    service_name="Voltage %s",
    sections=["redfish_power"],
    discovery_function=discovery_redfish_voltage,
    check_function=check_redfish_voltage,
)
