"""
Datalake table / column configuration.

Phase 1 queries only depend on these names. If the real table or column names
change, only this file needs to be updated.
"""

from app.config import get_settings


def get_table_name() -> str:
    return get_settings().DATALAKE_STATUS_TABLE


def get_column_map() -> dict[str, str]:
    s = get_settings()
    return {
        "line": s.DATALAKE_LINE_COLUMN,
        "eqp_id": s.DATALAKE_EQP_COLUMN,
        "raw_status": s.DATALAKE_STATUS_COLUMN,
        "status_date": s.DATALAKE_STATUS_DATE_COLUMN,
        "pre_status": s.DATALAKE_PRE_STATUS_COLUMN,
    }


REQUIRED_COLUMNS_LOGICAL = ["line", "eqp_id", "raw_status", "status_date", "pre_status"]
