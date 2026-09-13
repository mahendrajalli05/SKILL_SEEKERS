"""Work-level cleaning for the primary free MPLADS extract.

Reads the GitHub recommended-works CSV only. Does not merge OpenCity MP-level
summaries, does not invent government fields, and never writes to ``data/raw``.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from app.config import REPO_ROOT
from app.domain.enums import LifecycleStage
from app.pipeline.discover import build_provenance, sha256_file
from app.pipeline.load import load_tabular
from app.pipeline.profile import MISSING_TOKENS, is_andhra_pradesh_state
from app.pipeline.types import Provenance

PRIMARY_WORKS_FILENAME = "github_vonter_india-mplads-works_MPLADS.csv"
INTERNAL_ID_PREFIX = "internal:"
INTERNAL_ID_SCHEME = "sarvsakshi_internal_work_v1"
INTERNAL_ID_KIND = "internal_surrogate_hash"

# Observed STATUS values in the primary extract. Not an official code list.
OBSERVED_STATUS_CANONICAL = {
    "unsanctioned": "Unsanctioned",
    "sanctioned": "Sanctioned",
    "ongoing": "Ongoing",
    "completed": "Completed",
}

# Internal lifecycle grouping only. Does not create a new government status.
STATUS_TO_LIFECYCLE = {
    "Unsanctioned": LifecycleStage.FUTURE.value,
    "Sanctioned": LifecycleStage.FUTURE.value,
    "Ongoing": LifecycleStage.ONGOING.value,
    "Completed": LifecycleStage.COMPLETED.value,
}

OBSERVED_CATEGORY_CANONICAL = {
    "normal/others": "Normal/Others",
    "repair and renovation": "Repair and Renovation",
    "trust and society": "Trust and Society",
    "bar and associations": "Bar and Associations",
}

OBSERVED_IDA_APPROVAL_CANONICAL = {
    "action pending": "Action Pending",
    "approved by ida": "Approved by IDA",
    "rejected by ida": "Rejected by IDA",
}

OBSERVED_HOUSE_CANONICAL = {
    "lok sabha": "Lok Sabha",
    "rajya sabha": "Rajya Sabha",
}

SOURCE_COLUMNS = [
    "MP NAME",
    "WORK",
    "CATEGORY",
    "STATE",
    "CONSTITUENCY",
    "IDA",
    "CITY",
    "WARD",
    "BLOCK",
    "VILLAGE",
    "RECOMMENDED DATE",
    "ALLOCATION AMOUNT",
    "IDA APPROVAL",
    "STATUS",
    "HOUSE",
]

SOURCE_PRESERVE_MAP = {
    "MP NAME": "source_mp_name",
    "WORK": "source_work",
    "CATEGORY": "source_category",
    "STATE": "source_state",
    "CONSTITUENCY": "source_constituency",
    "IDA": "source_ida",
    "CITY": "source_city",
    "WARD": "source_ward",
    "BLOCK": "source_block",
    "VILLAGE": "source_village",
    "RECOMMENDED DATE": "source_recommended_date",
    "ALLOCATION AMOUNT": "source_allocation_amount",
    "IDA APPROVAL": "source_ida_approval",
    "STATUS": "source_status",
    "HOUSE": "source_house",
}

HASH_FIELD_ORDER = [
    "mp_name",
    "work_description",
    "category",
    "state",
    "constituency",
    "ida",
    "city",
    "ward",
    "block",
    "village",
    "recommended_date",
    "allocation_amount",
    "ida_approval",
    "status",
    "house",
]

ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
CLEANED_SECTION_START = "<!-- BEGIN CLEANED DATASET -->"
CLEANED_SECTION_END = "<!-- END CLEANED DATASET -->"

DEFAULT_RAW_PATH = REPO_ROOT / "data" / "raw" / PRIMARY_WORKS_FILENAME
DEFAULT_OUTPUT_CSV = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.csv"
DEFAULT_OUTPUT_PROVENANCE = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.provenance.json"
DEFAULT_CLEANING_REPORT = REPO_ROOT / "DATA_CLEANING_REPORT.md"
DEFAULT_DICTIONARY_PATH = REPO_ROOT / "DATA_DICTIONARY.md"
DEFAULT_PROFILING_PATH = REPO_ROOT / "DATA_PROFILING_REPORT.md"


def is_missing_value(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return True
    text = str(value).strip().lower()
    return text in MISSING_TOKENS


def original_source_text(value: object) -> str:
    """Exact source cell as text. Empty/NA cells become an empty string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def normalize_whitespace(value: object) -> str:
    if is_missing_value(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_text_field(value: object) -> str:
    return normalize_whitespace(value)


def normalize_ida(value: object) -> str:
    text = normalize_whitespace(value)
    if text.lower().endswith("_ida"):
        return text[:-4] + "_IDA"
    return text


def _canonical_lookup(value: object, mapping: dict[str, str]) -> str:
    text = normalize_whitespace(value)
    if not text:
        return ""
    return mapping.get(text.lower(), text)


def normalize_category(value: object) -> str:
    return _canonical_lookup(value, OBSERVED_CATEGORY_CANONICAL)


def normalize_ida_approval(value: object) -> str:
    return _canonical_lookup(value, OBSERVED_IDA_APPROVAL_CANONICAL)


def normalize_house(value: object) -> str:
    return _canonical_lookup(value, OBSERVED_HOUSE_CANONICAL)


def normalize_status(value: object) -> str:
    """Return an observed STATUS spelling, or empty. Does not invent statuses."""
    text = normalize_whitespace(value)
    if not text:
        return ""
    return OBSERVED_STATUS_CANONICAL.get(text.lower(), text)


def lifecycle_from_status(status: object) -> str:
    canonical = normalize_status(status)
    return STATUS_TO_LIFECYCLE.get(canonical, LifecycleStage.UNKNOWN.value)


def normalize_date(value: object) -> str:
    """Return ISO YYYY-MM-DD, or empty when missing/unparseable. Does not invent dates."""
    if is_missing_value(value):
        return ""
    text = normalize_whitespace(value)
    if not text:
        return ""
    match = ISO_DATE.match(text)
    if match:
        year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return ""
    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        parsed = pd.to_datetime(text, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        return ""
    return pd.Timestamp(parsed).date().isoformat()


def normalize_amount(value: object) -> int | None:
    """Parse a monetary cell to an integer. None if missing or unparseable.

    Indian grouping commas are stripped. No unit conversion is applied; the
    source column does not state a unit.
    """
    if is_missing_value(value):
        return None
    text = unicodedata.normalize("NFKC", str(value)).strip()
    text = text.replace("\u00a0", " ")
    text = text.replace(",", "")
    text = re.sub(r"(?i)(?:\brs\.?|\binr\b|₹)", "", text)
    text = text.replace("₹", "").strip()
    text = re.sub(r"^\.+", "", text).strip()
    text = re.sub(r"\s+", "", text)
    if not text or is_missing_value(text):
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    if number != number:
        return None
    if number.is_integer():
        return int(number)
    return None


def _hash_amount_token(amount: int | None) -> str:
    return "" if amount is None else str(amount)


def make_internal_project_id(record: dict[str, object]) -> str:
    """Deterministic internal surrogate. Not an official MPLADS work ID."""
    parts = [INTERNAL_ID_SCHEME]
    for key in HASH_FIELD_ORDER:
        value = record.get(key, "")
        if key == "allocation_amount":
            if value is None or value == "":
                token = ""
            elif isinstance(value, bool):
                token = _hash_amount_token(normalize_amount(value))
            elif isinstance(value, (int, float)) and value == value:
                token = str(int(value)) if float(value).is_integer() else _hash_amount_token(None)
            else:
                token = _hash_amount_token(normalize_amount(value))
        else:
            token = "" if value is None else str(value)
        parts.append(f"{key}={token}")
    payload = "\n".join(parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{INTERNAL_ID_PREFIX}{digest}"


def validate_source_columns(columns: list[str]) -> None:
    missing = [name for name in SOURCE_COLUMNS if name not in columns]
    extra_note = [name for name in columns if name not in SOURCE_COLUMNS]
    if missing:
        raise ValueError(
            "Primary extract is missing expected source columns: "
            + ", ".join(missing)
            + (f" (also saw: {extra_note})" if extra_note else "")
        )


@dataclass
class CleaningStats:
    source_filename: str
    raw_row_count: int
    exact_extra_duplicate_count: int
    cleaned_row_count: int
    collapsed_row_count: int
    andhra_pradesh_raw_count: int
    andhra_pradesh_cleaned_count: int
    observed_status_values: list[str]
    raw_status_counts: dict[str, int]
    cleaned_status_counts: dict[str, int]
    lifecycle_counts: dict[str, int]
    amount_unparseable_count: int
    date_unparseable_count: int
    blank_status_cleaned_count: int
    blank_constituency_cleaned_count: int
    cleaned_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    )


def clean_works_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, CleaningStats]:
    """Normalize the primary work-level extract. Does not add district/vendor/GPS/expenditure."""
    validate_source_columns(list(frame.columns))
    working = frame.loc[:, SOURCE_COLUMNS].copy()
    n_raw = len(working)
    exact_extra_dups = int(working.duplicated(keep="first").sum())

    cleaned = pd.DataFrame(
        {
            "internal_id_kind": INTERNAL_ID_KIND,
            "internal_id_scheme": INTERNAL_ID_SCHEME,
            "source_dataset": PRIMARY_WORKS_FILENAME,
            "source_first_row_number": range(1, n_raw + 1),
        }
    )
    for original, preserved in SOURCE_PRESERVE_MAP.items():
        cleaned[preserved] = working[original].map(original_source_text)
    cleaned["mp_name"] = working["MP NAME"].map(normalize_text_field)
    cleaned["work_description"] = working["WORK"].map(normalize_text_field)
    cleaned["category"] = working["CATEGORY"].map(normalize_category)
    cleaned["state"] = working["STATE"].map(normalize_text_field)
    cleaned["constituency"] = working["CONSTITUENCY"].map(normalize_text_field)
    cleaned["ida"] = working["IDA"].map(normalize_ida)
    cleaned["city"] = working["CITY"].map(normalize_text_field)
    cleaned["ward"] = working["WARD"].map(normalize_text_field)
    cleaned["block"] = working["BLOCK"].map(normalize_text_field)
    cleaned["village"] = working["VILLAGE"].map(normalize_text_field)
    cleaned["recommended_date"] = working["RECOMMENDED DATE"].map(normalize_date)
    cleaned["allocation_amount"] = working["ALLOCATION AMOUNT"].map(normalize_amount)
    cleaned["ida_approval"] = working["IDA APPROVAL"].map(normalize_ida_approval)
    cleaned["status"] = working["STATUS"].map(normalize_status)
    cleaned["house"] = working["HOUSE"].map(normalize_house)
    cleaned["lifecycle_stage"] = cleaned["status"].map(lifecycle_from_status)
    cleaned["internal_project_id"] = [
        make_internal_project_id(
            {key: row[key] for key in HASH_FIELD_ORDER}
        )
        for row in cleaned[HASH_FIELD_ORDER].to_dict(orient="records")
    ]
    duplicate_counts = cleaned.groupby("internal_project_id", sort=False).size()
    first_index = cleaned.groupby("internal_project_id", sort=False).head(1).index
    unique = cleaned.loc[first_index].copy()
    unique["source_duplicate_count"] = unique["internal_project_id"].map(duplicate_counts).astype(int)
    unique = unique.reset_index(drop=True)

    status_counts = Counter(str(v) if v else "(blank)" for v in unique["status"].tolist())
    raw_status_counts = Counter(normalize_status(v) or "(blank)" for v in working["STATUS"].tolist())
    ap_raw = int(working["STATE"].map(is_andhra_pradesh_state).sum())
    ap_clean = int(unique["state"].map(is_andhra_pradesh_state).sum())

    stats = CleaningStats(
        source_filename=PRIMARY_WORKS_FILENAME,
        raw_row_count=n_raw,
        exact_extra_duplicate_count=exact_extra_dups,
        cleaned_row_count=len(unique),
        collapsed_row_count=n_raw - len(unique),
        andhra_pradesh_raw_count=ap_raw,
        andhra_pradesh_cleaned_count=ap_clean,
        observed_status_values=sorted(OBSERVED_STATUS_CANONICAL.values()),
        raw_status_counts=dict(raw_status_counts),
        cleaned_status_counts=dict(status_counts),
        lifecycle_counts=dict(Counter(unique["lifecycle_stage"].tolist())),
        amount_unparseable_count=int(unique["allocation_amount"].isna().sum()),
        date_unparseable_count=int((unique["recommended_date"] == "").sum()),
        blank_status_cleaned_count=int((unique["status"] == "").sum()),
        blank_constituency_cleaned_count=int((unique["constituency"] == "").sum()),
    )
    return unique, stats


OUTPUT_COLUMN_ORDER = [
    "internal_project_id",
    "internal_id_kind",
    "internal_id_scheme",
    "source_dataset",
    "source_first_row_number",
    "source_duplicate_count",
    "source_mp_name",
    "source_work",
    "source_category",
    "source_state",
    "source_constituency",
    "source_ida",
    "source_city",
    "source_ward",
    "source_block",
    "source_village",
    "source_recommended_date",
    "source_allocation_amount",
    "source_ida_approval",
    "source_status",
    "source_house",
    "mp_name",
    "work_description",
    "category",
    "state",
    "constituency",
    "ida",
    "city",
    "ward",
    "block",
    "village",
    "recommended_date",
    "allocation_amount",
    "ida_approval",
    "status",
    "house",
    "lifecycle_stage",
]


def order_cleaned_columns(frame: pd.DataFrame) -> pd.DataFrame:
    columns = [name for name in OUTPUT_COLUMN_ORDER if name in frame.columns]
    leftover = [name for name in frame.columns if name not in columns]
    return frame.loc[:, columns + leftover]


def write_cleaned_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = order_cleaned_columns(frame)
    ordered.to_csv(path, index=False, encoding="utf-8")


def write_processed_provenance(
    path: Path,
    *,
    source_provenance: Provenance,
    output_csv: Path,
    stats: CleaningStats,
) -> None:
    payload = {
        "dataset_name": "SARVSAKSHI cleaned work-level extract (internal)",
        "output_filename": output_csv.name,
        "primary_source_filename": source_provenance.original_filename,
        "source_url": source_provenance.source_url,
        "source_extracted_at": source_provenance.extracted_at,
        "source_download_date": source_provenance.download_date,
        "source_publisher": source_provenance.publisher,
        "source_sha256": source_provenance.sha256,
        "cleaned_sha256": sha256_file(output_csv) if output_csv.is_file() else None,
        "cleaned_at": stats.cleaned_at,
        "internal_id_scheme": INTERNAL_ID_SCHEME,
        "notes": (
            "internal_project_id is a SARVSAKSHI surrogate hash, not an official MPLADS work ID. "
            "OpenCity MP-level files were not merged. District, vendor, coordinates, and "
            "expenditure were not added because they are absent from the primary extract."
        ),
        "stats": asdict(stats),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _extract_marked_section(text: str) -> str | None:
    start = text.find(CLEANED_SECTION_START)
    end = text.find(CLEANED_SECTION_END)
    if start < 0 or end < 0 or end <= start:
        return None
    return text[start : end + len(CLEANED_SECTION_END)]


def merge_cleaned_section(existing_text: str, new_body: str) -> str:
    """Replace or append the marked cleaned-dataset section."""
    block = f"{CLEANED_SECTION_START}\n{new_body.rstrip()}\n{CLEANED_SECTION_END}"
    start = existing_text.find(CLEANED_SECTION_START)
    end = existing_text.find(CLEANED_SECTION_END)
    if start >= 0 and end > start:
        return existing_text[:start] + block + existing_text[end + len(CLEANED_SECTION_END) :]
    return existing_text.rstrip() + "\n\n" + block + "\n"


def preserve_cleaned_section(existing_text: str, newly_rendered: str) -> str:
    block = _extract_marked_section(existing_text)
    if not block:
        return newly_rendered
    current = _extract_marked_section(newly_rendered)
    if current:
        return newly_rendered
    return newly_rendered.rstrip() + "\n\n" + block + "\n"


def _counts_md(counts: dict[str, int]) -> str:
    if not counts:
        return "(none)"
    lines = []
    for key, value in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{key}`: {value}")
    return "\n".join(lines)


def render_cleaning_report(
    stats: CleaningStats,
    *,
    source_provenance: Provenance,
    output_csv: Path,
) -> str:
    return "\n".join(
        [
            "# SARVSAKSHI data cleaning report",
            "",
            "Phase 2 — work-level cleaning of the **primary free MPLADS extract**.",
            "This report does not invent government fields, does not merge paid or MP-level files,",
            "and does not treat Investigation Priority as a legal fraud finding.",
            "",
            f"- Cleaned at (UTC): {stats.cleaned_at}",
            f"- Primary source: `{stats.source_filename}`",
            f"- Source URL: {source_provenance.source_url or '(not provided)'}",
            f"- Source extracted at: {source_provenance.extracted_at or '(not provided)'}",
            f"- Source download date: {source_provenance.download_date or '(not provided)'}",
            f"- Source SHA256: `{source_provenance.sha256}`",
            f"- Cleaned output: `{output_csv.as_posix()}`",
            f"- Internal identifier scheme: `{INTERNAL_ID_SCHEME}`",
            "",
            "## Primary dataset used",
            "",
            "The GitHub Vonter `india-mplads-works` CSV is the only work-level extract in `data/raw/`.",
            "It is a community flatten of MoSPI MPLADS HTML/XLS reports, not an official bulk dump.",
            "OpenCity 15th–17th Lok Sabha files are MP-level summaries and were **not** merged.",
            "Paid Dataful Completed Works / expenditure / vendor catalogs were not downloaded.",
            "",
            "## Row counts",
            "",
            f"- Raw rows: {stats.raw_row_count}",
            f"- Extra exact full-row duplicates in the source: {stats.exact_extra_duplicate_count}",
            f"- Rows collapsed by internal surrogate ID: {stats.collapsed_row_count}",
            f"- **Cleaned rows (unique internal_project_id): {stats.cleaned_row_count}**",
            f"- Andhra Pradesh rows in the raw extract: {stats.andhra_pradesh_raw_count}",
            f"- **Andhra Pradesh rows after cleaning: {stats.andhra_pradesh_cleaned_count}**",
            "",
            "## Observed STATUS values",
            "",
            "These are source values after whitespace normalisation. No new government status was added.",
            "",
            "Raw extract (including duplicate rows):",
            "",
            _counts_md(stats.raw_status_counts),
            "",
            "Cleaned extract (unique internal IDs):",
            "",
            _counts_md(stats.cleaned_status_counts),
            "",
            "## Internal lifecycle mapping",
            "",
            "System `lifecycle_stage` is an internal grouping of observed `STATUS` values.",
            "It is not an official MPLADS status list.",
            "",
            "| Observed STATUS | lifecycle_stage | Reason |",
            "| --- | --- | --- |",
            "| Unsanctioned | FUTURE | Recommended, not yet sanctioned |",
            "| Sanctioned | FUTURE | Sanctioned in source, not reported as started or completed |",
            "| Ongoing | ONGOING | Source reports work in progress |",
            "| Completed | COMPLETED | Source reports completion |",
            "| (blank / unrecognised) | UNKNOWN | Insufficient source value |",
            "",
            "Lifecycle counts on the cleaned extract:",
            "",
            _counts_md(stats.lifecycle_counts),
            "",
            "## Internal project identifier",
            "",
            f"`internal_project_id` is prefixed `{INTERNAL_ID_PREFIX}` and is not an official MPLADS ID.",
            "The source file has no unique work number. The surrogate is SHA-256 of canonicalised",
            f"available source fields (scheme `{INTERNAL_ID_SCHEME}`).",
            "Whitespace-only copies share an ID; distinct recorded fields keep distinct IDs.",
            "",
            "## Usable fields for later engines",
            "",
            "Assessed against this cleaned work-level extract only. OpenCity MP-level columns are out of scope.",
            "",
            "### Cost Intelligence — partial",
            "",
            "- Sufficient as a **recommended allocation** peer signal: `allocation_amount`, `state`, `category`, `work_description`, `constituency`.",
            "- **Not sufficient** for district-aware or expenditure-aware cost review: no district, no vendor, no utilised/spent amount, no SoR/material prices.",
            "- Amount unit is unspecified in the source column name; values look like whole rupees but that unit is not labelled in the file.",
            "",
            "### Time Intelligence — weak / partial",
            "",
            "- Available: `recommended_date`, `status`, `lifecycle_stage`.",
            "- **Not sufficient** for duration, slippage, or expected completion: no sanction date, start date, completion date, or milestone dates.",
            "- Observed recommended dates in this snapshot span 2023-04-26 to 2024-03-04 only.",
            "",
            "### Overlap detection — partial",
            "",
            "- Available: work text, allocation, recommended date, constituency, IDA, MP name, and place text (`city` / `ward` / `block` / `village`).",
            "- **Not sufficient** for GPS proximity: no latitude/longitude.",
            "- Place text is sparse (city/ward mostly empty). Many `WORK` values share a source prefix `NA - ` plus a generic title, so textual overlap will over-match without extra evidence.",
            "",
            "### Relationship Graph — partial MVP",
            "",
            "- Nodes possible from this extract: internal project, MP, IDA (agency), state, constituency, category, house.",
            "- Edge attributes possible: allocation amount, recommended date, status.",
            "- **No vendor node, no district node, no GPS edge.** IDA names often contain a place token; that is not treated as a district field.",
            "",
            "### Project Digital Passport — partial",
            "",
            "- Available plan/claim-like fields: description, category, state, constituency, MP, house, IDA, allocation, recommended date, status, IDA approval, place text.",
            "- **Missing for a full passport:** official work ID, district, vendor, expenditure, photos, documents, GPS, completion date, blueprint/BOQ.",
            "- Plan vs Claim vs Evidence cannot be separated beyond this single recommended-work snapshot.",
            "",
            "## Data quality and limitations",
            "",
            "- No official work ID exists in the source; `internal_project_id` is a surrogate only.",
            "- Snapshot coverage is recommended works from about 1 April 2023 to 4 March 2024, not a full MPLADS history.",
            "- Community flatten may already have dropped duplicates before this copy was acquired; this pipeline still collapses remaining identical canonical rows.",
            f"- Blank `STATUS` after cleaning: {stats.blank_status_cleaned_count}.",
            f"- Blank `constituency` after cleaning (source used the token `nan`): {stats.blank_constituency_cleaned_count}.",
            f"- Unparseable amounts after cleaning: {stats.amount_unparseable_count}.",
            f"- Unparseable recommended dates after cleaning: {stats.date_unparseable_count}.",
            "- `CITY` / `WARD` are empty for most rows; `BLOCK` / `VILLAGE` are empty for about a quarter of raw rows.",
            "- Many work titles start with `NA - `; that prefix is preserved because it is in the source text.",
            "- MP names retain honorifics (`Shri`, `Smt`, `Dr`, …); they are not split into given/family names.",
            "- IDA values keep the `_IDA` suffix after case normalisation; district is not parsed out of the agency string.",
            "- Nine raw allocation values are zero; zeros are kept as zero, not recoded as missing.",
            "- OpenCity files remain in `data/raw/` for later MP-level context. They are a different grain and were not joined.",
            "- No Coastal Andhra district list is chosen from this extract (no work-level district column).",
            "- This extract does not support live eSAKSHI, PFMS, or CAG-labelled fraud claims.",
            "",
            "## Next step",
            "",
            "Create the master SQLite schema and load this cleaned extract into `data/processed/sarvsakshi.db`,",
            "mapping `internal_project_id` to a clearly labelled internal key (not `unique_work_number` as an official ID).",
            "Do not start Cost/Time/Overlap engines until that load exists, and do not invent district or expenditure columns.",
            "",
        ]
    )


CLEANED_FIELD_ROWS = [
    ("internal_project_id", "string", "internal", "SARVSAKSHI surrogate hash (`internal:…`). Not an official MPLADS ID."),
    ("internal_id_kind", "string", "internal", "Always `internal_surrogate_hash`."),
    ("internal_id_scheme", "string", "internal", "Hash recipe version, currently `sarvsakshi_internal_work_v1`."),
    ("source_dataset", "string", "provenance", "Primary raw filename."),
    ("source_first_row_number", "integer", "provenance", "1-based data-row number of the kept source row."),
    ("source_duplicate_count", "integer", "provenance", "How many raw rows shared this internal ID."),
    ("source_mp_name", "string", "source", "Original `MP NAME`."),
    ("source_work", "string", "source", "Original `WORK`."),
    ("source_category", "string", "source", "Original `CATEGORY`."),
    ("source_state", "string", "source", "Original `STATE`."),
    ("source_constituency", "string", "source", "Original `CONSTITUENCY`."),
    ("source_ida", "string", "source", "Original `IDA`."),
    ("source_city", "string", "source", "Original `CITY`."),
    ("source_ward", "string", "source", "Original `WARD`."),
    ("source_block", "string", "source", "Original `BLOCK`."),
    ("source_village", "string", "source", "Original `VILLAGE`."),
    ("source_recommended_date", "string", "source", "Original `RECOMMENDED DATE`."),
    ("source_allocation_amount", "string", "source", "Original `ALLOCATION AMOUNT`."),
    ("source_ida_approval", "string", "source", "Original `IDA APPROVAL`."),
    ("source_status", "string", "source", "Original `STATUS`."),
    ("source_house", "string", "source", "Original `HOUSE`."),
    ("mp_name", "string", "normalized", "Whitespace/Unicode-normalised MP name. Honorifics kept."),
    ("work_description", "string", "normalized", "Whitespace/Unicode-normalised `WORK` text."),
    ("category", "string", "normalized", "Canonical observed category spelling."),
    ("state", "string", "normalized", "Whitespace-normalised state/UT name as recorded."),
    ("constituency", "string", "normalized", "Whitespace-normalised constituency; source `nan` becomes empty."),
    ("ida", "string", "normalized", "Whitespace-normalised implementing district authority; `_ida` suffix cased to `_IDA`."),
    ("city", "string", "normalized", "Whitespace-normalised city text from source. Often empty."),
    ("ward", "string", "normalized", "Whitespace-normalised ward text from source. Often empty."),
    ("block", "string", "normalized", "Whitespace-normalised block text from source."),
    ("village", "string", "normalized", "Whitespace-normalised village text from source."),
    ("recommended_date", "date", "normalized", "ISO `YYYY-MM-DD` from `RECOMMENDED DATE`."),
    ("allocation_amount", "integer", "normalized", "Numeric allocation as recorded. Unit unspecified in source."),
    ("ida_approval", "string", "normalized", "Canonical observed IDA approval spelling."),
    ("status", "string", "normalized", "Canonical observed STATUS. Blank if source blank. Not a new code list."),
    ("house", "string", "normalized", "Lok Sabha / Rajya Sabha as recorded."),
    ("lifecycle_stage", "string", "internal", "FUTURE / ONGOING / COMPLETED / UNKNOWN derived from observed STATUS only."),
]


def render_cleaned_dictionary_section() -> str:
    lines = [
        "## Cleaned work-level extract (`data/processed/mplads_works_cleaned.csv`)",
        "",
        "Primary source: `github_vonter_india-mplads-works_MPLADS.csv` only. OpenCity files are not in this table.",
        f"`internal_project_id` is an internal surrogate (`{INTERNAL_ID_PREFIX}…`), not an official MPLADS work ID.",
        "Original source cells are preserved in `source_*` columns. District, vendor, coordinates, and expenditure are absent and were not added.",
        "Full limitations: `DATA_CLEANING_REPORT.md`.",
        "",
        "| Field | Logical type | Kind | Meaning |",
        "| --- | --- | --- | --- |",
    ]
    for name, logical, kind, meaning in CLEANED_FIELD_ROWS:
        lines.append(f"| `{name}` | {logical} | {kind} | {meaning} |")
    lines.append("")
    return "\n".join(lines)


def render_cleaned_profiling_section(stats: CleaningStats | None = None) -> str:
    counts = ""
    if stats is not None:
        counts = "\n".join(
            [
                "",
                "### Cleaning run counts",
                "",
                f"- Raw rows: {stats.raw_row_count}",
                f"- Cleaned rows: {stats.cleaned_row_count}",
                f"- Andhra Pradesh cleaned rows: {stats.andhra_pradesh_cleaned_count}",
                f"- Extra exact source duplicates: {stats.exact_extra_duplicate_count}",
                "",
            ]
        )
    return "\n".join(
        [
            "## Work-level cleaning (Phase 2)",
            "",
            "The primary free work-level extract was cleaned without modifying `data/raw/` and without merging OpenCity MP-level files.",
            "See `DATA_CLEANING_REPORT.md` for data quality, limitations, lifecycle mapping, and engine-field sufficiency.",
            counts,
            "No Coastal Andhra district list is asserted (the work-level file has no District column).",
            "",
        ]
    )


def update_markdown_with_cleaned_section(path: Path, section_body: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(merge_cleaned_section(existing, section_body), encoding="utf-8")


def clean_primary_dataset(
    raw_path: Path | None = None,
    *,
    output_csv: Path | None = None,
    output_provenance: Path | None = None,
    cleaning_report_path: Path | None = None,
    dictionary_path: Path | None = None,
    profiling_path: Path | None = None,
    write_docs: bool = True,
) -> tuple[pd.DataFrame, CleaningStats]:
    raw_path = Path(raw_path) if raw_path is not None else DEFAULT_RAW_PATH
    output_csv = Path(output_csv) if output_csv is not None else DEFAULT_OUTPUT_CSV
    output_provenance = Path(output_provenance) if output_provenance is not None else DEFAULT_OUTPUT_PROVENANCE
    cleaning_report_path = (
        Path(cleaning_report_path) if cleaning_report_path is not None else DEFAULT_CLEANING_REPORT
    )
    dictionary_path = Path(dictionary_path) if dictionary_path is not None else DEFAULT_DICTIONARY_PATH
    profiling_path = Path(profiling_path) if profiling_path is not None else DEFAULT_PROFILING_PATH

    if not raw_path.is_file():
        raise FileNotFoundError(f"Primary MPLADS extract not found: {raw_path}")
    if raw_path.name != PRIMARY_WORKS_FILENAME:
        raise ValueError(
            f"Refusing to clean `{raw_path.name}`; primary source must be `{PRIMARY_WORKS_FILENAME}`."
        )

    loaded = load_tabular(raw_path)
    frame, _sheet, _header, _notes = loaded[0]
    cleaned, stats = clean_works_frame(frame)
    write_cleaned_csv(cleaned, output_csv)

    raw_dir = raw_path.parent
    provenance = build_provenance(raw_path, raw_dir)
    write_processed_provenance(
        output_provenance,
        source_provenance=provenance,
        output_csv=output_csv,
        stats=stats,
    )
    if write_docs:
        cleaning_report_path.write_text(
            render_cleaning_report(stats, source_provenance=provenance, output_csv=output_csv),
            encoding="utf-8",
        )
        update_markdown_with_cleaned_section(dictionary_path, render_cleaned_dictionary_section())
        update_markdown_with_cleaned_section(profiling_path, render_cleaned_profiling_section(stats))
    return cleaned, stats
