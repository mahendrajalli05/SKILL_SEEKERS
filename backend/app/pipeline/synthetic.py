"""Synthetic HYBRID enrichment for SARVSAKSHI prototype testing.

Reads the cleaned real MPLADS extract and writes a separate SYNTHETIC layer
under ``data/synthetic/`` only. Does not modify ``data/raw/``,
``data/processed/``, or the SQLite ``project`` table.

Every output row is labelled ``record_mode=HYBRID`` and
``enrichment_source=SYNTHETIC``. District, vendor, GPS, expenditure, sanction
and completion dates are generated for the prototype. They are not official
MPLADS values. The link to a real work is ``internal_project_id`` only.
"""

from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import REPO_ROOT
from app.pipeline.discover import sha256_file

DEFAULT_SEED = 26102
TARGET_RECORD_COUNT = 10000
SYNTHETIC_AS_OF_DATE = date(2024, 6, 30)
SYNTHETIC_ID_PREFIX = "synthetic:"
RECORD_MODE = "HYBRID"
ENRICHMENT_SOURCE = "SYNTHETIC"

DEFAULT_CLEANED_CSV = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "synthetic"
DEFAULT_OUTPUT_CSV = DEFAULT_OUTPUT_DIR / "sarvsakshi_synthetic_enrichment.csv"
DEFAULT_PROVENANCE_PATH = (
    DEFAULT_OUTPUT_DIR / "sarvsakshi_synthetic_enrichment.provenance.json"
)

SYNTHETIC_DISCLAIMER = (
    "SYNTHETIC prototype enrichment. Not an official MPLADS field or dataset. "
    "Linked to a real work only via internal_project_id. Do not treat district, "
    "agency, vendor, coordinates, dates, or expenditure as government values."
)

SCENARIO_PERCENTS: list[tuple[str, float]] = [
    ("NORMAL", 0.70),
    ("COST_ANOMALY", 0.10),
    ("TIME_ANOMALY", 0.08),
    ("OVERLAP", 0.05),
    ("EVIDENCE_GHOST", 0.04),
    ("MIXED", 0.03),
]

DEMO_FROM_SCENARIO = (
    ("NORMAL", "DEMO_CLEAN", "CLEAN"),
    ("COST_ANOMALY", "DEMO_OVERBILL", "OVERBILL"),
    ("TIME_ANOMALY", "DEMO_STUCK", "STUCK"),
    ("EVIDENCE_GHOST", "DEMO_GHOST", "GHOST"),
)

MIXED_SIGNAL_CYCLE = (
    "COST_ANOMALY,TIME_ANOMALY",
    "EVIDENCE_GHOST,COST_ANOMALY",
    "OVERLAP,COST_ANOMALY",
)

IDA_ROLE_RE = re.compile(
    r"^(?:"
    r"DISTRICT\s+PLANNING\s+OFFICER|"
    r"DISTRICT\s+MAGISTRATE|"
    r"DISTRICT\s+MAGISTRAE|"
    r"DISTRICT\s+COLLECTOR|"
    r"DEPUTY\s+COMMISSIONER|"
    r"CHIEF\s+EXECUTIVE\s+OFFICER|"
    r"COMMISSIONER|"
    r"COLLECTOR"
    r")\s+",
    re.IGNORECASE,
)

NON_GEO_CONSTITUENCY = frozenset(
    {
        "sitting rajya sabha",
        "nan",
        "",
    }
)

# Approximate state centroids for SYNTHETIC coordinates only.
STATE_CENTROIDS: dict[str, tuple[float, float]] = {
    "andaman and nicobar islands": (11.7401, 92.6586),
    "andhra pradesh": (15.9129, 79.7400),
    "arunachal pradesh": (28.2180, 94.7278),
    "assam": (26.2006, 92.9376),
    "bihar": (25.0961, 85.3131),
    "chhattisgarh": (21.2787, 81.8661),
    "delhi": (28.6139, 77.2090),
    "goa": (15.2993, 74.1240),
    "gujarat": (22.2587, 71.1924),
    "haryana": (29.0588, 76.0856),
    "himachal pradesh": (31.1048, 77.1734),
    "jammu and kashmir": (33.2778, 75.3412),
    "jharkhand": (23.6102, 85.2799),
    "karnataka": (15.3173, 75.7139),
    "kerala": (10.8505, 76.2711),
    "lakshadweep": (10.5667, 72.6417),
    "madhya pradesh": (22.9734, 78.6569),
    "maharashtra": (19.7515, 75.7139),
    "manipur": (24.6637, 93.9063),
    "meghalaya": (25.4670, 91.3662),
    "mizoram": (23.1645, 92.9376),
    "nagaland": (26.1584, 94.5624),
    "odisha": (20.9517, 85.0985),
    "puducherry": (11.9416, 79.8083),
    "punjab": (31.1471, 75.3412),
    "rajasthan": (27.0238, 74.2179),
    "sikkim": (27.5330, 88.5122),
    "tamil nadu": (11.1271, 78.6569),
    "telangana": (18.1124, 79.0193),
    "tripura": (23.9408, 91.9882),
    "uttar pradesh": (26.8467, 80.9462),
    "uttarakhand": (30.0668, 79.0193),
    "west bengal": (22.9868, 87.8550),
}

# Approximate Andhra Pradesh constituency points for SYNTHETIC coordinates only.
AP_CONSTITUENCY_COORDS: dict[str, tuple[float, float]] = {
    "kurnool": (15.8281, 78.0373),
    "vizianagaram": (18.1067, 83.3956),
    "araku(st)": (18.3273, 82.8775),
    "anantapur": (14.6819, 77.6006),
    "amalapuram(sc)": (16.5787, 82.0061),
    "chittoor": (13.2172, 79.1005),
    "rajampet": (14.1950, 79.1580),
    "ongole": (15.5057, 80.0499),
    "srikakulam": (18.2949, 83.8938),
    "nandyal": (15.4786, 78.4836),
    "narasaraopet": (16.2351, 80.0499),
    "kadapa": (14.4673, 78.8242),
    "guntur": (16.3067, 80.4365),
    "bapatla": (15.9044, 80.4675),
    "nellore(sc)": (14.4426, 79.9865),
    "nellore": (14.4426, 79.9865),
    "tirupati(sc)": (13.6288, 79.4192),
    "tirupati": (13.6288, 79.4192),
    "anakapalle": (17.6911, 83.0039),
    "machilipatnam": (16.1875, 81.1389),
    "hindupur": (13.8281, 77.4910),
    "visakhapatnam": (17.6868, 83.2185),
    "kakinada": (16.9891, 82.2475),
    "eluru": (16.7107, 81.0952),
}

VENDOR_TRADE = {
    "LIGHTING": "Lighting Works",
    "ROAD": "Roadworks",
    "WATER": "Water Systems",
    "COMMUNITY_HALL": "Community Works",
    "BOUNDARY_WALL": "Civil Works",
    "SANITATION": "Sanitation Works",
    "BUILDING": "Building Works",
    "OTHER": "General Works",
}

DURATION_DAYS = {
    "LIGHTING": (30, 90),
    "ROAD": (90, 240),
    "WATER": (60, 180),
    "COMMUNITY_HALL": (150, 360),
    "BOUNDARY_WALL": (45, 150),
    "SANITATION": (45, 150),
    "BUILDING": (120, 300),
    "OTHER": (60, 180),
}

REAL_COLUMNS = [
    "internal_project_id",
    "state",
    "constituency",
    "category",
    "work_description",
    "allocation_amount",
    "recommended_date",
    "status",
    "lifecycle_stage",
    "ida",
    "city",
    "block",
    "village",
    "mp_name",
    "house",
]

OUTPUT_COLUMNS = [
    "synthetic_record_id",
    "internal_project_id",
    "record_mode",
    "enrichment_source",
    "synthetic_as_of_date",
    "scenario_type",
    "demo_case_id",
    "mixed_signals",
    "overlap_group_id",
    "anomaly_notes",
    "synthetic_disclaimer",
    "real_state",
    "real_constituency",
    "real_category",
    "real_work_description",
    "real_allocation_amount",
    "real_recommended_date",
    "real_status",
    "real_lifecycle_stage",
    "real_ida",
    "real_city",
    "real_block",
    "real_village",
    "real_mp_name",
    "real_house",
    "implementing_district",
    "implementing_agency",
    "vendor_name",
    "sanction_date",
    "planned_start_date",
    "planned_completion_date",
    "actual_start_date",
    "actual_completion_date",
    "sanctioned_amount",
    "expenditure_amount",
    "latitude",
    "longitude",
    "coordinate_source",
    "project_area",
    "physical_progress_percent",
    "milestone_number",
    "milestone_amount",
    "milestone_total_amount",
]


@dataclass
class GenerationStats:
    seed: int
    as_of_date: str
    requested_records: int
    generated_records: int
    unique_internal_project_ids: int
    scenario_counts: dict[str, int]
    demo_case_ids: dict[str, str]
    source_csv: str
    source_sha256: str | None
    generated_at: str


@dataclass
class SyntheticWriteResult:
    csv_path: Path
    provenance_path: Path
    stats: GenerationStats
    frame: pd.DataFrame = field(repr=False)


def scenario_quota(n: int) -> dict[str, int]:
    """Largest-remainder split of n into the prototype scenario mix."""
    raw = [(name, n * pct) for name, pct in SCENARIO_PERCENTS]
    counts = {name: int(value) for name, value in raw}
    assigned = sum(counts.values())
    remainders = sorted(((value - int(value), name) for name, value in raw), reverse=True)
    index = 0
    while assigned < n:
        counts[remainders[index % len(remainders)][1]] += 1
        assigned += 1
        index += 1
    return counts


def apply_demo_slots(counts: dict[str, int]) -> dict[str, int]:
    out = dict(counts)
    for source, demo_name, _demo_id in DEMO_FROM_SCENARIO:
        if out.get(source, 0) > 0:
            out[source] -= 1
            out[demo_name] = out.get(demo_name, 0) + 1
    return out


def parse_iso_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def parse_int(value: object) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(round(float(text)))
    except ValueError:
        return None


def iso(value: date | None) -> str:
    return value.isoformat() if value is not None else ""


def add_days(value: date, days: int) -> date:
    return value + timedelta(days=days)


def clip_progress(value: int) -> int:
    return max(0, min(100, int(value)))


def usable_constituency(value: object) -> bool:
    return str(value or "").strip().lower() not in NON_GEO_CONSTITUENCY


def classify_work(description: str) -> str:
    text = description.lower()
    if "street light" in text or "lighting" in text:
        return "LIGHTING"
    if "road" in text or "pathway" in text or "culvert" in text or "bridge" in text:
        return "ROAD"
    if (
        "drinking water" in text
        or "pipeline" in text
        or "water plant" in text
        or "irrigation" in text
    ):
        return "WATER"
    if "sanitation" in text:
        return "SANITATION"
    if "boundary wall" in text:
        return "BOUNDARY_WALL"
    if "community" in text and any(token in text for token in ("hall", "center", "centre")):
        return "COMMUNITY_HALL"
    if "room" in text or "building" in text:
        return "BUILDING"
    return "OTHER"


def district_place_from_ida(ida: str) -> str:
    text = (ida or "").strip()
    if text.upper().endswith("_IDA"):
        text = text[:-4]
    stripped = IDA_ROLE_RE.sub("", text).strip(" -_")
    return stripped


def synthetic_district(ida: str, constituency: str, state: str) -> str:
    place = district_place_from_ida(ida)
    if not place and usable_constituency(constituency):
        place = str(constituency).strip()
    if not place:
        place = (state or "unspecified").strip() or "unspecified"
    return f"{place} [SYNTHETIC]"


def synthetic_agency(ida: str) -> str:
    source = (ida or "").strip() or "unspecified IDA from real extract"
    return f"SYNTHETIC implementing unit attached to {source}"


def synthetic_vendor(place: str, work_type: str, rng: random.Random) -> str:
    trade = VENDOR_TRADE.get(work_type, "General Works")
    suffix = rng.choice(("Contractor", "Constructions", "Agency"))
    clean_place = place.replace("[SYNTHETIC]", "").strip() or "Local"
    return f"SYNTHETIC {clean_place} {trade} {suffix}"


def synthetic_area(village: str, block: str, city: str, constituency: str, state: str, work_type: str) -> str:
    place = village or block or city
    if not place and usable_constituency(constituency):
        place = constituency
    if not place:
        place = state or "unspecified"
    label = work_type.replace("_", " ").title()
    return f"SYNTHETIC {label} site near {place}, {state}"


def base_coordinates(state: str, constituency: str) -> tuple[float, float]:
    state_key = (state or "").strip().lower()
    if state_key == "andhra pradesh" and usable_constituency(constituency):
        key = constituency.strip().lower()
        if key in AP_CONSTITUENCY_COORDS:
            return AP_CONSTITUENCY_COORDS[key]
    if state_key in STATE_CENTROIDS:
        return STATE_CENTROIDS[state_key]
    return STATE_CENTROIDS["andhra pradesh"]


def jitter_coords(
    base: tuple[float, float], rng: random.Random, spread: float
) -> tuple[float, float]:
    lat = base[0] + rng.uniform(-spread, spread)
    lon = base[1] + rng.uniform(-spread, spread)
    return (round(lat, 6), round(lon, 6))


def planned_duration_days(work_type: str, allocation: int, rng: random.Random) -> int:
    low, high = DURATION_DAYS.get(work_type, (60, 180))
    days = rng.randint(low, high)
    if allocation >= 2_000_000:
        days = int(days * 1.4)
    elif allocation >= 1_000_000:
        days = int(days * 1.15)
    return max(30, days)


def read_real_projects(path: Path = DEFAULT_CLEANED_CSV) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned real extract not found: {path}")
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [name for name in REAL_COLUMNS if name not in frame.columns]
    if missing:
        raise ValueError(f"Cleaned extract missing columns required for enrichment: {missing}")
    out = frame.loc[:, REAL_COLUMNS].copy()
    out["internal_project_id"] = out["internal_project_id"].astype(str).str.strip()
    out = out[out["internal_project_id"] != ""].drop_duplicates(
        subset=["internal_project_id"], keep="first"
    )
    return out.reset_index(drop=True)


def _status_of(row: pd.Series) -> str:
    return str(row.get("status") or "").strip()


def pick_demo_projects(frame: pd.DataFrame) -> dict[str, str]:
    """Deterministic, easy-to-find AP demo hosts. No RNG."""
    chosen: dict[str, str] = {}
    used: set[str] = set()

    def take(mask: pd.Series, key: str) -> None:
        if key in chosen:
            return
        subset = frame.loc[mask].copy()
        if subset.empty:
            return
        subset["_alloc"] = subset["allocation_amount"].map(lambda v: parse_int(v) or 0)
        subset = subset.sort_values(
            ["_alloc", "internal_project_id"], ascending=[False, True]
        )
        for pid in subset["internal_project_id"]:
            if pid not in used:
                chosen[key] = str(pid)
                used.add(str(pid))
                return

    ap = frame["state"].str.strip().str.lower() == "andhra pradesh"
    geo = frame["constituency"].map(usable_constituency)
    take(ap & geo & (frame["status"] == "Completed"), "GHOST")
    take(ap & geo & (frame["status"] == "Completed"), "OVERBILL")
    take(ap & geo & (frame["status"] == "Ongoing"), "STUCK")
    take(ap & geo & (frame["status"] == "Sanctioned"), "CLEAN")

    if "GHOST" not in chosen:
        take(frame["status"] == "Completed", "GHOST")
    if "OVERBILL" not in chosen:
        take(frame["status"] == "Completed", "OVERBILL")
    if "STUCK" not in chosen:
        take(frame["status"] == "Ongoing", "STUCK")
    if "STUCK" not in chosen:
        take(frame["status"] == "Sanctioned", "STUCK")
    if "CLEAN" not in chosen:
        take(frame["status"] == "Sanctioned", "CLEAN")
    if "CLEAN" not in chosen:
        take(frame["status"] == "Completed", "CLEAN")
    return chosen


def target_status_counts(available: dict[str, int], n: int) -> dict[str, int]:
    plan = {name: 0 for name in available}
    remaining = n

    def take(status: str, wanted: int) -> None:
        nonlocal remaining
        got = min(available.get(status, 0), remaining, max(0, wanted))
        plan[status] = plan.get(status, 0) + got
        remaining -= got

    take("Ongoing", available.get("Ongoing", 0))
    take("Completed", available.get("Completed", 0))
    take("Sanctioned", min(available.get("Sanctioned", 0), max(n // 4, 1)))
    take("", min(available.get("", 0), max(n // 50, 0)))
    take("Unsanctioned", remaining)
    if remaining:
        for status in sorted(available, key=lambda name: available[name], reverse=True):
            extra = min(available.get(status, 0) - plan.get(status, 0), remaining)
            if extra > 0:
                plan[status] = plan.get(status, 0) + extra
                remaining -= extra
            if remaining == 0:
                break
    return plan


def select_project_ids(
    frame: pd.DataFrame,
    n: int,
    rng: random.Random,
    pinned: list[str],
) -> list[str]:
    unique = frame.drop_duplicates("internal_project_id")
    if len(unique) < n:
        raise ValueError(
            f"Need {n} unique real internal_project_id values; found {len(unique)}"
        )
    pinned_set = [pid for pid in pinned if pid in set(unique["internal_project_id"])]
    selected: list[str] = list(dict.fromkeys(pinned_set))
    remaining_needed = n - len(selected)
    leftover = unique[~unique["internal_project_id"].isin(selected)]
    available: dict[str, list[str]] = defaultdict(list)
    for _, row in leftover.iterrows():
        available[_status_of(row)].append(str(row["internal_project_id"]))
    for status in available:
        available[status].sort()
    counts = target_status_counts({k: len(v) for k, v in available.items()}, remaining_needed)
    for status, k in counts.items():
        pool = available.get(status, [])
        if k <= 0 or not pool:
            continue
        selected.extend(rng.sample(pool, k) if k < len(pool) else list(pool))
    selected = list(dict.fromkeys(selected))
    if len(selected) < n:
        extras = sorted(set(unique["internal_project_id"]) - set(selected))
        selected.extend(rng.sample(extras, n - len(selected)))
    return sorted(selected[:n])


def _pool(ids: list[str], meta: dict[str, dict[str, str]], predicate) -> list[str]:
    return [pid for pid in ids if predicate(meta[pid])]


def assign_scenarios(
    selected_ids: list[str],
    meta: dict[str, dict[str, str]],
    quotas: dict[str, int],
    demo_map: dict[str, str],
    rng: random.Random,
) -> dict[str, tuple[str, str, str]]:
    """Return internal_project_id -> (scenario_type, mixed_signals, demo_case_id)."""
    assigned: dict[str, tuple[str, str, str]] = {}
    available = set(selected_ids)

    demo_scenario = {
        "GHOST": "DEMO_GHOST",
        "OVERBILL": "DEMO_OVERBILL",
        "STUCK": "DEMO_STUCK",
        "CLEAN": "DEMO_CLEAN",
    }
    for demo_id, pid in demo_map.items():
        if pid in available and quotas.get(demo_scenario[demo_id], 0) > 0:
            assigned[pid] = (demo_scenario[demo_id], "", demo_id)
            available.remove(pid)

    ordered = sorted(available)

    def take(pool: list[str], k: int) -> list[str]:
        eligible = [pid for pid in pool if pid in available]
        if k <= 0 or not eligible:
            return []
        chosen = rng.sample(eligible, min(k, len(eligible)))
        for pid in chosen:
            available.remove(pid)
        return chosen

    ghost_pool = _pool(ordered, meta, lambda m: m["status"] == "Completed")
    for pid in take(ghost_pool, quotas.get("EVIDENCE_GHOST", 0)):
        assigned[pid] = ("EVIDENCE_GHOST", "", "")

    stuck_pool = _pool(ordered, meta, lambda m: m["status"] == "Ongoing") + _pool(
        ordered, meta, lambda m: m["status"] == "Sanctioned"
    )
    for pid in take(stuck_pool, quotas.get("TIME_ANOMALY", 0)):
        assigned[pid] = ("TIME_ANOMALY", "", "")

    cost_pool = _pool(
        ordered,
        meta,
        lambda m: m["status"] in {"Sanctioned", "Ongoing", "Completed"},
    )
    for pid in take(cost_pool, quotas.get("COST_ANOMALY", 0)):
        assigned[pid] = ("COST_ANOMALY", "", "")

    mixed_pool = _pool(
        ordered,
        meta,
        lambda m: m["status"] in {"Ongoing", "Completed", "Sanctioned"},
    )
    mixed_ids = take(mixed_pool, quotas.get("MIXED", 0))
    for index, pid in enumerate(sorted(mixed_ids)):
        assigned[pid] = ("MIXED", MIXED_SIGNAL_CYCLE[index % len(MIXED_SIGNAL_CYCLE)], "")

    overlap_pool = sorted(available)
    for pid in take(overlap_pool, quotas.get("OVERLAP", 0)):
        assigned[pid] = ("OVERLAP", "", "")

    for pid in sorted(available):
        assigned[pid] = ("NORMAL", "", "")
    return assigned


def _blank_record(project: pd.Series, scenario: str, mixed: str, demo_id: str) -> dict[str, Any]:
    allocation = parse_int(project.get("allocation_amount"))
    return {
        "synthetic_record_id": "",
        "internal_project_id": str(project["internal_project_id"]),
        "record_mode": RECORD_MODE,
        "enrichment_source": ENRICHMENT_SOURCE,
        "synthetic_as_of_date": SYNTHETIC_AS_OF_DATE.isoformat(),
        "scenario_type": scenario,
        "demo_case_id": demo_id,
        "mixed_signals": mixed,
        "overlap_group_id": "",
        "anomaly_notes": "",
        "synthetic_disclaimer": SYNTHETIC_DISCLAIMER,
        "real_state": str(project.get("state") or ""),
        "real_constituency": str(project.get("constituency") or ""),
        "real_category": str(project.get("category") or ""),
        "real_work_description": str(project.get("work_description") or ""),
        "real_allocation_amount": "" if allocation is None else allocation,
        "real_recommended_date": str(project.get("recommended_date") or ""),
        "real_status": str(project.get("status") or ""),
        "real_lifecycle_stage": str(project.get("lifecycle_stage") or ""),
        "real_ida": str(project.get("ida") or ""),
        "real_city": str(project.get("city") or ""),
        "real_block": str(project.get("block") or ""),
        "real_village": str(project.get("village") or ""),
        "real_mp_name": str(project.get("mp_name") or ""),
        "real_house": str(project.get("house") or ""),
        "implementing_district": "",
        "implementing_agency": "",
        "vendor_name": "",
        "sanction_date": "",
        "planned_start_date": "",
        "planned_completion_date": "",
        "actual_start_date": "",
        "actual_completion_date": "",
        "sanctioned_amount": "",
        "expenditure_amount": "",
        "latitude": "",
        "longitude": "",
        "coordinate_source": (
            "SYNTHETIC approximate location from real state/constituency; not official GPS"
        ),
        "project_area": "",
        "physical_progress_percent": 0,
        "milestone_number": "",
        "milestone_amount": "",
        "milestone_total_amount": "",
    }


def _set_milestones(
    record: dict[str, Any],
    *,
    number: int,
    total: int,
    sanctioned: int,
) -> None:
    number = max(1, number)
    total = max(0, total)
    record["milestone_number"] = number
    record["milestone_total_amount"] = total
    record["milestone_amount"] = total // number if number else ""


def _apply_location(record: dict[str, Any], project: pd.Series, rng: random.Random) -> None:
    work_type = classify_work(str(project.get("work_description") or ""))
    district = synthetic_district(
        str(project.get("ida") or ""),
        str(project.get("constituency") or ""),
        str(project.get("state") or ""),
    )
    record["implementing_district"] = district
    record["implementing_agency"] = synthetic_agency(str(project.get("ida") or ""))
    place = district.replace("[SYNTHETIC]", "").strip()
    record["vendor_name"] = synthetic_vendor(place, work_type, rng)
    record["project_area"] = synthetic_area(
        str(project.get("village") or ""),
        str(project.get("block") or ""),
        str(project.get("city") or ""),
        str(project.get("constituency") or ""),
        str(project.get("state") or ""),
        work_type,
    )
    spread = 0.06 if (str(project.get("state") or "").lower() == "andhra pradesh") else 0.35
    lat, lon = jitter_coords(
        base_coordinates(str(project.get("state") or ""), str(project.get("constituency") or "")),
        rng,
        spread,
    )
    record["latitude"] = lat
    record["longitude"] = lon


def _normal_schedule(
    record: dict[str, Any],
    project: pd.Series,
    rng: random.Random,
    as_of: date,
) -> None:
    status = str(project.get("status") or "").strip()
    recommended = parse_iso_date(project.get("recommended_date"))
    allocation = parse_int(project.get("allocation_amount")) or 0
    work_type = classify_work(str(project.get("work_description") or ""))
    duration = planned_duration_days(work_type, allocation, rng)

    if status in {"", "Unsanctioned"}:
        record["physical_progress_percent"] = 0
        return

    if recommended is None:
        record["physical_progress_percent"] = 0 if status != "Completed" else 100
        return

    sanction = add_days(recommended, rng.randint(7, 40))
    if sanction < recommended:
        sanction = recommended
    record["sanction_date"] = iso(sanction)
    record["sanctioned_amount"] = allocation

    if status == "Sanctioned":
        planned_start = max(add_days(sanction, rng.randint(10, 25)), as_of - timedelta(days=7))
        if planned_start < sanction:
            planned_start = sanction
        planned_end = add_days(planned_start, duration)
        record["planned_start_date"] = iso(planned_start)
        record["planned_completion_date"] = iso(planned_end)
        record["physical_progress_percent"] = 0
        record["expenditure_amount"] = 0
        return

    if status == "Ongoing":
        planned_start = add_days(sanction, rng.randint(7, 21))
        if planned_start < sanction:
            planned_start = sanction
        planned_end = add_days(planned_start, duration)
        if planned_end <= as_of:
            planned_end = add_days(as_of, rng.randint(30, 150))
        actual_start = add_days(planned_start, rng.randint(0, 14))
        if actual_start < sanction:
            actual_start = sanction
        progress = rng.randint(25, 70)
        expenditure = int(round(allocation * progress / 100 * rng.uniform(0.85, 0.98)))
        record["planned_start_date"] = iso(planned_start)
        record["planned_completion_date"] = iso(planned_end)
        record["actual_start_date"] = iso(actual_start)
        record["physical_progress_percent"] = clip_progress(progress)
        record["expenditure_amount"] = min(expenditure, allocation)
        _set_milestones(
            record,
            number=rng.randint(1, 3),
            total=int(record["expenditure_amount"]),
            sanctioned=allocation,
        )
        return

    if status == "Completed":
        planned_start = add_days(sanction, rng.randint(7, 21))
        if planned_start < sanction:
            planned_start = sanction
        planned_end = add_days(planned_start, duration)
        actual_start = add_days(planned_start, rng.randint(0, 10))
        if actual_start < sanction:
            actual_start = sanction
        actual_end = add_days(planned_end, rng.randint(-10, 12))
        if actual_end < actual_start:
            actual_end = actual_start
        if actual_end > as_of:
            actual_end = as_of
        if planned_end < planned_start:
            planned_end = add_days(planned_start, duration)
        expenditure = int(round(allocation * rng.uniform(0.90, 1.00)))
        record["planned_start_date"] = iso(planned_start)
        record["planned_completion_date"] = iso(planned_end)
        record["actual_start_date"] = iso(actual_start)
        record["actual_completion_date"] = iso(actual_end)
        record["physical_progress_percent"] = 100
        record["expenditure_amount"] = min(expenditure, allocation)
        _set_milestones(
            record,
            number=rng.randint(2, 4),
            total=int(record["expenditure_amount"]),
            sanctioned=allocation,
        )


def _ensure_sanctioned(record: dict[str, Any], project: pd.Series, rng: random.Random, as_of: date) -> int:
    allocation = parse_int(project.get("allocation_amount")) or 0
    if record["sanctioned_amount"] == "":
        record["sanctioned_amount"] = max(allocation, 1)
    if not record["sanction_date"]:
        recommended = parse_iso_date(project.get("recommended_date")) or add_days(as_of, -90)
        record["sanction_date"] = iso(add_days(recommended, rng.randint(7, 21)))
    return int(record["sanctioned_amount"])


def apply_cost_anomaly(record: dict[str, Any], project: pd.Series, rng: random.Random, as_of: date) -> None:
    sanctioned = _ensure_sanctioned(record, project, rng, as_of)
    factor = rng.uniform(1.35, 2.15)
    expenditure = max(sanctioned + 1, int(round(sanctioned * factor)))
    record["expenditure_amount"] = expenditure
    total = max(sanctioned + 1, int(round(sanctioned * rng.uniform(1.08, 1.45))))
    _set_milestones(record, number=rng.randint(2, 4), total=total, sanctioned=sanctioned)
    record["anomaly_notes"] = (
        (record["anomaly_notes"] + " | " if record["anomaly_notes"] else "")
        + "SYNTHETIC COST_ANOMALY/OVERBILL signal for prototype testing; not a legal finding."
    )


def apply_time_anomaly(record: dict[str, Any], project: pd.Series, rng: random.Random, as_of: date) -> None:
    status = str(project.get("status") or "").strip()
    recommended = parse_iso_date(project.get("recommended_date")) or add_days(as_of, -180)
    sanction = parse_iso_date(record["sanction_date"]) or add_days(recommended, 10)
    if sanction < recommended:
        sanction = recommended
    record["sanction_date"] = iso(sanction)
    if record["sanctioned_amount"] == "":
        record["sanctioned_amount"] = parse_int(project.get("allocation_amount")) or 0

    planned_start = add_days(sanction, rng.randint(7, 20))
    if planned_start < sanction:
        planned_start = sanction
    planned_end = add_days(as_of, -rng.randint(60, 180))
    if planned_end <= planned_start:
        planned_end = add_days(planned_start, 45)
        if planned_end >= as_of:
            planned_end = add_days(as_of, -30)
            if planned_end <= planned_start:
                planned_start = add_days(planned_end, -60)
                if planned_start < sanction:
                    planned_start = sanction
                    planned_end = add_days(planned_start, 40)
    record["planned_start_date"] = iso(planned_start)
    record["planned_completion_date"] = iso(planned_end)

    if status == "Completed":
        actual_start = planned_start
        actual_end = add_days(planned_end, rng.randint(90, 160))
        if actual_end < actual_start:
            actual_end = actual_start
        record["actual_start_date"] = iso(actual_start)
        record["actual_completion_date"] = iso(actual_end)
        record["physical_progress_percent"] = 100
    else:
        actual_start = planned_start
        record["actual_start_date"] = iso(actual_start)
        record["actual_completion_date"] = ""
        record["physical_progress_percent"] = clip_progress(rng.randint(5, 18))
        sanctioned = int(record["sanctioned_amount"] or 0)
        spent = int(round(sanctioned * record["physical_progress_percent"] / 100 * 0.9))
        record["expenditure_amount"] = min(spent, sanctioned) if sanctioned else spent
    record["anomaly_notes"] = (
        (record["anomaly_notes"] + " | " if record["anomaly_notes"] else "")
        + "SYNTHETIC TIME_ANOMALY/STUCK signal for prototype testing; not a legal finding."
    )


def apply_ghost(record: dict[str, Any], project: pd.Series, rng: random.Random, as_of: date) -> None:
    allocation = parse_int(project.get("allocation_amount")) or 0
    recommended = parse_iso_date(project.get("recommended_date")) or add_days(as_of, -120)
    sanction = parse_iso_date(record["sanction_date"]) or add_days(recommended, 10)
    record["sanction_date"] = iso(max(sanction, recommended))
    record["sanctioned_amount"] = allocation
    planned_start = parse_iso_date(record["planned_start_date"]) or add_days(sanction, 10)
    planned_end = parse_iso_date(record["planned_completion_date"]) or add_days(planned_start, 90)
    actual_start = parse_iso_date(record["actual_start_date"]) or planned_start
    actual_end = parse_iso_date(record["actual_completion_date"]) or min(
        as_of, add_days(planned_end, 5)
    )
    if actual_end < actual_start:
        actual_end = actual_start
    record["planned_start_date"] = iso(planned_start)
    record["planned_completion_date"] = iso(planned_end)
    record["actual_start_date"] = iso(actual_start)
    record["actual_completion_date"] = iso(actual_end)
    record["physical_progress_percent"] = 100
    if record["expenditure_amount"] == "":
        record["expenditure_amount"] = int(round(allocation * 0.95)) if allocation else 0
    if rng.random() < 0.5:
        record["latitude"] = ""
        record["longitude"] = ""
        record["coordinate_source"] = "SYNTHETIC missing GPS for GHOST prototype case; not official"
        note = "SYNTHETIC EVIDENCE/GHOST: completed claim with no coordinates."
    else:
        record["latitude"] = round(10.05 + rng.uniform(-0.2, 0.2), 6)
        record["longitude"] = round(68.40 + rng.uniform(-0.2, 0.2), 6)
        record["coordinate_source"] = (
            "SYNTHETIC implausible offshore coordinates for GHOST prototype case; not official GPS"
        )
        note = "SYNTHETIC EVIDENCE/GHOST: completed claim with coordinates far from the real state."
    record["anomaly_notes"] = (
        (record["anomaly_notes"] + " | " if record["anomaly_notes"] else "") + note
    )


def apply_demo_overrides(
    record: dict[str, Any],
    project: pd.Series,
    demo_id: str,
    rng: random.Random,
    as_of: date,
) -> None:
    if demo_id == "CLEAN":
        record["anomaly_notes"] = (
            "DEMO_CLEAN: internally consistent SYNTHETIC enrichment for the prototype clean case."
        )
        return
    if demo_id == "OVERBILL":
        apply_cost_anomaly(record, project, rng, as_of)
        sanctioned = int(record["sanctioned_amount"] or 0)
        record["expenditure_amount"] = max(sanctioned + 1, int(round(sanctioned * 1.80)))
        _set_milestones(record, number=3, total=max(sanctioned + 1, int(round(sanctioned * 1.25))), sanctioned=sanctioned)
        record["demo_case_id"] = "OVERBILL"
        record["anomaly_notes"] = (
            "DEMO_OVERBILL: SYNTHETIC expenditure and milestone total exceed sanctioned amount. "
            "Prototype case only; not a legal finding."
        )
        return
    if demo_id == "STUCK":
        apply_time_anomaly(record, project, rng, as_of)
        record["actual_completion_date"] = ""
        record["physical_progress_percent"] = 12
        sanctioned = int(record["sanctioned_amount"] or 0)
        spent = min(sanctioned, int(round(sanctioned * 0.12 * 0.9))) if sanctioned else 0
        record["expenditure_amount"] = spent
        if sanctioned:
            _set_milestones(record, number=1, total=spent, sanctioned=sanctioned)
        record["demo_case_id"] = "STUCK"
        record["anomaly_notes"] = (
            "DEMO_STUCK: SYNTHETIC overdue schedule with low physical progress and no completion date. "
            "Prototype case only; not a legal finding."
        )
        return
    if demo_id == "GHOST":
        apply_ghost(record, project, rng, as_of)
        record["latitude"] = 10.050000
        record["longitude"] = 68.400000
        record["coordinate_source"] = (
            "SYNTHETIC implausible offshore coordinates for DEMO_GHOST; not official GPS"
        )
        record["physical_progress_percent"] = 100
        record["demo_case_id"] = "GHOST"
        record["anomaly_notes"] = (
            "DEMO_GHOST: SYNTHETIC completed claim with coordinates that do not match the real "
            "state/constituency. Prototype case only; not a legal finding."
        )


def apply_scenario(
    record: dict[str, Any],
    project: pd.Series,
    rng: random.Random,
    as_of: date,
) -> None:
    scenario = record["scenario_type"]
    mixed = [part.strip() for part in str(record["mixed_signals"] or "").split(",") if part.strip()]
    demo_id = str(record["demo_case_id"] or "")

    signals = list(mixed)
    if scenario == "COST_ANOMALY" or "COST_ANOMALY" in mixed:
        signals.append("COST_ANOMALY")
    if scenario == "TIME_ANOMALY" or "TIME_ANOMALY" in mixed:
        signals.append("TIME_ANOMALY")
    if scenario == "EVIDENCE_GHOST" or "EVIDENCE_GHOST" in mixed:
        signals.append("EVIDENCE_GHOST")

    if demo_id:
        apply_demo_overrides(record, project, demo_id, rng, as_of)
        return

    if "TIME_ANOMALY" in signals:
        apply_time_anomaly(record, project, rng, as_of)
    if "COST_ANOMALY" in signals:
        apply_cost_anomaly(record, project, rng, as_of)
    if "EVIDENCE_GHOST" in signals:
        apply_ghost(record, project, rng, as_of)
    if scenario == "MIXED" and not record["anomaly_notes"]:
        record["anomaly_notes"] = (
            "SYNTHETIC MIXED multi-signal case for prototype testing; not a legal finding."
        )
    elif scenario == "MIXED":
        record["anomaly_notes"] = (
            record["anomaly_notes"]
            + " | SYNTHETIC MIXED signals: "
            + (record["mixed_signals"] or "")
        )


def apply_overlap_clusters(records: list[dict[str, Any]], rng: random.Random, seed: int) -> None:
    members = [
        rec
        for rec in records
        if rec["scenario_type"] == "OVERLAP" or "OVERLAP" in str(rec.get("mixed_signals") or "")
    ]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in members:
        grouped[(str(rec["real_state"]), str(rec["real_constituency"]))].append(rec)

    group_no = 1
    leftovers: list[dict[str, Any]] = []

    def stamp(chunk: list[dict[str, Any]]) -> None:
        nonlocal group_no
        if not chunk:
            return
        lead = chunk[0]
        group_id = f"{SYNTHETIC_ID_PREFIX}overlap:{seed}:{group_no:04d}"
        base_lat = lead["latitude"] if lead["latitude"] != "" else 15.9129
        base_lon = lead["longitude"] if lead["longitude"] != "" else 79.7400
        vendor = lead["vendor_name"]
        for index, rec in enumerate(chunk):
            rec["overlap_group_id"] = group_id
            rec["vendor_name"] = vendor
            if index == 0:
                rec["latitude"] = base_lat
                rec["longitude"] = base_lon
            else:
                rec["latitude"] = round(float(base_lat) + rng.uniform(-0.0012, 0.0012), 6)
                rec["longitude"] = round(float(base_lon) + rng.uniform(-0.0012, 0.0012), 6)
            if rec["scenario_type"] == "OVERLAP" and not rec["anomaly_notes"]:
                rec["anomaly_notes"] = (
                    "SYNTHETIC OVERLAP group: nearby coordinates and shared vendor for prototype "
                    "testing; not a legal finding."
                )
        group_no += 1

    for key in sorted(grouped):
        items = sorted(grouped[key], key=lambda rec: rec["internal_project_id"])
        index = 0
        while index < len(items):
            remaining = len(items) - index
            if remaining == 1:
                leftovers.append(items[index])
                break
            size = 4 if remaining >= 4 and remaining != 5 else (3 if remaining >= 3 else 2)
            if remaining == 5:
                size = 3
            stamp(items[index : index + size])
            index += size

    leftovers.sort(key=lambda rec: rec["internal_project_id"])
    index = 0
    while index < len(leftovers):
        chunk = leftovers[index : index + 2]
        if len(chunk) == 1 and group_no > 1:
            chunk[0]["overlap_group_id"] = f"{SYNTHETIC_ID_PREFIX}overlap:{seed}:{group_no - 1:04d}"
            break
        stamp(chunk)
        index += 2


def _row_meta(row: pd.Series) -> dict[str, str]:
    return {
        "status": _status_of(row),
        "state": str(row.get("state") or ""),
        "lifecycle_stage": str(row.get("lifecycle_stage") or ""),
    }


def generate_synthetic_enrichment(
    projects: pd.DataFrame,
    *,
    n: int = TARGET_RECORD_COUNT,
    seed: int = DEFAULT_SEED,
    as_of: date = SYNTHETIC_AS_OF_DATE,
) -> tuple[pd.DataFrame, GenerationStats]:
    if n < 1:
        raise ValueError("n must be >= 1")
    rng = random.Random(seed)
    demo_map = pick_demo_projects(projects)
    selected_ids = select_project_ids(projects, n, rng, list(demo_map.values()))
    by_id = projects.set_index("internal_project_id", drop=False)
    meta = {pid: _row_meta(by_id.loc[pid]) for pid in selected_ids}
    quotas = apply_demo_slots(scenario_quota(n))
    assigned = assign_scenarios(selected_ids, meta, quotas, demo_map, rng)

    records: list[dict[str, Any]] = []
    for index, pid in enumerate(sorted(selected_ids), start=1):
        project = by_id.loc[pid]
        if isinstance(project, pd.DataFrame):
            project = project.iloc[0]
        scenario, mixed, demo_id = assigned[pid]
        record = _blank_record(project, scenario, mixed, demo_id)
        record["synthetic_record_id"] = f"{SYNTHETIC_ID_PREFIX}enr:{seed}:{index:06d}"
        _apply_location(record, project, rng)
        _normal_schedule(record, project, rng, as_of)
        apply_scenario(record, project, rng, as_of)
        records.append(record)

    apply_overlap_clusters(records, rng, seed)
    frame = pd.DataFrame.from_records(records, columns=OUTPUT_COLUMNS)
    counts: dict[str, int] = defaultdict(int)
    for rec in records:
        counts[str(rec["scenario_type"])] += 1
    demo_ids = {
        rec["demo_case_id"]: rec["internal_project_id"]
        for rec in records
        if rec["demo_case_id"]
    }
    stats = GenerationStats(
        seed=seed,
        as_of_date=as_of.isoformat(),
        requested_records=n,
        generated_records=len(frame),
        unique_internal_project_ids=int(frame["internal_project_id"].nunique()),
        scenario_counts=dict(sorted(counts.items())),
        demo_case_ids=demo_ids,
        source_csv="",
        source_sha256=None,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
    return frame, stats


def assert_synthetic_output_dir(path: Path) -> None:
    resolved = path.resolve()
    forbidden = [
        (REPO_ROOT / "data" / "raw").resolve(),
        (REPO_ROOT / "data" / "processed").resolve(),
    ]
    for banned in forbidden:
        if resolved == banned or banned in resolved.parents:
            raise ValueError(f"Refusing to write synthetic enrichment under {banned}")


def _serialize_cell(value: object) -> object:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return value


def write_synthetic_csv(frame: pd.DataFrame, path: Path) -> None:
    assert_synthetic_output_dir(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = frame.loc[:, [name for name in OUTPUT_COLUMNS if name in frame.columns]]
    serialized = ordered.map(_serialize_cell) if hasattr(ordered, "map") else ordered.applymap(
        _serialize_cell
    )
    serialized.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")


def write_provenance(path: Path, stats: GenerationStats, csv_path: Path) -> None:
    assert_synthetic_output_dir(path.parent)
    payload = {
        "dataset_name": "SARVSAKSHI synthetic enrichment (HYBRID prototype layer)",
        "record_mode": RECORD_MODE,
        "enrichment_source": ENRICHMENT_SOURCE,
        "seed": stats.seed,
        "synthetic_as_of_date": stats.as_of_date,
        "output_filename": csv_path.name,
        "output_sha256": sha256_file(csv_path) if csv_path.is_file() else None,
        "linked_real_source": stats.source_csv,
        "linked_real_source_sha256": stats.source_sha256,
        "generated_at": stats.generated_at,
        "generated_records": stats.generated_records,
        "unique_internal_project_ids": stats.unique_internal_project_ids,
        "scenario_counts": stats.scenario_counts,
        "demo_case_ids": stats.demo_case_ids,
        "notes": (
            "NOT a government dataset. Synthetic prototype/testing layer only. "
            "Does not modify the real cleaned extract or SQLite project table. "
            "internal_project_id is a SARVSAKSHI surrogate, not an official MPLADS ID. "
            "synthetic_record_id is not an official MPLADS ID. "
            "District, vendor, GPS, expenditure, and unobserved dates are SYNTHETIC."
        ),
        "disclaimer": SYNTHETIC_DISCLAIMER,
        "stats": asdict(stats),
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_and_write(
    *,
    source_csv: Path = DEFAULT_CLEANED_CSV,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    n: int = TARGET_RECORD_COUNT,
    seed: int = DEFAULT_SEED,
) -> SyntheticWriteResult:
    assert_synthetic_output_dir(output_dir)
    projects = read_real_projects(source_csv)
    frame, stats = generate_synthetic_enrichment(projects, n=n, seed=seed)
    stats.source_csv = str(source_csv)
    stats.source_sha256 = sha256_file(source_csv) if source_csv.is_file() else None
    csv_path = output_dir / DEFAULT_OUTPUT_CSV.name
    provenance_path = output_dir / DEFAULT_PROVENANCE_PATH.name
    write_synthetic_csv(frame, csv_path)
    write_provenance(provenance_path, stats, csv_path)
    return SyntheticWriteResult(
        csv_path=csv_path,
        provenance_path=provenance_path,
        stats=stats,
        frame=frame,
    )
