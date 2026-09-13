from __future__ import annotations

from app.pipeline.types import AndhraSlice, ColumnProfile, DatasetInventory, DatasetProfile, IntelligenceSupport, Provenance

COASTAL_UNDECIDED = (
    "No final Coastal Andhra district list is asserted from these extracts. "
    "Report observed Andhra Pradesh districts and let the team decide the pilot set."
)


def _pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}%"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _join(items: list[str]) -> str:
    return ", ".join(items) if items else "(none observed)"


def _provenance_md(prov: Provenance) -> str:
    missing = ", ".join(prov.missing_fields) if prov.missing_fields else "(none)"
    return "\n".join(
        [
            f"- Original filename: `{prov.original_filename}`",
            f"- Relative path: `{prov.relative_path}`",
            f"- Size (bytes): {prov.size_bytes}",
            f"- SHA256: `{prov.sha256}`",
            f"- Filesystem mtime (UTC date): {prov.file_mtime_iso or '(unavailable)'}",
            f"- Source URL: {prov.source_url or '(not provided)'}",
            f"- Extracted at: {prov.extracted_at or '(not provided)'}",
            f"- Download date: {prov.download_date or '(not provided)'}",
            f"- Publisher: {prov.publisher or '(not provided)'}",
            f"- Sidecar: {prov.sidecar_path or '(none)'}",
            f"- Notes: {prov.notes or '(none)'}",
            f"- Missing provenance fields: {missing}",
        ]
    )


def _column_table(columns: list[ColumnProfile]) -> str:
    lines = [
        "| Column | Pandas dtype | Logical type | Likely role | Missing n | Missing % | Unique (non-null) |",
        "| --- | --- | --- | --- | ---: | ---: | ---: |",
    ]
    for col in columns:
        lines.append(
            f"| `{col.name}` | {col.pandas_dtype} | {col.inferred_logical_type} | "
            f"{col.likely_role} | {col.missing_count} | {col.missing_pct:.2f}% | {col.n_unique} |"
        )
    return "\n".join(lines)


def _column_details(col: ColumnProfile) -> str:
    lines = [
        f"#### `{col.name}`",
        "",
        f"- Likely meaning: {col.likely_meaning}",
        f"- Meaning basis: {col.meaning_basis}",
        f"- Sample values (observed, truncated): {col.sample_values or '(none)'}",
    ]
    if col.date_parseable_count is not None:
        lines.append(
            f"- Date parseable: {col.date_parseable_count} ({_pct(col.date_parseable_pct)}); "
            f"invalid non-null: {col.date_invalid_non_null_count}; "
            f"convention tried: {col.date_parse_convention}; "
            f"min={col.date_min or 'n/a'}; max={col.date_max or 'n/a'}"
        )
    if col.numeric_parseable_count is not None:
        lines.append(
            f"- Numeric parseable: {col.numeric_parseable_count} ({_pct(col.numeric_parseable_pct)}); "
            f"min={col.numeric_min}; max={col.numeric_max}; "
            f"negatives={col.numeric_negative_count}; zeros={col.numeric_zero_count}; "
            f"suspected unit={col.suspected_unit or 'n/a'}"
        )
    return "\n".join(lines)


def _andhra_md(andhra: AndhraSlice | None) -> str:
    if andhra is None:
        return "Andhra Pradesh slice was not computed (no datasets)."
    lines = [
        f"- State column used: `{andhra.state_column}`" if andhra.state_column else "- State column used: (none observed)",
        f"- District column used: `{andhra.district_column}`" if andhra.district_column else "- District column used: (none observed)",
        f"- Total Andhra Pradesh records (name-match on state values): {andhra.total_ap_records}",
        f"- AP state-value variants observed: {andhra.ap_state_value_variants or '(none)'}",
        f"- Coastal/region fields observed: {_join(andhra.coastal_region_fields_observed)}",
        f"- Coastal correspondence: {andhra.coastal_correspondence_note}",
        f"- {COASTAL_UNDECIDED}",
        "",
        "| Andhra Pradesh district (as recorded) | Records | Missing description % | Missing amount % | Missing date % | Missing agency % | Missing status % | Missing location % |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    if not andhra.districts:
        lines.append("| (none observed) | 0 | n/a | n/a | n/a | n/a | n/a | n/a |")
    for district in andhra.districts:
        lines.append(
            f"| {district.name} | {district.record_count} | {_pct(district.missing_description_pct)} | "
            f"{_pct(district.missing_amount_pct)} | {_pct(district.missing_date_pct)} | "
            f"{_pct(district.missing_agency_pct)} | {_pct(district.missing_status_pct)} | "
            f"{_pct(district.missing_location_pct)} |"
        )
    if andhra.unmatched_state_sample:
        lines.extend(["", "Unmatched (non-AP) state values (top):", ""])
        for name, count in andhra.unmatched_state_sample[:25]:
            lines.append(f"- {name}: {count}")
    return "\n".join(lines)


def _join_keys_md(inventory: DatasetInventory) -> str:
    rec = inventory.recommended_works_dataset_id
    lines = [
        "## Join keys with Recommended Works",
        "",
        "Observed column-name and role overlaps only. Files are not merged and values are not assumed to match.",
        f"- Recommended Works dataset used for comparison: `{rec}`" if rec else "- Recommended Works dataset used for comparison: (none identified from filenames/notes)",
    ]
    if not rec:
        lines.append("- No Recommended Works extract was identified among profiled files, so pairwise join keys were not computed.")
        return "\n".join(lines)
    if not inventory.join_keys:
        lines.append("- No overlapping column names or join-relevant roles were observed against other profiled files.")
        return "\n".join(lines)
    lines.extend(
        [
            "",
            "| Other dataset | Recommended Works column | Other column | Match kind | Likely role | Note |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for pair in inventory.join_keys:
        lines.append(
            f"| `{pair.right_dataset}` | `{pair.left_column}` | `{pair.right_column}` | "
            f"{pair.match_kind} | {pair.likely_role} | {pair.note} |"
        )
    return "\n".join(lines)


def _intelligence_md(intel: IntelligenceSupport | None) -> str:
    if intel is None:
        return "Intelligence field mapping was not computed."
    lines = [
        f"- Cost Intelligence candidate fields: {_join(intel.cost_fields)}",
        f"- Time Intelligence candidate fields: {_join(intel.time_fields)}",
        f"- Overlap / duplicate-detection candidate fields: {_join(intel.overlap_fields)}",
        f"- Relationship Graph candidate fields: {_join(intel.relationship_graph_fields)}",
        f"- Evidence / Project Digital Passport candidate fields: {_join(intel.evidence_passport_fields)}",
    ]
    for note in intel.notes:
        lines.append(f"- Note: {note}")
    return "\n".join(lines)


def _dataset_section(dataset: DatasetProfile) -> str:
    parts = [
        f"## Dataset `{dataset.dataset_id}`",
        "",
        "### Provenance",
        _provenance_md(dataset.provenance),
        "",
        "### Shape",
        f"- Rows: {dataset.n_rows}",
        f"- Columns: {dataset.n_columns}",
        f"- Header row index (0-based): {dataset.header_row_index}",
        f"- Sheet: {dataset.sheet_name or '(n/a — not a multi-sheet workbook, or single default)'}",
        f"- Load notes: {dataset.load_notes or '(none)'}",
        "",
        "### Columns",
        _column_table(dataset.column_profiles),
        "",
        "### Column details",
        "",
        "\n\n".join(_column_details(c) for c in dataset.column_profiles) if dataset.column_profiles else "(no columns)",
        "",
        "### Duplicates",
        f"- Extra full-row duplicates (beyond the first copy): {dataset.duplicate_extra_row_count}",
        f"- Duplicate groups: {dataset.duplicate_group_count}",
        f"- Likely ID columns: {_join(dataset.likely_id_columns)}",
        f"- Extra duplicates on likely ID columns: {dataset.duplicate_id_extra_counts or '{}'}",
        "",
        "### Observed values of interest",
        f"- State values (top): {dataset.state_value_counts or '(no state column inferred)'}",
        f"- District values (top): {dataset.district_value_counts or '(no district column inferred)'}",
        f"- Project/work description fields: {_join(dataset.work_description_fields)}",
        f"- Implementing agency fields: {_join(dataset.agency_fields)}",
        f"- Vendor/contractor fields: {_join(dataset.vendor_fields)}",
        f"- Status fields: {_join(dataset.status_fields)}",
        f"- Latitude/longitude/location fields: {_join(dataset.location_fields)}",
        f"- Date fields: {_join(dataset.date_fields)}",
        f"- Monetary fields: {_join(dataset.monetary_fields)}",
        "",
        "### Andhra Pradesh in this file",
        _andhra_md(dataset.andhra),
        "",
        "### Intelligence field support (this file)",
        _intelligence_md(dataset.intelligence),
        "",
    ]
    return "\n".join(parts)


def render_profiling_report(inventory: DatasetInventory) -> str:
    header = [
        "# SARVSAKSHI data profiling report",
        "",
        "Phase 2 — raw extract inspection only. This document records **observed** files and fields.",
        "It does not invent missing values, does not declare legal fraud, and does not freeze a Coastal Andhra district list.",
        "",
        f"- Profiled at (UTC): {inventory.profiled_at}",
        f"- Raw directory: `{inventory.raw_dir}`",
        f"- Tabular datasets profiled: {len(inventory.datasets)}",
        f"- Skipped names: {inventory.skipped_names or '(none)'}",
        "",
    ]
    if inventory.empty_reason:
        header.extend(
            [
                "## Inventory result",
                "",
                inventory.empty_reason,
                "",
                "No government fields were observed. The data dictionary contains no invented columns.",
                "",
            ]
        )
    body = [_dataset_section(dataset) for dataset in inventory.datasets]
    combined = [
        "## Combined Andhra Pradesh view",
        "",
        _andhra_md(inventory.combined_andhra),
        "",
        "## Combined intelligence field support",
        "",
        _intelligence_md(inventory.combined_intelligence),
        "",
        _join_keys_md(inventory),
        "",
        "## Coastal Andhra decision",
        "",
        COASTAL_UNDECIDED,
        "",
        "D014 remains: initial pilot is Coastal Andhra Pradesh **subject to actual data availability**.",
        "",
    ]
    return "\n".join(header + body + combined).rstrip() + "\n"


def render_data_dictionary(inventory: DatasetInventory) -> str:
    lines = [
        "# DATA DICTIONARY",
        "",
        "Built **only** from fields actually observed in `data/raw/` during profiling.",
        "Likely meaning is a name heuristic, not an official MoSPI/eSAKSHI schema.",
        "Do not treat absent fields as present.",
        "",
        f"- Profiled at (UTC): {inventory.profiled_at}",
        f"- Raw directory: `{inventory.raw_dir}`",
        "",
    ]
    if not inventory.datasets:
        lines.extend(
            [
                "## Observed fields",
                "",
                "None. No tabular extracts were present.",
                "",
            ]
        )
        return "\n".join(lines)
    for dataset in inventory.datasets:
        lines.extend(
            [
                f"## `{dataset.dataset_id}`",
                "",
                "### Provenance",
                _provenance_md(dataset.provenance),
                "",
                f"- Rows observed: {dataset.n_rows}",
                f"- Columns observed: {dataset.n_columns}",
                "",
                "| Field (as in file) | Observed pandas dtype | Inferred logical type | Likely role | Likely meaning | Missing % |",
                "| --- | --- | --- | --- | --- | ---: |",
            ]
        )
        for col in dataset.column_profiles:
            meaning = col.likely_meaning.replace("|", "/")
            lines.append(
                f"| `{col.name}` | {col.pandas_dtype} | {col.inferred_logical_type} | "
                f"{col.likely_role} | {meaning} | {col.missing_pct:.2f}% |"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
