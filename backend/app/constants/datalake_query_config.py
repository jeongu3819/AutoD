"""
Datalake table / column configuration.

실제 DataLake 상태 테이블 컬럼:
  lineid, eqpid, status, status_date, reasoncode, username,
  eqp_comment, pre_status, pre_status_date, first_down_date, backup_date

1-Step에서 사용할 컬럼 (7개):
  lineid, eqpid, status, status_date, pre_status, backup_date, first_down_date

제외 컬럼 (향후 단계에서 추가):
  reasoncode, username, eqp_comment, pre_status_date
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
        "backup_date": s.DATALAKE_BACKUP_DATE_COLUMN,
        "first_down_date": s.DATALAKE_FIRST_DOWN_DATE_COLUMN,
    }


REQUIRED_COLUMNS_LOGICAL = [
    "line", "eqp_id", "raw_status", "status_date",
    "pre_status", "backup_date", "first_down_date",
]
