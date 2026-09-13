"""Internal state/UT abbreviations for SARVSAKSHI Scheme IDs.

These codes are application abbreviations, not official MPLADS identifiers
and not a claim of ISO certification of the source extract. Observed extract
names are matched case-insensitively. Unmapped names get a deterministic
fallback code so Scheme IDs remain unique without fabricating an official list.
"""

from __future__ import annotations

import re

from app.engines.cost.work_type import normalize_observed_text

# Common India state/UT abbreviations keyed by casefolded observed names.
# Not an official MPLADS code list.
_STATE_CODES: dict[str, str] = {
    "andaman and nicobar islands": "AN",
    "andhra pradesh": "AP",
    "arunachal pradesh": "AR",
    "assam": "AS",
    "bihar": "BR",
    "chandigarh": "CH",
    "chhattisgarh": "CG",
    "dadra and nagar haveli": "DN",
    "dadra and nagar haveli and daman and diu": "DH",
    "daman and diu": "DD",
    "delhi": "DL",
    "nct of delhi": "DL",
    "goa": "GA",
    "gujarat": "GJ",
    "haryana": "HR",
    "himachal pradesh": "HP",
    "jammu and kashmir": "JK",
    "jharkhand": "JH",
    "karnataka": "KA",
    "kerala": "KL",
    "ladakh": "LA",
    "lakshadweep": "LD",
    "madhya pradesh": "MP",
    "maharashtra": "MH",
    "manipur": "MN",
    "meghalaya": "ML",
    "mizoram": "MZ",
    "nagaland": "NL",
    "odisha": "OD",
    "orissa": "OD",
    "puducherry": "PY",
    "pondicherry": "PY",
    "punjab": "PB",
    "rajasthan": "RJ",
    "sikkim": "SK",
    "tamil nadu": "TN",
    "telangana": "TS",
    "tripura": "TR",
    "uttar pradesh": "UP",
    "uttarakhand": "UK",
    "uttaranchal": "UK",
    "west bengal": "WB",
}

BLANK_STATE_CODE = "XX"


def internal_state_code(state: str | None) -> str:
    """Return a 2–3 letter internal abbreviation for an observed state name."""
    text = normalize_observed_text(state)
    if not text:
        return BLANK_STATE_CODE
    mapped = _STATE_CODES.get(text.casefold())
    if mapped:
        return mapped
    return _fallback_code(text)


def _fallback_code(text: str) -> str:
    words = [re.sub(r"[^A-Za-z]", "", part) for part in text.split()]
    words = [part for part in words if part]
    if len(words) >= 2:
        code = (words[0][0] + words[1][0]).upper()
        return code or BLANK_STATE_CODE
    letters = "".join(char for char in text if char.isalpha())
    if len(letters) >= 2:
        return letters[:2].upper()
    if letters:
        return (letters + "X")[:2].upper()
    return BLANK_STATE_CODE


def states_matching_code(observed_states: list[str], code: str) -> list[str]:
    """Return observed state strings that map to the given internal code."""
    wanted = (code or "").strip().upper()
    if not wanted:
        return []
    matched: list[str] = []
    for value in observed_states:
        if internal_state_code(value) == wanted:
            matched.append(value)
    return matched


def is_blank_state(state: str | None) -> bool:
    return not normalize_observed_text(state)
