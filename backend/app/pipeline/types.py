from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Provenance:
    original_filename: str
    relative_path: str
    size_bytes: int
    sha256: str
    file_mtime_iso: str | None = None
    source_url: str | None = None
    extracted_at: str | None = None
    download_date: str | None = None
    publisher: str | None = None
    notes: str | None = None
    sidecar_path: str | None = None
    missing_fields: list[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return not self.missing_fields


@dataclass
class ColumnProfile:
    name: str
    pandas_dtype: str
    inferred_logical_type: str
    likely_role: str
    likely_meaning: str
    meaning_basis: str
    missing_count: int
    missing_pct: float
    n_unique: int
    sample_values: list[str]
    date_parseable_count: int | None = None
    date_parseable_pct: float | None = None
    date_min: str | None = None
    date_max: str | None = None
    date_invalid_non_null_count: int | None = None
    date_parse_convention: str | None = None
    numeric_parseable_count: int | None = None
    numeric_parseable_pct: float | None = None
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_negative_count: int | None = None
    numeric_zero_count: int | None = None
    suspected_unit: str | None = None


@dataclass
class DistrictQuality:
    name: str
    record_count: int
    missing_description_pct: float | None = None
    missing_amount_pct: float | None = None
    missing_date_pct: float | None = None
    missing_agency_pct: float | None = None
    missing_status_pct: float | None = None
    missing_location_pct: float | None = None


@dataclass
class AndhraSlice:
    state_column: str | None
    district_column: str | None
    total_ap_records: int
    ap_state_value_variants: list[tuple[str, int]]
    districts: list[DistrictQuality]
    coastal_region_fields_observed: list[str]
    coastal_correspondence_note: str
    unmatched_state_sample: list[tuple[str, int]]


@dataclass
class IntelligenceSupport:
    cost_fields: list[str]
    time_fields: list[str]
    overlap_fields: list[str]
    relationship_graph_fields: list[str]
    evidence_passport_fields: list[str]
    notes: list[str]


@dataclass
class DatasetProfile:
    dataset_id: str
    relative_path: str
    sheet_name: str | None
    n_rows: int
    n_columns: int
    columns: list[str]
    column_profiles: list[ColumnProfile]
    duplicate_extra_row_count: int
    duplicate_group_count: int
    likely_id_columns: list[str]
    duplicate_id_extra_counts: dict[str, int]
    state_value_counts: list[tuple[str, int]]
    district_value_counts: list[tuple[str, int]]
    work_description_fields: list[str]
    agency_fields: list[str]
    vendor_fields: list[str]
    status_fields: list[str]
    location_fields: list[str]
    date_fields: list[str]
    monetary_fields: list[str]
    andhra: AndhraSlice | None
    intelligence: IntelligenceSupport
    load_notes: list[str]
    provenance: Provenance
    header_row_index: int


@dataclass
class JoinKeyPair:
    left_dataset: str
    right_dataset: str
    left_column: str
    right_column: str
    match_kind: str
    likely_role: str
    note: str


@dataclass
class DatasetInventory:
    profiled_at: str
    raw_dir: str
    skipped_names: list[str]
    datasets: list[DatasetProfile]
    empty_reason: str | None = None
    combined_andhra: AndhraSlice | None = None
    combined_intelligence: IntelligenceSupport | None = None
    join_keys: list[JoinKeyPair] = field(default_factory=list)
    recommended_works_dataset_id: str | None = None
