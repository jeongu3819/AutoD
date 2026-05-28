"""
Equipment status normalization rules for Phase 1.

Normalization rules:
1. raw status is trimmed and upper-cased.
2. If present in STATUS_MAPPING, mapped to normalized_status.
3. Otherwise -> "UNKNOWN".

Production-available rule:
- Only RUN / IDLE / BU_DONE are production-available.
- LOCAL, DOWN, PM_PROGRESS, PM_DONE, BU_WAIT, BU_PROGRESS, BU_FAIL, HOLD, UNKNOWN -> not available.
"""

STATUS_MAPPING = {
    "RUN": "RUN",
    "IDLE": "IDLE",
    "DOWN": "DOWN",
    "LOCAL": "LOCAL",
    "PM": "PM_PROGRESS",
    "PM_PROGRESS": "PM_PROGRESS",
    "PM_DONE": "PM_DONE",
    "BU_WAIT": "BU_WAIT",
    "BU_PROGRESS": "BU_PROGRESS",
    "BU_DONE": "BU_DONE",
    "BU_FAIL": "BU_FAIL",
    "HOLD": "HOLD",
}

AVAILABLE_STATUSES = {"RUN", "IDLE", "BU_DONE"}

PM_BU_STATUSES = {
    "PM_PROGRESS",
    "PM_DONE",
    "BU_WAIT",
    "BU_PROGRESS",
    "BU_DONE",
    "BU_FAIL",
}


def normalize_status(raw: str | None) -> str:
    if raw is None:
        return "UNKNOWN"
    key = str(raw).strip().upper()
    if not key:
        return "UNKNOWN"
    return STATUS_MAPPING.get(key, "UNKNOWN")


def is_production_available(normalized_status: str) -> bool:
    return normalized_status in AVAILABLE_STATUSES
