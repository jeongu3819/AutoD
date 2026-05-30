from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MySQL connection string, e.g. mysql+pymysql://root:pw@127.0.0.1:3306/autoD
    DATABASE_URL: str = ""

    APP_TIMEZONE: str = "Asia/Seoul"

    EQUIPMENT_STATUS_POLL_INTERVAL_SECONDS: int = 300
    EQUIPMENT_STATUS_CURRENT_PATH: str = "data/current/equipment_status_current.parquet"
    EQUIPMENT_STATUS_JOB_STATUS_PATH: str = "data/meta/equipment_status_job_status.json"

    DATALAKE_STATUS_TABLE: str = "mo~~"
    DATALAKE_LINE_COLUMN: str = "lineid"
    DATALAKE_EQP_COLUMN: str = "eqpid"
    DATALAKE_STATUS_COLUMN: str = "status"
    DATALAKE_STATUS_DATE_COLUMN: str = "status_date"
    DATALAKE_PRE_STATUS_COLUMN: str = "pre_status"
    DATALAKE_BACKUP_DATE_COLUMN: str = "backup_date"
    DATALAKE_FIRST_DOWN_DATE_COLUMN: str = "first_down_date"


@lru_cache
def get_settings() -> Settings:
    return Settings()
