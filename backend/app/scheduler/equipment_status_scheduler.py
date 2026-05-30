"""
APScheduler job: poll Datalake for latest status_date and refresh parquet cache.

Cadence: EQUIPMENT_STATUS_POLL_INTERVAL_SECONDS (default 300s = 5 min).
Datalake itself ingests roughly every 10 min, so most ticks will be no-ops.

Timezone: Asia/Seoul (KST) — all app-controlled timestamps use KST.
Datalake-origin timestamps (status_date, lake_status_date) are stored as-is
from MySQL (naive), so comparisons between them stay consistent.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.services.equipment_status_cache import (
    read_job_status,
    write_current_parquet,
    write_job_status,
)
from app.services.equipment_status_collector import (
    collect_equipment_status_from_lake,
    get_latest_lake_status_date,
)

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
_run_lock = threading.Lock()
JOB_ID = "equipment_status_refresh"


def _kst() -> ZoneInfo:
    return ZoneInfo(get_settings().APP_TIMEZONE)


def _now_kst() -> datetime:
    return datetime.now(_kst())


def _parse_iso(value: Any) -> datetime | None:
    """Parse an ISO string back to datetime. Returns naive if no tz info."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _strip_tz(dt: datetime | None) -> datetime | None:
    """Strip timezone for comparison against naive Datalake datetimes."""
    if dt is None:
        return None
    return dt.replace(tzinfo=None)


def run_refresh(force: bool = False) -> dict[str, Any]:
    """
    Single execution of the refresh job. Safe to call from the scheduler
    or from the manual /refresh-now endpoint.
    """
    if not _run_lock.acquire(blocking=False):
        return {"ran_full_query": False, "skipped_reason": "Another refresh is already running."}

    try:
        check_time = _now_kst()
        updates: dict[str, Any] = {"last_check_time": check_time, "last_error_message": None}

        try:
            latest = get_latest_lake_status_date()  # naive datetime from MySQL
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to probe latest_status_date")
            updates["last_error_message"] = f"latest_status_date probe failed: {exc}"
            write_job_status(updates)
            return {"ran_full_query": False, "skipped_reason": updates["last_error_message"]}

        prior = read_job_status()
        # last_lake_status_date stored as naive ISO; strip tz before comparing
        prior_latest = _strip_tz(_parse_iso(prior.get("last_lake_status_date")))

        if latest is None:
            updates["last_full_query_skipped_reason"] = "Lake returned no status_date."
            write_job_status(updates)
            return {"ran_full_query": False, "skipped_reason": updates["last_full_query_skipped_reason"]}

        if not force and prior_latest is not None and latest == prior_latest:
            updates["last_full_query_skipped_reason"] = "Lake status_date has not changed."
            write_job_status(updates)
            return {"ran_full_query": False, "skipped_reason": updates["last_full_query_skipped_reason"]}

        try:
            df = collect_equipment_status_from_lake()
            write_current_parquet(df)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Full query / parquet write failed")
            updates["last_error_message"] = f"Full query failed: {exc}"
            write_job_status(updates)
            return {"ran_full_query": False, "skipped_reason": updates["last_error_message"]}

        updates.update(
            {
                "last_lake_status_date": latest,
                "last_success_collect_time": _now_kst(),
                "last_full_query_skipped_reason": None,
            }
        )
        write_job_status(updates)
        return {"ran_full_query": True, "skipped_reason": None}
    finally:
        _run_lock.release()


def _scheduled_run() -> None:
    try:
        run_refresh(force=False)
    finally:
        if _scheduler is not None:
            job = _scheduler.get_job(JOB_ID)
            if job is not None and job.next_run_time is not None:
                # next_run_time from APScheduler is KST-aware; store as ISO with +09:00
                write_job_status({"next_run_time": job.next_run_time})


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    interval = get_settings().EQUIPMENT_STATUS_POLL_INTERVAL_SECONDS
    tz = _kst()
    _scheduler = BackgroundScheduler(timezone=tz)
    _scheduler.add_job(
        _scheduled_run,
        trigger=IntervalTrigger(seconds=interval, timezone=tz),
        id=JOB_ID,
        max_instances=1,
        coalesce=True,
        replace_existing=True,
        next_run_time=_now_kst(),
    )
    _scheduler.start()

    write_job_status(
        {
            "scheduler_enabled": True,
            "poll_interval_seconds": interval,
        }
    )
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        write_job_status({"scheduler_enabled": False})


def get_scheduler() -> BackgroundScheduler | None:
    return _scheduler
