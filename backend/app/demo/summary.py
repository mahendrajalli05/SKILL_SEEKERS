"""Final case summary for Demo Cases V1. Reads existing outputs only."""

from __future__ import annotations

from typing import Any

from app.demo.constants import DEMO_NOTICE, GOVERNANCE_NOTE, NO_FRAUD_NOTE, NO_SANCTION_NOTE
from app.domain.enums import DataMode


def _ids(payload: dict[str, Any] | None, *keys: str) -> list[str]:
    if not payload:
        return []
    found: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            found.extend(str(item) for item in value if item)
        elif isinstance(value, str) and value:
            found.append(value)
    return found


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _officer_label(decisions: list[dict[str, Any]]) -> str | None:
    if not decisions:
        return None
    last = decisions[0]
    action = last.get("decision_type") or last.get("action") or last.get("officer_action")
    return None if action is None else str(action)


def build_case_summary(
    *,
    case_id: str,
    display_name: str,
    project_id: int,
    scheme_id: str | None,
    internal_project_id: str,
    data_mode: DataMode | str,
    lifecycle: dict[str, Any],
    risk: dict[str, Any] | None,
    evidence_items: list[dict[str, Any]],
    main_signals: list[dict[str, Any]],
    missing: list[str],
    recommendation: str | None,
    officer_decisions: list[dict[str, Any]],
    is_synthetic: bool,
) -> dict[str, Any]:
    mode = data_mode.value if isinstance(data_mode, DataMode) else str(data_mode)
    evidence_ids = _unique(
        [str(item.get("evidence_id")) for item in evidence_items if item.get("evidence_id")]
        + _ids(risk, "evidence_ids")
        + _ids(lifecycle.get("evidence_summary") if isinstance(lifecycle.get("evidence_summary"), dict) else None, "evidence_ids")
    )
    last_decision = _officer_label(officer_decisions)
    reliability = "SYNTHETIC" if is_synthetic else ("HYBRID" if mode == "HYBRID" else "REAL")
    return {
        "case_id": case_id,
        "display_name": display_name,
        "project": {
            "project_id": project_id,
            "scheme_id": scheme_id,
            "internal_project_id": internal_project_id,
            "work_description": lifecycle.get("work_description"),
            "constituency": lifecycle.get("constituency"),
            "category": lifecycle.get("category"),
            "source_status": lifecycle.get("source_status"),
        },
        "lifecycle": lifecycle.get("lifecycle_state"),
        "current_stage": lifecycle.get("current_stage"),
        "investigation_priority": None if not risk else risk.get("investigation_priority"),
        "evidence_confidence": None if not risk else risk.get("evidence_confidence"),
        "main_signals": main_signals,
        "evidence": evidence_ids,
        "missing_information": list(missing),
        "recommended_action": recommendation,
        "officer_decision": last_decision,
        "officer_decisions": list(officer_decisions),
        "data_reliability": reliability,
        "data_mode": mode,
        "demo_notice": DEMO_NOTICE,
        "governance_note": GOVERNANCE_NOTE,
        "no_fraud_note": NO_FRAUD_NOTE,
        "no_sanction_note": NO_SANCTION_NOTE,
        "automatic_sanction": False,
        "automatic_payment": False,
        "pfms_integrated": False,
        "fraud_conclusion": False,
        "scores_mutated": False,
    }
