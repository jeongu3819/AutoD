"""
Datalake collector for equipment status (Phase 1).

Principles:
- Never SELECT *. Only select the 5 required columns.
- Never rely on LIMIT.
- Always restrict to managed equipment via whitelists from managed_equipments.py.
- Two query modes:
  1. get_latest_lake_status_date(): cheap MAX(status_date) probe.
  2. collect_equipment_status_from_lake(): full query, per-equipment latest row,
     run only when latest_status_date has actually changed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import text

from app.constants.datalake_query_config import get_column_map, get_table_name
from app.constants.managed_equipments import (
    MANAGED_EQUIPMENTS,
    get_managed_eqp_ids,
    get_managed_equipment_map,
    get_managed_line_ids,
)
from app.constants.status_mapping import is_production_available, normalize_status
from app.db import get_engine


def _build_in_clause(prefix: str, values: list[str]) -> tuple[str, dict[str, Any]]:
    """Build a safe `col IN (:p0, :p1, ...)` fragment with bound parameters."""
    if not values:
        # An always-false guard; we never want to query the whole table.
        return "1 = 0", {}
    keys = [f"{prefix}{i}" for i in range(len(values))]
    placeholders = ", ".join(f":{k}" for k in keys)
    params = {k: v for k, v in zip(keys, values)}
    return placeholders, params


def get_latest_lake_status_date() -> datetime | None:
    """
    Probe MAX(status_date) for managed equipment only.

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
    Per-equipment latest row. Targets MySQL 8.0+ via ROW_NUMBER() window function.

    Fallback for MySQL 5.7 or older engines without window functions: use the
    GROUP BY + JOIN form shown in _fetch_latest_rows_per_equipment_fallback().
    Swap the call in collect_equipment_status_from_lake() if needed.
    """
    engine = get_engine()
    if engine is None:
        return pd.DataFrame(
            columns=["lineid", "eqpid", "status", "status_date", "pre_status"]
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
                {cols['line']}        AS lineid,
                {cols['eqp_id']}      AS eqpid,
                {cols['raw_status']}  AS status,
                {cols['status_date']} AS status_date,
                {cols['pre_status']}  AS pre_status,
                ROW_NUMBER() OVER (
                    PARTITION BY {cols['line']}, {cols['eqp_id']}
                    ORDER BY {cols['status_date']} DESC
                ) AS rn
            FROM {table}
            WHERE {cols['line']} IN ({line_in})
              AND {cols['eqp_id']} IN ({eqp_in})
        )
        SELECT lineid, eqpid, status, status_date, pre_status
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
    MySQL 5.7 / no-window-function fallback. Same result shape as the primary
    function. Uses GROUP BY + MAX(status_date) and self-joins back to fetch the
    matching row's status / pre_status.

    To use this, replace the call in collect_equipment_status_from_lake():
        raw_df = _fetch_latest_rows_per_equipment_fallback()
    """
    engine = get_engine()
    if engine is None:
        return pd.DataFrame(
            columns=["lineid", "eqpid", "status", "status_date", "pre_status"]
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
            t.{cols['line']}        AS lineid,
            t.{cols['eqp_id']}      AS eqpid,
            t.{cols['raw_status']}  AS status,
            t.{cols['status_date']} AS status_date,
            t.{cols['pre_status']}  AS pre_status
        FROM {table} t
        JOIN (
            SELECT
                {cols['line']}        AS lineid,
                {cols['eqp_id']}      AS eqpid,
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
        **line_params_outer,
        **eqp_params_outer,
        **line_params_inner,
        **eqp_params_inner,
    }

    with engine.connect() as conn:
        df = pd.read_sql(sql, conn, params=params)

    return df


def collect_equipment_status_from_lake() -> pd.DataFrame:
    """
    Full collection path. Returns the dataframe to be persisted to parquet.

    Output columns:
        lineid, eqpid, eqp_name, tool_group,
        status, pre_status, status_date,
        normalized_status, production_available,
        platform_collected_time
    """
    raw_df = _fetch_latest_rows_per_equipment()
    eqp_map = get_managed_equipment_map()
    collected_at = datetime.utcnow()

    # Start from the managed equipment list so missing equipment still appear (as UNKNOWN).
    rows: list[dict[str, Any]] = []
    raw_indexed: dict[tuple[str, str], dict[str, Any]] = {}
    if not raw_df.empty:
        for _, r in raw_df.iterrows():
            raw_indexed[(str(r["lineid"]), str(r["eqpid"]))] = r.to_dict()

    for eqp in MANAGED_EQUIPMENTS:
        key = (eqp["lineid"], eqp["eqpid"])
        meta = eqp_map[key]
        raw = raw_indexed.get(key)

        status = raw["status"] if raw is not None else None
        pre_status = raw["pre_status"] if raw is not None else None
        status_date = raw["status_date"] if raw is not None else None
        normalized = normalize_status(status)
        available = is_production_available(normalized)

        rows.append(
            {
                "lineid": eqp["lineid"],
                "eqpid": eqp["eqpid"],
                "eqp_name": meta["eqp_name"],
                "tool_group": meta["tool_group"],
                "status": status,
                "pre_status": pre_status,
                "status_date": status_date,
                "normalized_status": normalized,
                "production_available": available,
                "platform_collected_time": collected_at,
            }
        )

    df = pd.DataFrame(rows)
    if "status_date" in df.columns:
        df["status_date"] = pd.to_datetime(df["status_date"], errors="coerce")
    df["platform_collected_time"] = pd.to_datetime(df["platform_collected_time"])
    return df
