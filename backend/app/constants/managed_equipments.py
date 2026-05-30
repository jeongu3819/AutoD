"""
Hard-coded managed equipment list for Phase 1.

Field notes:
- eqp_name / tool_group 제거 (실제 Datalake 컬럼 없음)
- PRC_GROUP: 공정/설비 그룹 기준 (기존 tool_group 대체)
- chamber_step, param_name, grade, recipe_id, unit_name:
  설비 1대당 여러 값이 매핑될 수 있어 str 또는 list[str] 모두 허용

향후 확장 후보:
  - DB 테이블 managed_equipments으로 이전
  - 관리자 화면 / CSV 업로드 기반 관리
  - PRC_GROUP / area / eqp_model 기준 자동 그룹핑
"""
from __future__ import annotations

StrOrList = str | list[str]


class ManagedEquipment(dict):
    """
    Typed alias only for documentation. Actual values are plain dicts so that
    MANAGED_EQUIPMENTS can be edited without any class ceremony.

    Required keys : lineid, eqpid
    Optional keys : PRC_GROUP, FDC_MODEL, eqp_model, area, sdwt,
                    chamber_step, param_name, grade, recipe_id, unit_name
    Multi-value   : chamber_step, param_name, grade, recipe_id, unit_name
                    accept either a single str or a list[str].
    """


MANAGED_EQUIPMENTS: list[dict] = [
    {
        "lineid": "라인값",
        "eqpid": "설비ID_01",
        "PRC_GROUP": "공정그룹값",
        "FDC_MODEL": "FDC모델값",
        "eqp_model": "설비모델값",
        "area": "CMP",
        "sdwt": "SDWT값",
        "chamber_step": ["STEP1", "STEP2"],
        "param_name": ["PARAM_A", "PARAM_B"],
        "grade": ["A", "B"],
        "recipe_id": ["REC001", "REC002"],
        "unit_name": ["UNIT1", "UNIT2"],
    },
    {
        "lineid": "라인값",
        "eqpid": "설비ID_02",
        "PRC_GROUP": "공정그룹값",
        "FDC_MODEL": "FDC모델값",
        "eqp_model": "설비모델값",
        "area": "CMP",
        "sdwt": "SDWT값",
        "chamber_step": "STEP1",
        "param_name": "PARAM_A",
        "grade": "A",
        "recipe_id": "REC001",
        "unit_name": "UNIT1",
    },
]


def get_managed_line_ids() -> list[str]:
    return sorted({e["lineid"] for e in MANAGED_EQUIPMENTS})


def get_managed_eqp_ids() -> list[str]:
    return sorted({e["eqpid"] for e in MANAGED_EQUIPMENTS})


def get_managed_equipment_map() -> dict[tuple[str, str], dict]:
    """Lookup: (lineid, eqpid) -> full equipment dict (including PRC_GROUP, area, …)"""
    return {(e["lineid"], e["eqpid"]): e for e in MANAGED_EQUIPMENTS}


def normalize_multi(value: StrOrList | None) -> list[str]:
    """Normalise str | list[str] | None -> list[str] for consistent storage."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]
