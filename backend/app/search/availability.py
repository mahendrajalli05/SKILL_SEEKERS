"""Honest availability catalog for fields absent from the real extract."""

from __future__ import annotations

from app.engines.cost.constants import AMOUNT_UNIT_NOTE
from app.scope import (
    HYBRID_DEMO_NOTICE,
    NOT_ASSESSABLE_LABEL,
    REAL_DATA_NOTICE,
    SCHEME_ID_NOTE,
    UNAVAILABLE_REAL_LABEL,
)

UNAVAILABLE_REAL_FIELDS: tuple[dict[str, str], ...] = (
    {
        "field": "district",
        "status": "UNAVAILABLE",
        "reason": (
            "Verified district is not present in the current real work-level extract "
            "and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "vendor",
        "status": "UNAVAILABLE",
        "reason": (
            "Vendor or contractor is not present in the current real work-level extract "
            "and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "expenditure",
        "status": "UNAVAILABLE",
        "reason": (
            "Verified expenditure or utilised amount is not present in the current "
            "real work-level extract and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "gps",
        "status": "UNAVAILABLE",
        "reason": (
            "GPS coordinates are not present in the current real work-level extract "
            "and are not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "sanction_date",
        "status": "UNAVAILABLE",
        "reason": (
            "Verified sanction date is not present in the current real work-level extract "
            "and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "start_date",
        "status": "UNAVAILABLE",
        "reason": (
            "Verified start date is not present in the current real work-level extract "
            "and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "completion_date",
        "status": "UNAVAILABLE",
        "reason": (
            "Verified completion date is not present in the current real work-level extract "
            "and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "physical_progress",
        "status": "UNAVAILABLE",
        "reason": (
            "Physical progress is not present in the current real work-level extract "
            "and is not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
    {
        "field": "milestones",
        "status": "UNAVAILABLE",
        "reason": (
            "Milestone records are not present in the current real work-level extract "
            "and are not stored on the project record."
        ),
        "display": UNAVAILABLE_REAL_LABEL,
    },
)

TIME_UNAVAILABLE_MESSAGE = (
    "Time Intelligence unavailable because verified execution dates are not "
    "present in the current real dataset."
)

HYBRID_ENRICHMENT_NOTICE = HYBRID_DEMO_NOTICE

SEARCH_NOTE = (
    "Search uses observed real fields plus the internal SARVSAKSHI Scheme ID. "
    "Text search covers Scheme ID, internal project ID, work description, and "
    "MP name. Filters are State → Constituency → Category → Status. "
    "District, vendor, expenditure, GPS, sanction date, and completion date "
    "are not available to filter. "
    f"{SCHEME_ID_NOTE} {AMOUNT_UNIT_NOTE}"
)

PROVENANCE_AMOUNT_NOTE = AMOUNT_UNIT_NOTE

__all__ = [
    "UNAVAILABLE_REAL_FIELDS",
    "TIME_UNAVAILABLE_MESSAGE",
    "HYBRID_ENRICHMENT_NOTICE",
    "HYBRID_DEMO_NOTICE",
    "REAL_DATA_NOTICE",
    "SEARCH_NOTE",
    "PROVENANCE_AMOUNT_NOTE",
    "UNAVAILABLE_REAL_LABEL",
    "NOT_ASSESSABLE_LABEL",
    "SCHEME_ID_NOTE",
]
