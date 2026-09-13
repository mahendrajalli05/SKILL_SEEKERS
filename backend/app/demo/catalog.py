"""Static catalog for the four controlled prototype demonstration cases.

Uses existing DEMO_INTERNAL_IDS. Does not create a new dataset.
Suggested Copilot questions are prompts only — answers come from grounded retrieval.
"""

from __future__ import annotations

from typing import Any

from app.demo.constants import DEMO_NOTICE, HYBRID_NOTICE, CASE_IDS, internal_project_id_for

_CASES: dict[str, dict[str, Any]] = {
    "GHOST": {
        "case_id": "GHOST",
        "display_name": "GHOST",
        "purpose": "Demonstrate a location and evidence-integrity concern.",
        "scenario_type": "DEMO_GHOST",
        "short_description": (
            "Completed work with a claimed finish and labelled SYNTHETIC location "
            "signals that do not match the constituency context."
        ),
        "initial_claim": "Work is reported completed in the observed STATUS field.",
        "expected_lifecycle": "COMPLETED",
        "data_mode": "HYBRID",
        "expected_direction": "REVIEW / INSPECT",
        "expected_direction_note": (
            "Expected demonstration direction only. The live recommendation is "
            "whatever Risk Fusion V2 and lifecycle actually return. Not a legal finding."
        ),
        "officer_actions": ["confirm_concern", "dismiss", "need_more_info"],
        "officer_action_labels": [
            "CONFIRM CONCERN",
            "DISMISS",
            "NEED MORE INFORMATION",
        ],
        "suggested_questions": [
            "Why is this project being recommended for inspection?",
            "What location evidence supports the concern?",
            "What evidence is missing?",
            "What should I inspect next?",
        ],
        "modules": [
            "identity",
            "claim",
            "image",
            "forensics",
            "gps",
            "geospatial",
            "satellite",
            "evidence_confidence",
            "risk_fusion_v2",
            "copilot",
        ],
    },
    "OVERBILL": {
        "case_id": "OVERBILL",
        "display_name": "OVER-BILL",
        "purpose": "Demonstrate a financial and expenditure inconsistency.",
        "scenario_type": "DEMO_OVERBILL",
        "short_description": (
            "Completed work whose labelled HYBRID enrichment includes expenditure "
            "and milestone totals that exceed the sanctioned amount."
        ),
        "initial_claim": "Work is reported completed; HYBRID enrichment supplies expenditure for prototype testing.",
        "expected_lifecycle": "COMPLETED",
        "data_mode": "HYBRID",
        "expected_direction": "REVIEW / HOLD / INSPECT",
        "expected_direction_note": (
            "Expected demonstration direction only. Do not force Cost, Compliance, "
            "PCE, or Risk Fusion V2 results. Not a legal finding."
        ),
        "officer_actions": ["confirm_concern", "dismiss", "need_more_info"],
        "officer_action_labels": [
            "CONFIRM CONCERN",
            "DISMISS",
            "NEED MORE INFORMATION",
        ],
        "suggested_questions": [
            "What financial evidence supports the concern?",
            "What did Compliance report?",
            "Summarize Plan → Claim → Evidence.",
            "Why is this project flagged?",
        ],
        "modules": [
            "plan",
            "expenditure",
            "compliance",
            "cost",
            "pce",
            "milestone",
            "risk_fusion_v2",
            "copilot",
        ],
    },
    "STUCK": {
        "case_id": "STUCK",
        "display_name": "STUCK",
        "purpose": "Demonstrate schedule, progress, and milestone risk.",
        "scenario_type": "DEMO_STUCK",
        "short_description": (
            "Ongoing work with labelled SYNTHETIC overdue schedule signals and "
            "low reported physical progress. Dates are not invented as official records."
        ),
        "initial_claim": "Work is ongoing with low claimed progress in labelled HYBRID enrichment.",
        "expected_lifecycle": "ONGOING",
        "data_mode": "HYBRID",
        "expected_direction": "INSPECT / HOLD",
        "expected_direction_note": (
            "Expected demonstration direction only where Time Intelligence, PCE, "
            "and Milestone Advisor actually support it. Dates are not fabricated."
        ),
        "officer_actions": ["PROCEED", "HOLD", "INSPECT", "NEED_MORE_INFORMATION"],
        "officer_action_labels": [
            "PROCEED",
            "HOLD",
            "INSPECT",
            "NEED MORE INFORMATION",
        ],
        "investigation_actions": ["confirm_concern", "dismiss", "need_more_info"],
        "suggested_questions": [
            "Why is this milestone being held?",
            "Why is Time Intelligence concerned?",
            "What remains to be verified?",
            "What was the last milestone decision?",
        ],
        "modules": [
            "plan_dates",
            "progress",
            "milestone",
            "time",
            "pce",
            "risk_fusion_v2",
            "copilot",
        ],
    },
    "CLEAN": {
        "case_id": "CLEAN",
        "display_name": "CLEAN",
        "purpose": "Demonstrate that SARVSAKSHI does not flag every project.",
        "scenario_type": "DEMO_CLEAN",
        "short_description": (
            "Proposed/sanctioned work with internally consistent labelled SYNTHETIC "
            "enrichment. Investigation Priority is not forced to zero."
        ),
        "initial_claim": "Ordinary sanctioned work with supporting plan, claim, and evidence when recorded.",
        "expected_lifecycle": "FUTURE",
        "data_mode": "HYBRID",
        "expected_direction": "MONITOR / PROCEED",
        "expected_direction_note": (
            "Expected demonstration direction only where Need & Impact, Risk Fusion V2, "
            "and PCE actually support it. Score is not forced to zero."
        ),
        "officer_actions": ["PRIORITIZE", "DEFER", "NEED_MORE_INFORMATION"],
        "officer_action_labels": [
            "PRIORITIZE",
            "DEFER",
            "NEED MORE INFORMATION",
        ],
        "investigation_actions": ["confirm_concern", "dismiss", "need_more_info"],
        "suggested_questions": [
            "Why was this project not escalated?",
            "What evidence supports this?",
            "What information is missing?",
            "Why is this project not flagged?",
        ],
        "modules": [
            "plan",
            "claim",
            "evidence",
            "image",
            "geospatial",
            "citizen",
            "milestone",
            "risk_fusion_v2",
            "copilot",
        ],
    },
}


def normalize_case_id(value: str | None) -> str:
    text = str(value or "").strip().upper().replace("-", "").replace("_", "")
    if text == "OVERBILL":
        return "OVERBILL"
    if text in _CASES:
        return text
    raise KeyError(value)


def catalog_entry(case_id: str) -> dict[str, Any]:
    key = normalize_case_id(case_id)
    entry = dict(_CASES[key])
    entry["internal_project_id"] = internal_project_id_for(key)
    entry["demo_notice"] = DEMO_NOTICE
    entry["hybrid_notice"] = HYBRID_NOTICE
    entry["synthetic_label"] = "HYBRID / SYNTHETIC"
    return entry


def list_catalog() -> list[dict[str, Any]]:
    return [catalog_entry(case_id) for case_id in CASE_IDS]
