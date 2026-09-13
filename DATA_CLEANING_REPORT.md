# SARVSAKSHI data cleaning report

Phase 2 — work-level cleaning of the **primary free MPLADS extract**.
This report does not invent government fields, does not merge paid or MP-level files,
and does not treat Investigation Priority as a legal fraud finding.

- Cleaned at (UTC): 2026-09-09T18:35:42+00:00
- Primary source: `github_vonter_india-mplads-works_MPLADS.csv`
- Source URL: https://raw.githubusercontent.com/Vonter/india-mplads-works/main/csv/MPLADS.csv
- Source extracted at: 2026-09-09
- Source download date: 2026-09-09
- Source SHA256: `aa1d0b7c9c6bbe014a1af772a22ab3dc0a6eb24d043695060abaa0f94333e413`
- Cleaned output: `C:/Users/MAHENDRA JALLI/Documents/SIH_project/data/processed/mplads_works_cleaned.csv`
- Internal identifier scheme: `sarvsakshi_internal_work_v1`

## Primary dataset used

The GitHub Vonter `india-mplads-works` CSV is the only work-level extract in `data/raw/`.
It is a community flatten of MoSPI MPLADS HTML/XLS reports, not an official bulk dump.
OpenCity 15th–17th Lok Sabha files are MP-level summaries and were **not** merged.
Paid Dataful Completed Works / expenditure / vendor catalogs were not downloaded.

## Row counts

- Raw rows: 60359
- Extra exact full-row duplicates in the source: 4221
- Rows collapsed by internal surrogate ID: 4221
- **Cleaned rows (unique internal_project_id): 56138**
- Andhra Pradesh rows in the raw extract: 3944
- **Andhra Pradesh rows after cleaning: 3640**

## Observed STATUS values

These are source values after whitespace normalisation. No new government status was added.

Raw extract (including duplicate rows):

- `Unsanctioned`: 50888
- `Sanctioned`: 6528
- `Completed`: 1503
- `(blank)`: 811
- `Ongoing`: 629

Cleaned extract (unique internal IDs):

- `Unsanctioned`: 46667
- `Sanctioned`: 6528
- `Completed`: 1503
- `(blank)`: 811
- `Ongoing`: 629

## Internal lifecycle mapping

System `lifecycle_stage` is an internal grouping of observed `STATUS` values.
It is not an official MPLADS status list.

| Observed STATUS | lifecycle_stage | Reason |
| --- | --- | --- |
| Unsanctioned | FUTURE | Recommended, not yet sanctioned |
| Sanctioned | FUTURE | Sanctioned in source, not reported as started or completed |
| Ongoing | ONGOING | Source reports work in progress |
| Completed | COMPLETED | Source reports completion |
| (blank / unrecognised) | UNKNOWN | Insufficient source value |

Lifecycle counts on the cleaned extract:

- `FUTURE`: 53195
- `COMPLETED`: 1503
- `UNKNOWN`: 811
- `ONGOING`: 629

## Internal project identifier

`internal_project_id` is prefixed `internal:` and is not an official MPLADS ID.
The source file has no unique work number. The surrogate is SHA-256 of canonicalised
available source fields (scheme `sarvsakshi_internal_work_v1`).
Whitespace-only copies share an ID; distinct recorded fields keep distinct IDs.

## Usable fields for later engines

Assessed against this cleaned work-level extract only. OpenCity MP-level columns are out of scope.

### Cost Intelligence — partial

- Sufficient as a **recommended allocation** peer signal: `allocation_amount`, `state`, `category`, `work_description`, `constituency`.
- **Not sufficient** for district-aware or expenditure-aware cost review: no district, no vendor, no utilised/spent amount, no SoR/material prices.
- Amount unit is unspecified in the source column name; values look like whole rupees but that unit is not labelled in the file.

### Time Intelligence — weak / partial

- Available: `recommended_date`, `status`, `lifecycle_stage`.
- **Not sufficient** for duration, slippage, or expected completion: no sanction date, start date, completion date, or milestone dates.
- Observed recommended dates in this snapshot span 2023-04-26 to 2024-03-04 only.

### Overlap detection — partial

- Available: work text, allocation, recommended date, constituency, IDA, MP name, and place text (`city` / `ward` / `block` / `village`).
- **Not sufficient** for GPS proximity: no latitude/longitude.
- Place text is sparse (city/ward mostly empty). Many `WORK` values share a source prefix `NA - ` plus a generic title, so textual overlap will over-match without extra evidence.

### Relationship Graph — partial MVP

- Nodes possible from this extract: internal project, MP, IDA (agency), state, constituency, category, house.
- Edge attributes possible: allocation amount, recommended date, status.
- **No vendor node, no district node, no GPS edge.** IDA names often contain a place token; that is not treated as a district field.

### Project Digital Passport — partial

- Available plan/claim-like fields: description, category, state, constituency, MP, house, IDA, allocation, recommended date, status, IDA approval, place text.
- **Missing for a full passport:** official work ID, district, vendor, expenditure, photos, documents, GPS, completion date, blueprint/BOQ.
- Plan vs Claim vs Evidence cannot be separated beyond this single recommended-work snapshot.

## Data quality and limitations

- No official work ID exists in the source; `internal_project_id` is a surrogate only.
- Snapshot coverage is recommended works from about 1 April 2023 to 4 March 2024, not a full MPLADS history.
- Community flatten may already have dropped duplicates before this copy was acquired; this pipeline still collapses remaining identical canonical rows.
- Blank `STATUS` after cleaning: 811.
- Blank `constituency` after cleaning (source used the token `nan`): 5.
- Unparseable amounts after cleaning: 0.
- Unparseable recommended dates after cleaning: 0.
- `CITY` / `WARD` are empty for most rows; `BLOCK` / `VILLAGE` are empty for about a quarter of raw rows.
- Many work titles start with `NA - `; that prefix is preserved because it is in the source text.
- MP names retain honorifics (`Shri`, `Smt`, `Dr`, …); they are not split into given/family names.
- IDA values keep the `_IDA` suffix after case normalisation; district is not parsed out of the agency string.
- Nine raw allocation values are zero; zeros are kept as zero, not recoded as missing.
- OpenCity files remain in `data/raw/` for later MP-level context. They are a different grain and were not joined.
- No Coastal Andhra district list is chosen from this extract (no work-level district column).
- This extract does not support live eSAKSHI, PFMS, or CAG-labelled fraud claims.

## Next step

Create the master SQLite schema and load this cleaned extract into `data/processed/sarvsakshi.db`,
mapping `internal_project_id` to a clearly labelled internal key (not `unique_work_number` as an official ID).
Do not start Cost/Time/Overlap engines until that load exists, and do not invent district or expenditure columns.
