"""Configurable application scope for the current SARVSAKSHI pilot.

The master SQLite database keeps every loaded state. This module only
controls the default user-facing search universe. Changing the pilot state
does not require a second database or deletion of non-pilot rows.
"""

from __future__ import annotations

from app.config import get_settings

DEFAULT_PILOT_STATE = "Andhra Pradesh"
DEFAULT_DATA_MODE = "HYBRID"
PILOT_LABEL_PREFIX = "Current Pilot:"
SCHEME_ID_NOTE = (
    "Internal SARVSAKSHI application identifier — not an official MPLADS Work ID."
)
HYBRID_DEMO_NOTICE = (
    "HYBRID DEMO — Base project data comes from a real MPLADS extract. "
    "Fields marked SYNTHETIC are simulated prototype enrichment and are not "
    "official MPLADS records."
)
REAL_DATA_NOTICE = (
    "REAL DATA — Showing observed MPLADS extract fields only. Missing "
    "government fields are listed as unavailable in the current public extract. "
    "Synthetic enrichment is not used."
)
UNAVAILABLE_REAL_LABEL = "Unavailable in current public extract"
NOT_ASSESSABLE_LABEL = "Not assessable"
SELECT_STATE_FIRST = "Select state first"


def current_pilot_state() -> str:
    value = (get_settings().pilot_state or DEFAULT_PILOT_STATE).strip()
    return value or DEFAULT_PILOT_STATE


def current_pilot_label() -> str:
    return f"{PILOT_LABEL_PREFIX} {current_pilot_state()}"


def default_data_mode() -> str:
    value = (get_settings().default_data_mode or DEFAULT_DATA_MODE).strip().upper()
    if value == "REAL":
        return "REAL"
    return "HYBRID"


def resolve_data_mode(value: str | None) -> str:
    text = (value or "").strip().upper().replace("-", "_")
    if text in {"REAL", "REAL_DATA"}:
        return "REAL"
    if text in {"HYBRID", "HYBRID_DEMO", "HYBRID_TEST", "HYBRIDTEST"}:
        return "HYBRID"
    return default_data_mode()


def application_scope_payload() -> dict[str, object]:
    return {
        "current_pilot": current_pilot_state(),
        "pilot_label": current_pilot_label(),
        "default_state": current_pilot_state(),
        "default_data_mode": default_data_mode(),
        "scope_configurable": True,
        "database_retains_all_states": True,
        "note": (
            "The master database retains every loaded state. Normal officer "
            f"search defaults to {current_pilot_state()}. Other states can be "
            "enabled later by changing SARVSAKSHI_PILOT_STATE without redesigning "
            "the database."
        ),
    }
