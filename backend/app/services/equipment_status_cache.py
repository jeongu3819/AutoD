"""
Parquet cache + job status persistence for equipment status.

- Current parquet is overwritten atomically (write to .tmp, then os.replace).
- job_status.json is written through a temp file as well to avoid partial reads.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import get_settings


def _current_parquet_path() -> Path:
    return Path(get_settings().EQUIPMENT_STATUS_CURRENT_PATH)


def _job_status_path() -> Path:
    return Path(get_settings().EQUIPMENT_STATUS_JOB_STATUS_PATH)


def write_current_parquet(df: pd.DataFrame) -> None:
    final_path = _current_parquet_path()
    final_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix="equipment_status_current.", suffix=".tmp.parquet", dir=str(final_path.parent)
    )
    os.close(tmp_fd)
    try:
        df.to_parquet(tmp_name, index=False)
        os.replace(tmp_name, final_path)
    except Exception:
        try:
            os.remove(tmp_name)
        except OSError:
            pass
        raise


def read_current_parquet() -> pd.DataFrame | None:
    path = _current_parquet_path()
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return str(value)


def read_job_status() -> dict[str, Any]:
    path = _job_status_path()
    if not path.exists():
        return {
            "scheduler_enabled": False,
            "poll_interval_seconds": get_settings().EQUIPMENT_STATUS_POLL_INTERVAL_SECONDS,
            "last_check_time": None,
            "last_lake_status_date": None,
            "last_success_collect_time": None,
            "last_full_query_skipped_reason": None,
            "last_error_message": None,
            "next_run_time": None,
        }
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_job_status(updates: dict[str, Any]) -> dict[str, Any]:
    """Merge `updates` into the existing job status and persist atomically."""
    status = read_job_status()
    for k, v in updates.items():
        if isinstance(v, datetime):
            status[k] = v.isoformat()
        else:
            status[k] = v

    path = _job_status_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix="equipment_status_job_status.", suffix=".tmp.json", dir=str(path.parent)
    )
    os.close(tmp_fd)
    try:
        with open(tmp_name, "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.remove(tmp_name)
        except OSError:
            pass
        raise
    return status
