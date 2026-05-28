"""
Hard-coded managed equipment list for Phase 1.

In a later Phase, this should be replaced by an `equipment_master` DB table.
Keep this module as the single source of truth for what to query from the Datalake.
"""

MANAGED_EQUIPMENTS = [
    {"lineid": "LINE1", "eqpid": "CMP01", "eqp_name": "CMP01", "tool_group": "CMP_A"},
    {"lineid": "LINE1", "eqpid": "CMP02", "eqp_name": "CMP02", "tool_group": "CMP_A"},
    {"lineid": "LINE2", "eqpid": "CMP03", "eqp_name": "CMP03", "tool_group": "CMP_B"},
]


def get_managed_line_ids() -> list[str]:
    return sorted({e["lineid"] for e in MANAGED_EQUIPMENTS})


def get_managed_eqp_ids() -> list[str]:
    return sorted({e["eqpid"] for e in MANAGED_EQUIPMENTS})


def get_managed_equipment_map() -> dict[tuple[str, str], dict]:
    """Lookup: (lineid, eqpid) -> {eqp_name, tool_group, ...}"""
    return {(e["lineid"], e["eqpid"]): e for e in MANAGED_EQUIPMENTS}
