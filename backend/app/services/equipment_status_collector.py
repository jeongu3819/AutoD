"""
Datalake collector for equipment status (Phase 1).

Principles:
- Never SELECT *. Only select the 7 required columns.
- Never rely on LIMIT.
- Always restrict to managed equipment via whitelists from managed_equipments.py.
- Two query modes:
  1. get_latest_lake_status_date(): cheap MAX(status_date) probe.
  2. collect_equipment_status_from_lake(): full query, per-equipment latest row,
     run only when latest_status_date has actually changed.

1-Step 조회 컬럼: lineid, eqpid, status, status_date, pre_status, backup_date, first_down_date
제외 컬럼 (향후): reasoncode, username, eqp_comment, pre_status_date
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from sqlalchemy import text

from app.config import get_settings
from app.constants.datalake_query_config import get_column_map, get_table_name
from app.constants.managed_equipments import (
    MANAGED_EQUIPMENTS,
    get_managed_eqp_ids,
    get_managed_equipment_map,
    get_managed_line_ids,
    normalize_multi,
)
from app.constants.status_mapping import is_production_available, normalize_status
from app.db import get_engine


def _kst() -> ZoneInfo:
    return ZoneInfo(get_settings().APP_TIMEZONE)


def _build_in_clause(prefix: str, values: list[str]) -> tuple[str, dict[str, Any]]:
    """Build a safe `col IN (:p0, :p1, ...)` fragment with bound parameters."""
    if not values:
        return "1 = 0", {}
    keys = [f"{prefix}{i}" for i in range(len(values))]
    placeholders = ", ".join(f":{k}" for k in keys)
    params = {k: v for k, v in zip(keys, values)}
    return placeholders, params


def get_latest_lake_status_date() -> datetime | None:
    """
    Probe MAX(status_date) for managed equipment only.
    Returns a naive datetime (MySQL stores without tz).
    Returns None when the DB is not configured or no rows exist.
    """
    engine = get_engine()
    if engine is None:
        return None

    cols = get_column_map()
    table = get_table_name()
    line_ids = get_managed_line_ids()
    eqp_ids = get_managed_eqp_ids()

    line_in, line_params = _build_in_clause("line_", line_ids)
    eqp_in, eqp_params = _build_in_clause("eqp_", eqp_ids)

    sql = text(
        f"""
        SELECT MAX({cols['status_date']}) AS latest_status_date
        FROM {table}
        WHERE {cols['line']} IN ({line_in})
          AND {cols['eqp_id']} IN ({eqp_in})
        """
    )
    params = {**line_params, **eqp_params}

    with engine.connect() as conn:
        row = conn.execute(sql, params).first()

    if not row or row[0] is None:
        return None

    val = row[0]
    if isinstance(val, datetime):
        return val
    return pd.to_datetime(val).to_pydatetime()


def _fetch_latest_rows_per_equipment() -> pd.DataFrame:
    """
    Per-equipment latest row (MySQL 8.0+ ROW_NUMBER window function).
    Selects only the 7 required columns for Phase 1.

    Fallback for MySQL 5.7: swap call in collect_equipment_status_from_lake()
    to _fetch_latest_rows_per_equipment_fallback().
    """
    engine = get_engine()
    if engine is None:
        return pd.DataFrame(
            columns=["lineid", "eqpid", "status", "status_date",
                     "pre_status", "backup_date", "first_down_date"]
        )

    cols = get_column_map()
    table = get_table_name()
    line_ids = get_managed_line_ids()
    eqp_ids = get_managed_eqp_ids()

    line_in, line_params = _build_in_clause("line_", line_ids)
    eqp_in, eqp_params = _build_in_clause("eqp_", eqp_ids)

    sql = text(
        f"""
        WITH latest_status AS (
            SELECT
                {cols['line']}           AS lineid,
                {cols['eqp_id']}         AS eqpid,
                {cols['raw_status']}     AS status,
                {cols['status_date']}    AS status_date,
                {cols['pre_status']}     AS pre_status,
                {cols['backup_date']}    AS backup_date,
                {cols['first_down_date']} AS first_down_date,
                ROW_NUMBER() OVER (
                    PARTITION BY {cols['line']}, {cols['eqp_id']}
                    ORDER BY {cols['status_date']} DESC
                ) AS rn
            FROM {table}
            WHERE {cols['line']} IN ({line_in})
              AND {cols['eqp_id']} IN ({eqp_in})
        )
        SELECT lineid, eqpid, status, status_date,
               pre_status, backup_date, first_down_date
        FROM latest_status
        WHERE rn = 1
        """
    )
    params = {**line_params, **eqp_params}

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)

    return df


def _fetch_latest_rows_per_equipment_fallback() -> pd.DataFrame:
    """
    MySQL 5.7 fallback: GROUP BY + MAX(status_date) self-join.

    To use: replace the call in collect_equipment_status_from_lake():
        raw_df = _fetch_latest_rows_per_equipment_fallback()
    """
    engine = get_engine()
    if engine is None:
        return pd.DataFrame(
            columns=["lineid", "eqpid", "status", "status_date",
                     "pre_status", "backup_date", "first_down_date"]
        )

    cols = get_column_map()
    table = get_table_name()
    line_ids = get_managed_line_ids()
    eqp_ids = get_managed_eqp_ids()

    line_in_outer, line_params_outer = _build_in_clause("line_o_", line_ids)
    eqp_in_outer, eqp_params_outer = _build_in_clause("eqp_o_", eqp_ids)
    line_in_inner, line_params_inner = _build_in_clause("line_i_", line_ids)
    eqp_in_inner, eqp_params_inner = _build_in_clause("eqp_i_", eqp_ids)

    sql = text(
        f"""
        SELECT
            t.{cols['line']}            AS lineid,
            t.{cols['eqp_id']}          AS eqpid,
            t.{cols['raw_status']}      AS status,
            t.{cols['status_date']}     AS status_date,
            t.{cols['pre_status']}      AS pre_status,
            t.{cols['backup_date']}     AS backup_date,
            t.{cols['first_down_date']} AS first_down_date
        FROM {table} t
        JOIN (
            SELECT
                {cols['line']}   AS lineid,
                {cols['eqp_id']} AS eqpid,
                MAX({cols['status_date']}) AS max_status_date
            FROM {table}
            WHERE {cols['line']} IN ({line_in_inner})
              AND {cols['eqp_id']} IN ({eqp_in_inner})
            GROUP BY {cols['line']}, {cols['eqp_id']}
        ) latest
          ON t.{cols['line']}        = latest.lineid
         AND t.{cols['eqp_id']}      = latest.eqpid
         AND t.{cols['status_date']} = latest.max_status_date
        WHERE t.{cols['line']} IN ({line_in_outer})
          AND t.{cols['eqp_id']} IN ({eqp_in_outer})
        """
    )
    params = {
        **line_params_outer, **eqp_params_outer,
        **line_params_inner, **eqp_params_inner,
    }

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)

    return df


def collect_equipment_status_from_lake() -> pd.DataFrame:
    """
    Full collection path. Returns the dataframe to be persisted to parquet.

    Parquet columns:
        lineid, eqpid,
        PRC_GROUP, FDC_MODEL, eqp_model, area, sdwt,
        chamber_step, param_name, grade, recipe_id, unit_name,
        status, status_date, pre_status, backup_date, first_down_date,
        normalized_status, production_available,
        collect_status, error_message, collected_at

    collect_status: "SUCCESS" | "NO_DATA"
    error_message : None when SUCCESS
    collected_at  : KST-aware datetime (stored as UTC in parquet via utc=True)
    """
    raw_df = _fetch_latest_rows_per_equipment()
    eqp_map = get_managed_equipment_map()
    collected_at = datetime.now(_kst())

    raw_indexed: dict[tuple[str, str], dict[str, Any]] = {}
    if not raw_df.empty:
        for _, r in raw_df.iterrows():
            raw_indexed[(str(r["lineid"]), str(r["eqpid"]))] = r.to_dict()

    rows: list[dict[str, Any]] = []
    for eqp in MANAGED_EQUIPMENTS:
        key = (eqp["lineid"], eqp["eqpid"])
        meta = eqp_map[key]
        raw = raw_indexed.get(key)

        if raw is not None:
            status = raw.get("status")
            pre_status = raw.get("pre_status")
            status_date = raw.get("status_date")
            backup_date = raw.get("backup_date")
            first_down_date = raw.get("first_down_date")
            collect_status = "SUCCESS"
            error_message = None
        else:
            status = pre_status = status_date = None
            backup_date = first_down_date = None
            collect_status = "NO_DATA"
            error_message = "No data found in Lake for this equipment"

        normalized = normalize_status(status)
        available = is_production_available(normalized)

        rows.append(
            {
                "lineid": eqp["lineid"],
                "eqpid": eqp["eqpid"],
                "PRC_GROUP": meta.get("PRC_GROUP"),
                "FDC_MODEL": meta.get("FDC_MODEL"),
                "eqp_model": meta.get("eqp_model"),
                "area": meta.get("area"),
                "sdwt": meta.get("sdwt"),
                "chamber_step": ",".join(normalize_multi(meta.get("chamber_step"))),
                "param_name": ",".join(normalize_multi(meta.get("param_name"))),
                "grade": ",".join(normalize_multi(meta.get("grade"))),
                "recipe_id": ",".join(normalize_multi(meta.get("recipe_id"))),
                "unit_name": ",".join(normalize_multi(meta.get("unit_name"))),
                "status": status,
                "status_date": status_date,
                "pre_status": pre_status,
                "backup_date": backup_date,
                "first_down_date": first_down_date,
                "normalized_status": normalized,
                "production_available": available,
                "collect_status": collect_status,
                "error_message": error_message,
                "collected_at": collected_at,
            }
        )

    df = pd.DataFrame(rows)
    for col in ("status_date", "backup_date", "first_down_date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    df["collected_at"] = pd.to_datetime(df["collected_at"], utc=True)
    return df
