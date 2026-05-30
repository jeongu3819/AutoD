"""
Summary builders for the current parquet snapshot.

Phase 1 risk_level rules (PRC_GROUP):
- unavailable == 0           -> NORMAL
- 0 < unavailable < total    -> WARNING
- available == 0             -> CRITICAL
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from app.constants.status_mapping import PM_BU_STATUSES


def _empty_summary() -> dict[str, int]:
    return {
        "total": 0,
        "available": 0,
        "unavailable": 0,
        "run": 0,
        "idle": 0,
        "down": 0,
        "local": 0,
        "pm_bu": 0,
        "unknown": 0,
    }


def _count_bucket(rows: pd.DataFrame, key: str) -> int:
    if "normalized_status" not in rows.columns:
        return 0
    return int((rows["normalized_status"] == key).sum())


def _bucket_for(rows: pd.DataFrame) -> dict[str, int]:
    if rows.empty:
        return _empty_summary()
    available_mask = rows["production_available"].fillna(False).astype(bool)
    total = int(len(rows))
    available = int(available_mask.sum())
    unavailable = total - available
    pm_bu = int(rows["normalized_status"].isin(PM_BU_STATUSES).sum())
    return {
        "total": total,
        "available": available,
        "unavailable": unavailable,
        "run": _count_bucket(rows, "RUN"),
        "idle": _count_bucket(rows, "IDLE"),
        "down": _count_bucket(rows, "DOWN"),
        "local": _count_bucket(rows, "LOCAL"),
        "pm_bu": pm_bu,
        "unknown": _count_bucket(rows, "UNKNOWN"),
    }


def _risk_level(total: int, available: int, unavailable: int) -> str:
    if total == 0:
        return "NORMAL"
    if available == 0:
        return "CRITICAL"
    if unavailable >= 1:
        return "WARNING"
    return "NORMAL"


def build_summary(df: pd.DataFrame) -> dict[str, int]:
    return _bucket_for(df)


def build_line_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    out: list[dict[str, Any]] = []
    for lineid, group in df.groupby("lineid", sort=True):
        bucket = _bucket_for(group)
        out.append({"lineid": str(lineid), **bucket})
    return out


def build_tool_group_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "PRC_GROUP" not in df.columns:
        return []
    out: list[dict[str, Any]] = []
    for prc, group in df.groupby("PRC_GROUP", sort=True):
        bucket = _bucket_for(group)
        out.append(
            {
                "prc_group": str(prc),
                "total": bucket["total"],
                "available": bucket["available"],
                "unavailable": bucket["unavailable"],
                "risk_level": _risk_level(
                    bucket["total"], bucket["available"], bucket["unavailable"]
                ),
            }
        )
    return out


def _serialize(value: Any) -> Any:
    if isinstance(value, (pd.Timestamp, datetime)):
        return pd.Timestamp(value).isoformat()
    if value is pd.NA or (isinstance(value, float) and pd.isna(value)):
        return None
    return value


def items_from_df(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    for r in records:
        for k, v in list(r.items()):
            r[k] = _serialize(v)
    return records
