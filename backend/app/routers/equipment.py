from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from fastapi import APIRouter, Query

from app.config import get_settings
from app.scheduler.equipment_status_scheduler import run_refresh
from app.schemas.equipment import (
    EquipmentStatusResponse,
    JobStatusResponse,
    RefreshNowResponse,
)
from app.services.equipment_status_cache import read_current_parquet, read_job_status
from app.services.equipment_status_summary import (
    build_line_summary,
    build_summary,
    build_tool_group_summary,
    items_from_df,
)

router = APIRouter(prefix="/api/equipment", tags=["equipment"])


def _now_iso() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _max_ts(df: pd.DataFrame, col: str) -> str | None:
    if col not in df.columns or df[col].isna().all():
        return None
    ts = pd.to_datetime(df[col], utc=True, errors="coerce").max()
    return ts.isoformat() if pd.notna(ts) else None


@router.get("/status/current", response_model=EquipmentStatusResponse)
def get_current_status() -> EquipmentStatusResponse:
    """Return the cached parquet snapshot. Never queries the Datalake."""
    df = read_current_parquet()
    job = read_job_status()
    source_file = Path(get_settings().EQUIPMENT_STATUS_CURRENT_PATH).name

    if df is None or df.empty:
        return EquipmentStatusResponse(
            message="아직 수집된 상태 데이터가 없습니다.",
            data_source="parquet_cache",
            lake_status_date=job.get("last_lake_status_date"),
            last_collected_at=job.get("last_success_collect_time"),
            last_api_response_time=_now_iso(),
            source_file=source_file,
            summary={  # type: ignore[arg-type]
                "total": 0, "available": 0, "unavailable": 0,
                "run": 0, "idle": 0, "down": 0,
                "local": 0, "pm_bu": 0, "unknown": 0,
            },
            line_summary=[],
            prc_group_summary=[],
            items=[],
        )

    # status_date는 MySQL naive → 그대로 iso
    lake_status_date = None
    if "status_date" in df.columns and not df["status_date"].isna().all():
        ts = pd.to_datetime(df["status_date"], errors="coerce").max()
        if pd.notna(ts):
            lake_status_date = ts.isoformat()

    return EquipmentStatusResponse(
        message="OK",
        data_source="parquet_cache",
        lake_status_date=lake_status_date,
        last_collected_at=_max_ts(df, "collected_at"),
        last_api_response_time=_now_iso(),
        source_file=source_file,
        summary=build_summary(df),  # type: ignore[arg-type]
        line_summary=build_line_summary(df),  # type: ignore[arg-type]
        prc_group_summary=build_tool_group_summary(df),  # type: ignore[arg-type]
        items=items_from_df(df),  # type: ignore[arg-type]
    )


@router.post("/status/refresh-now", response_model=RefreshNowResponse)
def refresh_now(force: bool = Query(default=False)) -> RefreshNowResponse:
    """
    Development / test endpoint. Probes latest_status_date and runs a full query
    if changed. With force=true, the full query runs regardless.

    NOTE: In production this should be gated behind an admin-only auth check.
    """
    result = run_refresh(force=force)
    return RefreshNowResponse(
        ran_full_query=bool(result.get("ran_full_query")),
        skipped_reason=result.get("skipped_reason"),
        job_status=read_job_status(),
    )


@router.get("/status/job-status", response_model=JobStatusResponse)
def get_job_status() -> JobStatusResponse:
    job = read_job_status()
    return JobStatusResponse(**job)
