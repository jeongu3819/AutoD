from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class StatusSummary(BaseModel):
    total: int = 0
    available: int = 0
    unavailable: int = 0
    run: int = 0
    idle: int = 0
    down: int = 0
    local: int = 0
    pm_bu: int = 0
    unknown: int = 0


class LineSummary(StatusSummary):
    lineid: str


class PrcGroupSummary(BaseModel):
    prc_group: str
    total: int
    available: int
    unavailable: int
    risk_level: str


class EquipmentStatusItem(BaseModel):
    lineid: str
    eqpid: str
    # DataLake 상태 컬럼 (7개)
    status: str | None = None
    status_date: str | None = None
    pre_status: str | None = None
    backup_date: str | None = None
    first_down_date: str | None = None
    # 정규화/파생 필드
    normalized_status: str
    production_available: bool
    # 관리 대상 설비 메타정보 (managed_equipments.py)
    PRC_GROUP: str | None = None
    FDC_MODEL: str | None = None
    eqp_model: str | None = None
    area: str | None = None
    sdwt: str | None = None
    chamber_step: list[str] | str | None = None
    param_name: list[str] | str | None = None
    grade: list[str] | str | None = None
    recipe_id: list[str] | str | None = None
    unit_name: list[str] | str | None = None
    # 수집 메타정보
    collect_status: str | None = None
    error_message: str | None = None
    collected_at: str | None = None


class EquipmentStatusResponse(BaseModel):
    message: str
    data_source: str
    lake_status_date: str | None = None
    last_collected_at: str | None = None
    last_api_response_time: str
    source_file: str | None = None
    summary: StatusSummary
    line_summary: list[LineSummary] = []
    prc_group_summary: list[PrcGroupSummary] = []
    items: list[EquipmentStatusItem] = []


class JobStatusResponse(BaseModel):
    scheduler_enabled: bool
    poll_interval_seconds: int
    last_check_time: str | None = None
    last_lake_status_date: str | None = None
    last_success_collect_time: str | None = None
    last_full_query_skipped_reason: str | None = None
    last_error_message: str | None = None
    next_run_time: str | None = None


class RefreshNowResponse(BaseModel):
    ran_full_query: bool
    skipped_reason: str | None = None
    job_status: dict[str, Any]
