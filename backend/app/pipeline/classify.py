"""Column-role heuristics from *observed* names and values. Not an official schema."""

from __future__ import annotations

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_name(name: str) -> str:
    return _NON_ALNUM.sub(" ", str(name).strip().lower()).strip()


def likely_role(column_name: str) -> str:
    n = normalize_name(column_name)
    if not n:
        return "other"
    if n in {"unnamed 0", "unnamed"} or n.startswith("unnamed"):
        return "other"
    tokens = set(n.split())

    if tokens & {"latitude", "lat"} or n in {"lat", "y"} or "latitude" in n:
        return "latitude"
    if tokens & {"longitude", "lon", "lng", "long"} or n in {"lon", "lng", "x"} or "longitude" in n:
        return "longitude"
    if "gps" in tokens or n in {"coordinates", "coord", "geolocation"}:
        return "location"

    if "district" in tokens or n.endswith(" dist") or n == "dist":
        return "district"
    if "state" in tokens or n in {"stateut", "state ut"}:
        return "state"

    if tokens & {"status", "stage"} or "work status" in n or n.endswith(" status"):
        return "status"

    if "vendor" in tokens or "contractor" in tokens:
        return "vendor"
    if "agency" in tokens or "executing" in n or "implementing agency" in n:
        return "agency"
    if n in {"ida", "implementing district authority"}:
        return "agency"

    if any(k in n for k in ("sanctioned amount", "recommended amount", "utilised amount", "utilized amount")):
        return "amount"
    if any(k in n for k in ("amount", "cost", "expenditure", "estimate", "outlay")):
        if "date" not in tokens:
            return "amount"

    if "date" in tokens or n.endswith(" dt") or n in {"dt"}:
        return "date"
    if tokens & {"year"} and "amount" not in tokens:
        return "date"

    if any(k in n for k in ("unique id", "work id", "work number", "work no", "unique work")):
        return "work_id"
    if n in {"id", "s no", "sl no", "serial no", "sno"}:
        return "work_id"

    if n in {"work"} or any(
        k in n for k in ("work name", "work description", "project name", "particulars", "nature of work")
    ):
        return "description"
    if "description" in tokens or (tokens & {"work", "project"} and tokens & {"name", "title", "details"}):
        return "description"

    if (
        "village" in tokens
        or "place" in tokens
        or "block" in tokens
        or "mandal" in tokens
        or "location" in n
        or n in {"city", "ward", "town"}
    ):
        return "location"
    if "constituency" in n:
        return "constituency"
    if (
        tokens & {"mp"}
        or "member of parliament" in n
        or n.endswith(" mp name")
        or n.replace(" ", "") in {"mpname", "mpnames"}
    ):
        return "mp"
    if "lok sabha" in n or "rajya sabha" in n or n in {"house", "house name"}:
        return "house"
    if "image" in tokens or "photo" in tokens:
        return "image"
    if "category" in tokens or "sector" in tokens or "type of work" in n or n == "work type":
        return "work_type"
    return "other"


def likely_meaning(column_name: str, role: str) -> str:
    meanings = {
        "state": "State / UT name as recorded in the extract",
        "district": "District name as recorded in the extract",
        "amount": "Monetary value (role/unit inferred from the column name only)",
        "date": "Date-like field as recorded in the extract",
        "agency": "Implementing or executing agency name",
        "vendor": "Vendor or contractor name as recorded",
        "status": "Reported work/project status",
        "description": "Work or project title/description",
        "work_id": "Work identifier or serial present in the extract",
        "latitude": "Latitude if the extract actually stores coordinates",
        "longitude": "Longitude if the extract actually stores coordinates",
        "location": "Place/location text (not necessarily GPS)",
        "constituency": "Parliamentary constituency as recorded",
        "mp": "MP name as recorded",
        "house": "Lok Sabha / Rajya Sabha (or equivalent) as recorded",
        "image": "Image/photo upload flag or status as recorded",
        "work_type": "Work type/category/sector as recorded",
        "other": "Observed column; role not inferred from the name",
    }
    return meanings.get(role, meanings["other"])


def suspected_amount_unit(column_name: str) -> str | None:
    n = normalize_name(column_name)
    if "lakh" in n:
        return "lakh"
    if "crore" in n:
        return "crore"
    if "rs" in n.split() or "rupee" in n or "inr" in n or n.endswith(" rs") or "(rs)" in column_name.lower():
        return "inr"
    if "amount" in n or "cost" in n or "expenditure" in n:
        return "unspecified"
    return None
