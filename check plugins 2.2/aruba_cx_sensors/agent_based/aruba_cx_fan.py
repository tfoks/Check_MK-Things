#!/usr/bin/env python3
'''check for Fan status of Aruba CX 6k switches'''
# -*- coding: utf-8 -*-
#
# License: GNU General Public License v2
#

from typing import Any, Dict, Optional

from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    Metric,
    OIDEnd,
    Result,
    Service,
    SNMPTree,
    State,
    register,
    startswith,
)
from cmk.base.plugins.agent_based.agent_based_api.v1.type_defs import (
    CheckResult,
    DiscoveryResult,
    StringTable,
)

Section = Dict[str, Any]


def parse_arbua_cx_fan(string_table: StringTable) -> Optional[Section]:
    '''parse raw snmp data to dictionary'''
    try:
        parsed = {}
        for line in string_table:
            parsed.setdefault(line[1], {"state": line[2], "rpm": int(line[3])})
        return parsed
    except IndexError:
        pass


def discovery_arbua_cx_fan(section: Section) -> DiscoveryResult:
    '''every key of the parsed data is found as a service'''
    for key in section.keys():
        yield Service(item=key)


def check_arbua_cx_fan(item, section: Section) -> CheckResult:
    '''check the status of the Fan'''
    data = section.get(item)
    if not data:
        return

    if data.get("state") != "ok":
        yield Result(state=State.WARN, summary=f"Status not ok --> {data.get('state')}")
    else:
        yield Result(state=State.OK, summary=f"Status is {data.get('state')}")

    if data.get("rpm") != 0:
        yield Metric(name="rpm", value=data.get("rpm", 0))


register.snmp_section(
    name="arbua_cx_fan",
    parse_function=parse_arbua_cx_fan,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.47196.4.1.1.3.11.5.1.1",
        oids=[
            OIDEnd(),
            "4",
            "5",
            "8",
        ],
    ),
    detect=startswith(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.47196.4.1.1.1.270"),
)

register.check_plugin(
    name="arbua_cx_fan",
    service_name="Fan %s",
    discovery_function=discovery_arbua_cx_fan,
    check_function=check_arbua_cx_fan,
)
