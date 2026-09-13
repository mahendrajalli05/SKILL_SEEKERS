"""Geographic matching for external contextual data.

Does not fabricate district from IDA or constituency. Does not treat one
geographic level as equal to another.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.engines.context.constants import (
    FAILURE_MISSING_GEOGRAPHY,
    FAILURE_UNSUPPORTED_GEOGRAPHY,
    GEO_BLOCK,
    GEO_CONSTITUENCY,
    GEO_DISTRICT,
    GEO_LOCALITY,
    GEO_STATE,
    NON_GEOGRAPHIC_CONSTITUENCY_TOKENS,
    STATUS_INCONCLUSIVE,
    STATUS_UNAVAILABLE,
)

_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[^a-z0-9&]+")

STATE_ALIASES = {
    "andhra pradesh": "Andhra Pradesh",
    "ap": "Andhra Pradesh",
    "telangana": "Telangana",
    "ts": "Telangana",
    "uttaranchal": "Uttarakhand",
    "uttarakhand": "Uttarakhand",
    "orissa": "Odisha",
    "odisha": "Odisha",
    "pondicherry": "Puducherry",
    "puducherry": "Puducherry",
    "delhi": "NCT of Delhi",
    "nct of delhi": "NCT of Delhi",
    "nct delhi": "NCT of Delhi",
    "new delhi": "NCT of Delhi",
    "jammu and kashmir": "Jammu & Kashmir (UT)",
    "jammu & kashmir": "Jammu & Kashmir (UT)",
    "jammu & kashmir (ut)": "Jammu & Kashmir (UT)",
    "dadra and nagar haveli": "Dadra & Nagar Haveli",
    "dadra & nagar haveli": "Dadra & Nagar Haveli",
    "daman and diu": "Daman Diu",
    "daman diu": "Daman Diu",
    "andaman and nicobar islands": "Andaman & Nicobar Islands",
    "andaman & nicobar islands": "Andaman & Nicobar Islands",
    "a and n islands": "Andaman & Nicobar Islands",
}


@dataclass
class GeoMatch:
    level: str | None
    key: str | None
    status: str
    failure_code: str | None
    reason: str
    project_state: str | None = None
    project_constituency: str | None = None
    project_block: str | None = None
    project_locality: str | None = None


def normalize_geo_key(value: str | None) -> str:
    text = _SPACE.sub(" ", (value or "").strip().lower())
    text = text.replace(" and ", " & ")
    return _PUNCT.sub(" ", text).strip()


def canonical_state(value: str | None) -> str | None:
    key = normalize_geo_key(value)
    if not key:
        return None
    if key in STATE_ALIASES:
        return STATE_ALIASES[key]
    for alias, canonical in STATE_ALIASES.items():
        if key == normalize_geo_key(canonical) or key == alias:
            return canonical
    # Title-case unknown but non-empty state text; matcher may still miss.
    cleaned = (value or "").strip()
    return cleaned or None


def is_geographic_constituency(value: str | None) -> bool:
    text = normalize_geo_key(value)
    if not text:
        return False
    return text not in NON_GEOGRAPHIC_CONSTITUENCY_TOKENS and "rajya sabha" not in text


def match_project_geography(
    *,
    state: str | None,
    constituency: str | None = None,
    block: str | None = None,
    city: str | None = None,
    village: str | None = None,
    ward: str | None = None,
    ida: str | None = None,
    requested_level: str | None = None,
) -> GeoMatch:
    """Return the highest reliable level actually present on the record."""
    del ida  # IDA is not a verified district identifier.
    requested = (requested_level or GEO_STATE).upper()
    state_key = canonical_state(state)
    constituency_ok = is_geographic_constituency(constituency)
    locality = next((item for item in (village, city, ward) if (item or "").strip()), None)

    if requested == GEO_DISTRICT:
        return GeoMatch(
            level=GEO_DISTRICT,
            key=None,
            status=STATUS_INCONCLUSIVE,
            failure_code=FAILURE_UNSUPPORTED_GEOGRAPHY,
            reason=(
                "District-level matching is unsupported. The current MPLADS extract "
                "has no verified district field, and district is not fabricated from "
                "IDA or constituency text."
            ),
            project_state=state_key,
            project_constituency=(constituency or "").strip() or None,
            project_block=(block or "").strip() or None,
            project_locality=(locality or "").strip() or None,
        )
    if requested == GEO_CONSTITUENCY:
        if not constituency_ok:
            return GeoMatch(
                level=GEO_CONSTITUENCY,
                key=None,
                status=STATUS_INCONCLUSIVE,
                failure_code=FAILURE_MISSING_GEOGRAPHY,
                reason=(
                    "No reliable geographic constituency identifier is available on this record."
                ),
                project_state=state_key,
                project_constituency=(constituency or "").strip() or None,
            )
        return GeoMatch(
            level=GEO_CONSTITUENCY,
            key=(constituency or "").strip(),
            status=STATUS_INCONCLUSIVE,
            failure_code=FAILURE_UNSUPPORTED_GEOGRAPHY,
            reason=(
                "Constituency is recorded on the project, but no verified constituency-level "
                "external dataset is integrated. Constituency is not treated as equal to district or state."
            ),
            project_state=state_key,
            project_constituency=(constituency or "").strip(),
        )
    if requested == GEO_BLOCK:
        if not (block or "").strip():
            return GeoMatch(
                level=GEO_BLOCK,
                key=None,
                status=STATUS_UNAVAILABLE,
                failure_code=FAILURE_MISSING_GEOGRAPHY,
                reason="Block is blank on the project record. Block is not inferred.",
                project_state=state_key,
            )
        return GeoMatch(
            level=GEO_BLOCK,
            key=block.strip() if block else None,
            status=STATUS_INCONCLUSIVE,
            failure_code=FAILURE_UNSUPPORTED_GEOGRAPHY,
            reason="No verified block-level external dataset is integrated.",
            project_state=state_key,
            project_block=(block or "").strip() or None,
        )
    if requested == GEO_LOCALITY:
        if not (locality or "").strip():
            return GeoMatch(
                level=GEO_LOCALITY,
                key=None,
                status=STATUS_UNAVAILABLE,
                failure_code=FAILURE_MISSING_GEOGRAPHY,
                reason="Locality/village/city is blank on the project record. Locality is not inferred.",
                project_state=state_key,
            )
        return GeoMatch(
            level=GEO_LOCALITY,
            key=(locality or "").strip(),
            status=STATUS_INCONCLUSIVE,
            failure_code=FAILURE_UNSUPPORTED_GEOGRAPHY,
            reason="No verified locality-level external dataset is integrated.",
            project_state=state_key,
            project_locality=(locality or "").strip() or None,
        )

    if not state_key:
        return GeoMatch(
            level=GEO_STATE,
            key=None,
            status=STATUS_UNAVAILABLE,
            failure_code=FAILURE_MISSING_GEOGRAPHY,
            reason="State is blank on the project record. State is not inferred from MP name or constituency.",
        )
    return GeoMatch(
        level=GEO_STATE,
        key=state_key,
        status="AVAILABLE",
        failure_code=None,
        reason="Matched on observed project.state. This is a STATE-level key, not a project site.",
        project_state=state_key,
        project_constituency=(constituency or "").strip() or None,
        project_block=(block or "").strip() or None,
        project_locality=(locality or "").strip() or None,
    )
