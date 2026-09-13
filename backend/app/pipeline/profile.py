from __future__ import annotations

import re
import warnings
from collections import Counter

import pandas as pd

from app.pipeline.classify import likely_meaning, likely_role, normalize_name, suspected_amount_unit
from app.pipeline.types import (
    AndhraSlice,
    ColumnProfile,
    DatasetProfile,
    DistrictQuality,
    IntelligenceSupport,
    JoinKeyPair,
    Provenance,
)

MISSING_TOKENS = {"", "nan", "none", "null", "na", "n/a", "nil", "-", "--", ".", "nat"}
AP_EXACT = {
    "andhra pradesh",
    "andhra pradesh state",
    "andhrapradesh",
    "andhra",
    "ap",
    "a p",
    "a.p",
    "a.p.",
}
AP_REJECT_SUBSTRINGS = ("andaman", "nicobar", "pradesh ut", "arunachal")
COASTAL_REGION_NAME_HINTS = ("coastal", "coastal andhra", "andhra coastal", "coast")


def _is_missing(value: object) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return True
    text = str(value).strip().lower()
    return text in MISSING_TOKENS


def _as_text(value: object) -> str:
    if _is_missing(value):
        return ""
    return str(value).strip()


def _sample_values(series: pd.Series, limit: int = 8) -> list[str]:
    seen: list[str] = []
    for value in series:
        text = _as_text(value)
        if not text or text in seen:
            continue
        seen.append(text[:120])
        if len(seen) >= limit:
            break
    return seen


def _parse_money(value: object) -> float | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    text = text.replace(",", "")
    text = re.sub(r"(?i)\b(rs\.?|inr|₹)\b", "", text).strip()
    text = text.replace("₹", "").strip()
    if _is_missing(text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _date_parse_stats(series: pd.Series) -> tuple[pd.Series, str]:
    non_null = series.loc[~series.map(_is_missing)]
    if non_null.empty:
        return pd.to_datetime(series, errors="coerce"), "none"
    dayfirst = pd.to_datetime(non_null, errors="coerce", dayfirst=True)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        monthfirst = pd.to_datetime(non_null, errors="coerce", dayfirst=False)
    if int(dayfirst.notna().sum()) >= int(monthfirst.notna().sum()):
        parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
        return parsed, "dayfirst"
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=False)
    return parsed, "monthfirst"


def _logical_type(series: pd.Series, role: str) -> str:
    non_null = [_as_text(v) for v in series if not _is_missing(v)]
    if not non_null:
        return "empty"
    if role == "date":
        parsed, _ = _date_parse_stats(series)
        rate = float(parsed.notna().sum()) / max(len(non_null), 1)
        return "date" if rate >= 0.5 else "string"
    money = [_parse_money(v) for v in non_null]
    money_ok = sum(1 for v in money if v is not None)
    if role == "amount" or money_ok / len(non_null) >= 0.8:
        ints = all(v is not None and float(v).is_integer() for v in money if v is not None)
        return "integer" if ints and money_ok == len(non_null) else "float"
    boolish = {"yes", "no", "true", "false", "y", "n", "0", "1"}
    if all(v.lower() in boolish for v in non_null):
        return "boolean"
    return "string"


def _value_counts(series: pd.Series | None, limit: int | None = None) -> list[tuple[str, int]]:
    if series is None:
        return []
    counter: Counter[str] = Counter()
    for value in series:
        text = _as_text(value)
        if not text:
            continue
        counter[text] += 1
    items = counter.most_common(limit)
    return [(name, int(count)) for name, count in items]


def _columns_for_roles(profiles: list[ColumnProfile], roles: set[str]) -> list[str]:
    return [p.name for p in profiles if p.likely_role in roles]


def is_andhra_pradesh_state(value: object) -> bool:
    text = _as_text(value).lower()
    text = re.sub(r"\s+", " ", text)
    text = text.replace(".", "")
    if any(part in text for part in AP_REJECT_SUBSTRINGS):
        return False
    return text in AP_EXACT


def _profile_column(name: str, series: pd.Series) -> ColumnProfile:
    role = likely_role(name)
    n = len(series)
    missing = int(series.map(_is_missing).sum())
    non_null_n = n - missing
    unique_non_null = series.loc[~series.map(_is_missing)].nunique(dropna=True)
    profile = ColumnProfile(
        name=name,
        pandas_dtype=str(series.dtype),
        inferred_logical_type=_logical_type(series, role),
        likely_role=role,
        likely_meaning=likely_meaning(name, role),
        meaning_basis="column name heuristic; not an official data dictionary from the publisher",
        missing_count=missing,
        missing_pct=round((missing / n) * 100, 2) if n else 0.0,
        n_unique=int(unique_non_null),
        sample_values=_sample_values(series),
    )
    if role == "date" or profile.inferred_logical_type == "date":
        parsed, convention = _date_parse_stats(series)
        parseable = int(parsed.notna().sum())
        profile.date_parseable_count = parseable
        profile.date_parseable_pct = round((parseable / non_null_n) * 100, 2) if non_null_n else None
        profile.date_invalid_non_null_count = max(non_null_n - parseable, 0)
        profile.date_parse_convention = convention
        valid = parsed.dropna()
        if not valid.empty:
            profile.date_min = valid.min().date().isoformat()
            profile.date_max = valid.max().date().isoformat()
    if role == "amount" or profile.inferred_logical_type in {"integer", "float"}:
        parsed_nums = series.map(_parse_money)
        numeric_ok = parsed_nums.notna()
        ok_n = int(numeric_ok.sum())
        profile.numeric_parseable_count = ok_n
        profile.numeric_parseable_pct = round((ok_n / non_null_n) * 100, 2) if non_null_n else None
        vals = parsed_nums.dropna()
        if not vals.empty:
            profile.numeric_min = float(vals.min())
            profile.numeric_max = float(vals.max())
            profile.numeric_negative_count = int((vals < 0).sum())
            profile.numeric_zero_count = int((vals == 0).sum())
        profile.suspected_unit = suspected_amount_unit(name)
    return profile


def _duplicate_stats(frame: pd.DataFrame) -> tuple[int, int]:
    if frame.empty:
        return 0, 0
    dup_mask = frame.duplicated(keep="first")
    extra = int(dup_mask.sum())
    if extra == 0:
        return 0, 0
    groups = int(frame[frame.duplicated(keep=False)].drop_duplicates().shape[0])
    return extra, groups


def _id_duplicate_counts(frame: pd.DataFrame, id_columns: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for col in id_columns:
        series = frame[col]
        filled = series.loc[~series.map(_is_missing)]
        extra = int(filled.duplicated(keep="first").sum())
        counts[col] = extra
    return counts


def _missing_pct(frame: pd.DataFrame, columns: list[str]) -> float | None:
    if frame.empty or not columns:
        return None
    present = [c for c in columns if c in frame.columns]
    if not present:
        return None
    missing_any = frame[present].apply(lambda col: col.map(_is_missing)).all(axis=1)
    return round(float(missing_any.mean()) * 100, 2)


def _andhra_slice(frame: pd.DataFrame, profiles: list[ColumnProfile]) -> AndhraSlice | None:
    state_cols = _columns_for_roles(profiles, {"state"})
    district_cols = _columns_for_roles(profiles, {"district"})
    if not state_cols:
        return AndhraSlice(
            state_column=None,
            district_column=district_cols[0] if district_cols else None,
            total_ap_records=0,
            ap_state_value_variants=[],
            districts=[],
            coastal_region_fields_observed=[],
            coastal_correspondence_note=(
                "No state column was observed, so Andhra Pradesh rows cannot be counted from this file. "
                "No Coastal Andhra district list is asserted."
            ),
            unmatched_state_sample=[],
        )
    state_col = state_cols[0]
    ap_mask = frame[state_col].map(is_andhra_pradesh_state)
    ap_frame = frame.loc[ap_mask]
    variants = _value_counts(ap_frame[state_col] if not ap_frame.empty else None)
    unmatched = _value_counts(frame.loc[~ap_mask, state_col], limit=20)
    district_col = district_cols[0] if district_cols else None
    districts: list[DistrictQuality] = []
    if district_col and not ap_frame.empty:
        desc_cols = _columns_for_roles(profiles, {"description"})
        amount_cols = _columns_for_roles(profiles, {"amount"})
        date_cols = _columns_for_roles(profiles, {"date"})
        agency_cols = _columns_for_roles(profiles, {"agency"})
        status_cols = _columns_for_roles(profiles, {"status"})
        location_cols = _columns_for_roles(profiles, {"location", "latitude", "longitude"})
        for name, count in _value_counts(ap_frame[district_col]):
            sub = ap_frame.loc[ap_frame[district_col].map(_as_text) == name]
            districts.append(
                DistrictQuality(
                    name=name,
                    record_count=count,
                    missing_description_pct=_missing_pct(sub, desc_cols),
                    missing_amount_pct=_missing_pct(sub, amount_cols),
                    missing_date_pct=_missing_pct(sub, date_cols),
                    missing_agency_pct=_missing_pct(sub, agency_cols),
                    missing_status_pct=_missing_pct(sub, status_cols),
                    missing_location_pct=_missing_pct(sub, location_cols),
                )
            )
    coastal_fields = [
        p.name
        for p in profiles
        if any(hint in p.name.lower() for hint in COASTAL_REGION_NAME_HINTS)
        or (p.likely_role == "other" and "region" in p.name.lower())
    ]
    coastal_values_hint = False
    for col in frame.columns:
        if "region" in str(col).lower() or "coast" in str(col).lower():
            coastal_fields.append(str(col))
            sample = " ".join(_sample_values(frame[col], limit=20)).lower()
            if "coastal" in sample:
                coastal_values_hint = True
    coastal_fields = list(dict.fromkeys(coastal_fields))
    if coastal_fields and coastal_values_hint:
        note = (
            "A region/coast-related column is present. Values are listed in the column profile. "
            "This report does not convert those values into a final Coastal Andhra pilot district list. "
            "No final Coastal Andhra district list is asserted."
        )
    elif coastal_fields:
        note = (
            "A region/coast-related column name was observed, but this report does not assert a "
            "Coastal Andhra district list from it. No final Coastal Andhra district list is asserted."
        )
    else:
        note = (
            "No coastal-region field was observed. Andhra Pradesh district names are listed with "
            "counts only. Correspondence to a Coastal Andhra pilot cannot be decided from this extract. "
            "No final Coastal Andhra district list is asserted."
        )
    return AndhraSlice(
        state_column=state_col,
        district_column=district_col,
        total_ap_records=int(ap_mask.sum()),
        ap_state_value_variants=variants,
        districts=districts,
        coastal_region_fields_observed=coastal_fields,
        coastal_correspondence_note=note,
        unmatched_state_sample=unmatched,
    )


def _intelligence(profiles: list[ColumnProfile]) -> IntelligenceSupport:
    by_role = {p.likely_role: [] for p in profiles}
    for p in profiles:
        by_role.setdefault(p.likely_role, []).append(p.name)

    def take(*roles: str) -> list[str]:
        names: list[str] = []
        for role in roles:
            names.extend(by_role.get(role, []))
        return list(dict.fromkeys(names))

    cost = take("amount", "district", "state", "work_type", "description")
    time = take("date", "status")
    overlap = take(
        "description",
        "location",
        "latitude",
        "longitude",
        "amount",
        "date",
        "work_id",
        "district",
        "constituency",
        "agency",
        "mp",
    )
    graph = take(
        "work_id",
        "agency",
        "vendor",
        "district",
        "state",
        "work_type",
        "amount",
        "date",
        "description",
        "constituency",
        "mp",
        "house",
    )
    passport = take(
        "work_id",
        "description",
        "work_type",
        "state",
        "district",
        "constituency",
        "mp",
        "house",
        "agency",
        "vendor",
        "amount",
        "date",
        "status",
        "image",
        "location",
        "latitude",
        "longitude",
    )
    notes: list[str] = []
    if not take("amount"):
        notes.append("No monetary column was inferred; Cost Intelligence cannot be supported from this file yet.")
    if not take("date"):
        notes.append("No date column was inferred; Time Intelligence cannot be supported from this file yet.")
    if not take("latitude", "longitude"):
        notes.append("No latitude/longitude columns were inferred; GPS proximity overlap is unavailable from this file.")
    if not take("agency"):
        notes.append("No implementing-agency column was inferred; agency nodes in the relationship graph are unavailable from this file.")
    if not take("vendor"):
        notes.append("No vendor/contractor column was inferred; vendor nodes in the relationship graph are unavailable from this file.")
    if not take("image"):
        notes.append("No image/photo column was inferred; photo evidence is not present in this extract.")
    return IntelligenceSupport(
        cost_fields=cost,
        time_fields=time,
        overlap_fields=overlap,
        relationship_graph_fields=graph,
        evidence_passport_fields=passport,
        notes=notes,
    )


def profile_frame(
    frame: pd.DataFrame,
    *,
    relative_path: str,
    sheet_name: str | None,
    header_row_index: int,
    load_notes: list[str],
    provenance: Provenance,
) -> DatasetProfile:
    columns = [str(c) for c in frame.columns]
    profiles = [_profile_column(name, frame[name]) for name in columns]
    extra_rows, extra_groups = _duplicate_stats(frame)
    id_cols = _columns_for_roles(profiles, {"work_id"})
    state_cols = _columns_for_roles(profiles, {"state"})
    district_cols = _columns_for_roles(profiles, {"district"})
    dataset_id = relative_path if sheet_name is None else f"{relative_path}::{sheet_name}"
    return DatasetProfile(
        dataset_id=dataset_id,
        relative_path=relative_path,
        sheet_name=sheet_name,
        n_rows=int(len(frame)),
        n_columns=int(len(columns)),
        columns=columns,
        column_profiles=profiles,
        duplicate_extra_row_count=extra_rows,
        duplicate_group_count=extra_groups,
        likely_id_columns=id_cols,
        duplicate_id_extra_counts=_id_duplicate_counts(frame, id_cols),
        state_value_counts=_value_counts(frame[state_cols[0]] if state_cols else None, limit=50),
        district_value_counts=_value_counts(frame[district_cols[0]] if district_cols else None, limit=80),
        work_description_fields=_columns_for_roles(profiles, {"description"}),
        agency_fields=_columns_for_roles(profiles, {"agency"}),
        vendor_fields=_columns_for_roles(profiles, {"vendor"}),
        status_fields=_columns_for_roles(profiles, {"status"}),
        location_fields=_columns_for_roles(profiles, {"location", "latitude", "longitude"}),
        date_fields=_columns_for_roles(profiles, {"date"}),
        monetary_fields=_columns_for_roles(profiles, {"amount"}),
        andhra=_andhra_slice(frame, profiles),
        intelligence=_intelligence(profiles),
        load_notes=load_notes,
        provenance=provenance,
        header_row_index=header_row_index,
    )


def combine_andhra(datasets: list[DatasetProfile]) -> AndhraSlice | None:
    slices = [d.andhra for d in datasets if d.andhra is not None]
    if not slices:
        return None
    district_counts: Counter[str] = Counter()
    variants: Counter[str] = Counter()
    coastal_fields: list[str] = []
    total = 0
    state_cols = []
    district_cols = []
    for item in slices:
        total += item.total_ap_records
        if item.state_column:
            state_cols.append(item.state_column)
        if item.district_column:
            district_cols.append(item.district_column)
        for name, count in item.ap_state_value_variants:
            variants[name] += count
        for district in item.districts:
            district_counts[district.name] += district.record_count
        coastal_fields.extend(item.coastal_region_fields_observed)
    districts = [
        DistrictQuality(name=name, record_count=count) for name, count in district_counts.most_common()
    ]
    coastal_fields = list(dict.fromkeys(coastal_fields))
    return AndhraSlice(
        state_column=state_cols[0] if state_cols else None,
        district_column=district_cols[0] if district_cols else None,
        total_ap_records=total,
        ap_state_value_variants=list(variants.most_common()),
        districts=districts,
        coastal_region_fields_observed=coastal_fields,
        coastal_correspondence_note=(
            "Combined Andhra Pradesh district counts across profiled extracts. "
            "Files may have different grain (work-level vs MP-level) and are not merged. "
            "No final Coastal Andhra district list is asserted."
        ),
        unmatched_state_sample=[],
    )


def combine_intelligence(datasets: list[DatasetProfile]) -> IntelligenceSupport:
    cost: list[str] = []
    time: list[str] = []
    overlap: list[str] = []
    graph: list[str] = []
    passport: list[str] = []
    notes: list[str] = []
    for dataset in datasets:
        intel = dataset.intelligence
        cost.extend(intel.cost_fields)
        time.extend(intel.time_fields)
        overlap.extend(intel.overlap_fields)
        graph.extend(intel.relationship_graph_fields)
        passport.extend(intel.evidence_passport_fields)
        notes.extend(intel.notes)
    if not datasets:
        notes.append("No extracts were profiled, so intelligence field support cannot be assessed.")
    return IntelligenceSupport(
        cost_fields=list(dict.fromkeys(cost)),
        time_fields=list(dict.fromkeys(time)),
        overlap_fields=list(dict.fromkeys(overlap)),
        relationship_graph_fields=list(dict.fromkeys(graph)),
        evidence_passport_fields=list(dict.fromkeys(passport)),
        notes=list(dict.fromkeys(notes)),
    )


JOIN_ROLES = {
    "work_id",
    "state",
    "district",
    "constituency",
    "mp",
    "agency",
    "vendor",
    "description",
    "house",
}

RECOMMENDED_HINTS = ("recommended", "mplads-works", "india-mplads-works")


def identify_recommended_works(datasets: list[DatasetProfile]) -> DatasetProfile | None:
    for dataset in datasets:
        blob = " ".join(
            [
                dataset.relative_path.lower(),
                dataset.dataset_id.lower(),
                (dataset.provenance.notes or "").lower(),
                (dataset.provenance.original_filename or "").lower(),
            ]
        )
        if any(hint in blob for hint in RECOMMENDED_HINTS):
            return dataset
    return None


def compare_join_keys(left: DatasetProfile, right: DatasetProfile) -> list[JoinKeyPair]:
    """Observed column-name/role overlaps only. Does not merge or match values."""
    pairs: list[JoinKeyPair] = []
    seen: set[tuple[str, str]] = set()
    left_by_norm = {normalize_name(c.name): c for c in left.column_profiles}
    right_by_norm = {normalize_name(c.name): c for c in right.column_profiles}

    for norm, left_col in left_by_norm.items():
        right_col = right_by_norm.get(norm)
        if right_col is None:
            continue
        key = (left_col.name, right_col.name)
        if key in seen:
            continue
        seen.add(key)
        role = left_col.likely_role if left_col.likely_role == right_col.likely_role else f"{left_col.likely_role}/{right_col.likely_role}"
        pairs.append(
            JoinKeyPair(
                left_dataset=left.dataset_id,
                right_dataset=right.dataset_id,
                left_column=left_col.name,
                right_column=right_col.name,
                match_kind="normalized_column_name",
                likely_role=role,
                note="Same normalized column name. Values are not assumed to match; files are not merged.",
            )
        )

    left_by_role: dict[str, list[ColumnProfile]] = {}
    right_by_role: dict[str, list[ColumnProfile]] = {}
    for col in left.column_profiles:
        if col.likely_role in JOIN_ROLES:
            left_by_role.setdefault(col.likely_role, []).append(col)
    for col in right.column_profiles:
        if col.likely_role in JOIN_ROLES:
            right_by_role.setdefault(col.likely_role, []).append(col)

    for role in JOIN_ROLES:
        for left_col in left_by_role.get(role, []):
            for right_col in right_by_role.get(role, []):
                key = (left_col.name, right_col.name)
                if key in seen:
                    continue
                seen.add(key)
                pairs.append(
                    JoinKeyPair(
                        left_dataset=left.dataset_id,
                        right_dataset=right.dataset_id,
                        left_column=left_col.name,
                        right_column=right_col.name,
                        match_kind="likely_role",
                        likely_role=role,
                        note="Same inferred role from column names. Values are not assumed to match; files are not merged.",
                    )
                )
    return pairs


def recommended_works_join_keys(datasets: list[DatasetProfile]) -> tuple[str | None, list[JoinKeyPair]]:
    recommended = identify_recommended_works(datasets)
    if recommended is None:
        return None, []
    pairs: list[JoinKeyPair] = []
    for dataset in datasets:
        if dataset.dataset_id == recommended.dataset_id:
            continue
        pairs.extend(compare_join_keys(recommended, dataset))
    return recommended.dataset_id, pairs
