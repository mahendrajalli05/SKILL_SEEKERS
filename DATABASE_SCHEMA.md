# SARVSAKSHI database schema

SQLite file: `data/processed/sarvsakshi.db`

This schema is based on the cleaned work-level extract
`data/processed/mplads_works_cleaned.csv`. It does not invent district,
vendor, GPS, expenditure, sanction date, completion date, or official
MPLADS work IDs. `internal_project_id` is an internal SARVSAKSHI key only.

Loaded now:

- `dataset_snapshot` — one provenance row for the cleaned extract
- `project` — one row per cleaned work

Empty by design (extensible, no fabricated values):

- `implementing_agency`, `document`, `photo`, `photo_details`, `claim`,
  `plan_artifact`, `guideline_rule`, `guideline_snippet`, `evidence_object`,
  `evidence_fact`, `overlap_link`, `graph_edge`, `fusion_score`,
  `officer_decision`, `audit_event`, `copilot_turn`, `citizen_report`

Rebuild from the cleaned CSV (does not modify `data/raw/`):

```powershell
cd backend
python -m app.pipeline.db_load_run
```

## `dataset_snapshot`

Provenance for one ingest of the cleaned extract. Not a government work table.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite surrogate |
| `source_url` | TEXT | URL of the primary raw extract |
| `extracted_at` | DATETIME | Extract/download date from the sidecar, as UTC midnight when date-only |
| `download_date` | TEXT | Download date string from the sidecar |
| `publisher` | TEXT | Publisher note from the sidecar |
| `file_sha256` | TEXT | SHA-256 of the cleaned CSV |
| `original_filename` | TEXT | `mplads_works_cleaned.csv` |
| `source_filename` | TEXT | Primary raw filename |
| `source_sha256` | TEXT | SHA-256 of the primary raw file |
| `internal_id_scheme` | TEXT | Hash recipe, currently `sarvsakshi_internal_work_v1` |
| `cleaned_at` | DATETIME | When the cleaned CSV was produced |
| `record_count` | INTEGER | Cleaned CSV row count at load time |
| `notes` | TEXT | Sidecar notes (internal ID is not official; absent fields were not added) |
| `created_at` / `updated_at` | DATETIME | Row timestamps |

## `project`

One cleaned MPLADS work. Integer `id` is a SQLite primary key for future
foreign keys. It is not an official work number.

### Identity

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite row id |
| `internal_project_id` | TEXT UNIQUE NOT NULL | SARVSAKSHI surrogate (`internal:` + SHA-256). Not an official MPLADS ID |
| `internal_id_kind` | TEXT NOT NULL | Always `internal_surrogate_hash` in this load |
| `internal_id_scheme` | TEXT NOT NULL | Currently `sarvsakshi_internal_work_v1` |

### Row provenance

| Field | Type | Meaning |
| --- | --- | --- |
| `source_dataset` | TEXT | Primary raw filename |
| `source_first_row_number` | INTEGER | 1-based data-row number of the kept source row |
| `source_duplicate_count` | INTEGER | How many raw rows shared this internal ID |
| `snapshot_id` | INTEGER FK | `dataset_snapshot.id` |

### Original source cells (`source_*`)

Exact cells from the raw extract, preserved as text.

| Field | Source column |
| --- | --- |
| `source_mp_name` | `MP NAME` |
| `source_work` | `WORK` |
| `source_category` | `CATEGORY` |
| `source_state` | `STATE` |
| `source_constituency` | `CONSTITUENCY` |
| `source_ida` | `IDA` |
| `source_city` | `CITY` |
| `source_ward` | `WARD` |
| `source_block` | `BLOCK` |
| `source_village` | `VILLAGE` |
| `source_recommended_date` | `RECOMMENDED DATE` |
| `source_allocation_amount` | `ALLOCATION AMOUNT` |
| `source_ida_approval` | `IDA APPROVAL` |
| `source_status` | `STATUS` |
| `source_house` | `HOUSE` |

### Normalised observed fields

Whitespace/Unicode-normalised copies of the same source columns. Blank source
values stay blank. No district, vendor, GPS, or expenditure is derived.

| Field | Type | Meaning |
| --- | --- | --- |
| `mp_name` | TEXT | Normalised MP name; honorifics kept |
| `work_description` | TEXT | Normalised `WORK` text |
| `category` | TEXT | Canonical observed category spelling |
| `state` | TEXT | Normalised state/UT name |
| `constituency` | TEXT | Normalised constituency; source `nan` is empty |
| `ida` | TEXT | Normalised implementing district authority |
| `city` / `ward` / `block` / `village` | TEXT | Place text from source, often empty. Not GPS |
| `recommended_date` | DATE | ISO date from `RECOMMENDED DATE` |
| `allocation_amount` | INTEGER | Numeric allocation as recorded. Unit unspecified in source |
| `ida_approval` | TEXT | Canonical observed IDA approval spelling |
| `status` | TEXT | Canonical observed STATUS. Blank if source blank |
| `house` | TEXT | Lok Sabha / Rajya Sabha as recorded |
| `lifecycle_stage` | TEXT NOT NULL | Internal grouping: FUTURE / ONGOING / COMPLETED / UNKNOWN from STATUS only |

### Governance / reserved

| Field | Type | Meaning |
| --- | --- | --- |
| `agency_id` | INTEGER FK NULL | Reserved for a future agency table. Not populated from this extract |
| `is_synthetic` | BOOLEAN NOT NULL | Real loaded works are `0`. Test placeholders must be labelled |
| `synthetic_label` | TEXT | Required when `is_synthetic` is true |
| `created_at` / `updated_at` | DATETIME | Row timestamps |

### Indexes

| Index | Column | Unique |
| --- | --- | --- |
| `ix_project_internal_project_id` | `internal_project_id` | yes |
| `ix_project_state` | `state` | no |
| `ix_project_constituency` | `constituency` | no |
| `ix_project_category` | `category` | no |
| `ix_project_status` | `status` | no |
| `ix_project_mp_name` | `mp_name` | no |
| `ix_project_recommended_date` | `recommended_date` | no |

## Empty extensible tables

These exist so later evidence, risk, graph, citizen, milestone-adjacent claim,
and review data can be stored without inventing values now. All stay empty
after the cleaned-work load.

| Table | Future use |
| --- | --- |
| `implementing_agency` | Canonical agency rows. IDA text is on `project.ida` today |
| `document` / `plan_artifact` | Uploaded documents and blueprint/BOQ extracts |
| `photo` / `photo_details` | Photos, EXIF, perceptual hash |
| `claim` | Reported progress / amount used / completion statement (milestone-adjacent) |
| `guideline_rule` / `guideline_snippet` | Deterministic MPLADS rule engine |
| `evidence_object` / `evidence_fact` | Explainable engine findings (Evidence Object V1; see below) |
| `overlap_link` | Pairwise overlap scores |
| `graph_edge` | Relationship-graph edges |
| `fusion_score` | Investigation Priority and Evidence Confidence only (never a legal fraud probability) |
| `officer_decision` / `audit_event` | Human review and audit |
| `copilot_turn` | Grounded copilot Q&A log |
| `citizen_report` | Jan-Sakshi supporting reports |

## `evidence_object` / `evidence_fact` (Evidence Object V1)

Existing tables are reused. No duplicate evidence tables were added.
`init_db()` adds missing V1 columns on existing databases without dropping rows.

### `evidence_object`

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite surrogate; `evidence_fact.evidence_id` still references this |
| `evidence_id` | TEXT UNIQUE | Deterministic public ID (`ev:{engine}:{project}:{signal}:{mode}:{digest}`) |
| `project_id` | INTEGER FK | Subject work |
| `engine` / `engine_name` | TEXT | Engine that wrote the object (`cost`, `time`, `overlap`, `compliance`, …) |
| `engine_version` | TEXT | Frozen engine version string |
| `evidence_type` / `signal_type` | TEXT | Canonical signal (e.g. `allocation_cost_anomaly`) |
| `status` | TEXT | `consistent` / `mismatch` / `inconclusive` / `not_assessable` |
| `disposition` | TEXT | `WHY_FLAGGED` / `WHY_NOT_FLAGGED` / `INCONCLUSIVE` / `NOT_ASSESSABLE` |
| `severity` | TEXT | `info` / `watch` / `attention` |
| `finding` | TEXT | Derived finding (not a legal conclusion) |
| `summary` / `explanation` | TEXT | Full why-flagged / why-not / inconclusive text |
| `score` | FLOAT NULL | Engine score 0–100 when produced |
| `confidence` | FLOAT | Evidence-layer confidence 0.0–1.0 (engine 0–100 mapped / 100) |
| `source_type` | TEXT | Primary source class (`mplads_project_record`, `hybrid_enrichment`, …) |
| `source_ids_json` | TEXT | JSON list of preserved source identifiers |
| `data_mode` | TEXT | `REAL` / `HYBRID` / `SYNTHETIC` |
| `provenance_json` | TEXT | Required provenance payload; must not be dropped |
| `comparables_json` | TEXT | Optional comparable/match payload |
| `rule_ids_json` / `guideline_refs_json` | TEXT | Compliance rule IDs and guideline references |

### `evidence_fact`

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite surrogate |
| `evidence_id` | INTEGER FK | `evidence_object.id` (not the public `evidence_id` string) |
| `key` | TEXT | Fact key |
| `value` | TEXT | Stored value (JSON when structured) |
| `source` | TEXT | Required source/provenance for this fact |
| `fact_kind` | TEXT | `OBSERVATION` or `DERIVED` |
| `statement` | TEXT | Optional human-readable observation (e.g. actual allocation) |

## Fields not present (not invented)

The cleaned extract has no official work ID, district, vendor/contractor,
latitude/longitude, utilised/spent amount, sanction date, start date, or
completion date. Those columns are not on `project`.

## External contextual data (Real Contextual Data Enrichment V1)

Separate from `project`. Created by `init_db()`; not populated by the cleaned
CSV load. Do not merge these values into original MPLADS rows.

### `external_source`

Registry copy of `data/external/sources/registry.json`. Source facts are not
hard-coded in application callers.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite surrogate |
| `source_id` | TEXT UNIQUE | Registry identifier |
| `source_name` / `publisher` / `source_type` | TEXT | Attributable source metadata |
| `url` | TEXT NULL | Public URL or identifier |
| `retrieval_date` / `dataset_version` | TEXT NULL | Snapshot date / published version |
| `geographic_level` / `unit` | TEXT NULL | Native grain and unit |
| `update_frequency` / `license_note` / `transformation_notes` | TEXT NULL | Usage notes |
| `limitations_json` | TEXT NULL | JSON list of limitations |
| `active` / `requires_credential` | INTEGER | 1/0 flags |

### `external_context_snapshot`

Cached retrieval of one source snapshot. Avoids fetching remote sources on
every project page load.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite surrogate |
| `source_id` | TEXT UNIQUE | Registry identifier |
| `retrieval_at` | DATETIME NULL | When the snapshot was cached |
| `source_version` | TEXT NULL | Dataset/version string |
| `file_sha256` | TEXT NULL | Snapshot hash |
| `payload_json` | TEXT NULL | Normalized payload (not a filesystem path) |
| `processing_version` | TEXT NULL | `contextual-data-enrichment-v1` |
| `notes` | TEXT NULL | Cache notes |

### `external_context_observation`

One contextual indicator for a project. Absence is stored as UNAVAILABLE /
INCONCLUSIVE, never as fabricated zero.

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | INTEGER PK | SQLite surrogate |
| `project_id` | INTEGER FK NULL | Subject work; null for non-persisted new-project assessment |
| `internal_project_id` | TEXT | Surrogate key |
| `indicator` | TEXT | e.g. `state_population`, `reference_unit_rate` |
| `status` | TEXT | `AVAILABLE` / `UNAVAILABLE` / `INCONCLUSIVE` |
| `value` / `unit` | TEXT NULL | Observed value; null when unavailable |
| `geographic_level` / `geo_key` | TEXT NULL | Matching grain and key actually used |
| `source_id` / `retrieval_date` | TEXT NULL | Provenance |
| `reference_year` | INTEGER NULL | External dataset year |
| `data_mode` | TEXT | `REAL` / `HYBRID` / `SYNTHETIC` |
| `confidence` / `quality` | TEXT NULL | Quality controls |
| `context_kind` | TEXT | `OBSERVED_EXTERNAL_INDICATOR` / `DERIVED_CONTEXT` / `PROJECT_SPECIFIC_FACT` |
| `provenance_json` | TEXT NULL | Full observation payload |
| `failure_code` | TEXT NULL | Explicit failure, never a silent substitute |
| `assessment_kind` | TEXT NULL | `NEW_PROJECT_ASSESSMENT` when applicable |

Contextual findings are also written as Evidence Object V1 rows
(`engine=context`). They are not fused into Investigation Priority.
