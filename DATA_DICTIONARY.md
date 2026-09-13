# DATA DICTIONARY

Built **only** from fields actually observed in `data/raw/` during profiling.
Likely meaning is a name heuristic, not an official MoSPI/eSAKSHI schema.
Do not treat absent fields as present.

- Profiled at (UTC): 2026-09-09T18:11:09+00:00
- Raw directory: `C:\Users\MAHENDRA JALLI\Documents\SIH_project\data\raw`

## `github_vonter_india-mplads-works_MPLADS.csv`

### Provenance
- Original filename: `github_vonter_india-mplads-works_MPLADS.csv`
- Relative path: `github_vonter_india-mplads-works_MPLADS.csv`
- Size (bytes): 15796263
- SHA256: `aa1d0b7c9c6bbe014a1af772a22ab3dc0a6eb24d043695060abaa0f94333e413`
- Filesystem mtime (UTC date): 2026-09-09
- Source URL: https://raw.githubusercontent.com/Vonter/india-mplads-works/main/csv/MPLADS.csv
- Extracted at: 2026-09-09
- Download date: 2026-09-09
- Publisher: Vonter GitHub dataset; underlying source identified as the MoSPI MPLADS site (http://164.100.68.116/mpladssbi/Default.aspx)
- Sidecar: C:/Users/MAHENDRA JALLI/Documents/SIH_project/data/raw/github_vonter_india-mplads-works_MPLADS.csv.provenance.json
- Notes: Public GitHub CSV compiled from official MPLADS HTML/XLS reports (semicolon-delimited). Not an official MoSPI bulk dump and not altered after download. Community flatten.py may have dropped duplicate rows at source-compile time; this acquisition did not drop, fill, or filter rows. Work-level fields include MP name, work, category, state, constituency, implementing district authority, recommended date, allocation amount, IDA approval, status, house.
- Missing provenance fields: (none)

- Rows observed: 60359
- Columns observed: 15

| Field (as in file) | Observed pandas dtype | Inferred logical type | Likely role | Likely meaning | Missing % |
| --- | --- | --- | --- | --- | ---: |
| `MP NAME` | str | string | mp | MP name as recorded | 0.00% |
| `WORK` | str | string | description | Work or project title/description | 0.00% |
| `CATEGORY` | str | string | work_type | Work type/category/sector as recorded | 0.00% |
| `STATE` | str | string | state | State / UT name as recorded in the extract | 0.00% |
| `CONSTITUENCY` | str | string | constituency | Parliamentary constituency as recorded | 0.01% |
| `IDA` | str | string | agency | Implementing or executing agency name | 0.00% |
| `CITY` | str | string | location | Place/location text (not necessarily GPS) | 77.72% |
| `WARD` | str | string | location | Place/location text (not necessarily GPS) | 78.01% |
| `BLOCK` | str | string | location | Place/location text (not necessarily GPS) | 23.47% |
| `VILLAGE` | str | string | location | Place/location text (not necessarily GPS) | 23.47% |
| `RECOMMENDED DATE` | str | date | date | Date-like field as recorded in the extract | 0.00% |
| `ALLOCATION AMOUNT` | str | integer | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `IDA APPROVAL` | str | string | other | Observed column; role not inferred from the name | 0.00% |
| `STATUS` | str | string | status | Reported work/project status | 1.34% |
| `HOUSE` | str | string | house | Lok Sabha / Rajya Sabha (or equivalent) as recorded | 0.00% |

## `opencity_mplads_15th_lok_sabha.csv`

### Provenance
- Original filename: `opencity_mplads_15th_lok_sabha.csv`
- Relative path: `opencity_mplads_15th_lok_sabha.csv`
- Size (bytes): 77719
- SHA256: `45ee72a31ec90a10a21b1c11dd02f9c80c6119876af4cbc19a8ae6132a91c7f5`
- Filesystem mtime (UTC date): 2026-09-09
- Source URL: https://data.opencity.in/dataset/0844e65b-76ff-422b-a213-2495aec592d9/resource/0b894524-3708-41ec-896e-7a5e8d15c2f3/download/cfa8c46b-1bb0-4d8a-b149-2d1d53ad0826.csv
- Extracted at: 2026-09-09
- Download date: 2026-09-09
- Publisher: OpenCity.in republication; catalog source cited as https://www.mplads.gov.in/mplads/AuthenticatedPages/Reports/Citizen/rptDetailsSummary.aspx (MoSPI MPLADS citizen report)
- Sidecar: C:/Users/MAHENDRA JALLI/Documents/SIH_project/data/raw/opencity_mplads_15th_lok_sabha.csv.provenance.json
- Notes: Original CSV bytes saved unmodified. Leading report-title rows (Textbox4 / MP WISE DETAILS...) are part of the source export and were not removed. This is MP-level fund-release/pending summary, not work-level recommended/completed works.
- Missing provenance fields: (none)

- Rows observed: 549
- Columns observed: 20

| Field (as in file) | Observed pandas dtype | Inferred logical type | Likely role | Likely meaning | Missing % |
| --- | --- | --- | --- | --- | ---: |
| `State` | str | string | state | State / UT name as recorded in the extract | 0.00% |
| `House` | str | integer | house | Lok Sabha / Rajya Sabha (or equivalent) as recorded | 0.00% |
| `Sno` | str | integer | work_id | Work identifier or serial present in the extract | 0.00% |
| `MPName` | str | string | mp | MP name as recorded | 0.00% |
| `Constituency` | str | string | constituency | Parliamentary constituency as recorded | 0.18% |
| `District` | str | string | district | District name as recorded in the extract | 0.00% |
| `TotalEntitlementAmount_crore` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.36% |
| `TotalGOIRelease_crore` | str | float | other | Observed column; role not inferred from the name | 0.18% |
| `ReleasePendingAmount_crore` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.55% |
| `UnSanctionBalance_crore` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `UnspentBalance_crore` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `LastInstNumber1` | str | integer | other | Observed column; role not inferred from the name | 0.55% |
| `LastInstYear` | str | string | other | Observed column; role not inferred from the name | 0.55% |
| `LastReleaseDate` | str | string | other | Observed column; role not inferred from the name | 0.55% |
| `LastRelAmount_crore` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `PendingInstallmentNumberAndYear` | str | string | other | Observed column; role not inferred from the name | 37.16% |
| `ReasonsforNotRel` | str | string | other | Observed column; role not inferred from the name | 98.18% |
| `ls_start_year` | str | date | date | Date-like field as recorded in the extract | 0.00% |
| `ls_end_year` | str | date | date | Date-like field as recorded in the extract | 0.00% |
| `lok_sabha` | str | integer | house | Lok Sabha / Rajya Sabha (or equivalent) as recorded | 0.00% |

## `opencity_mplads_16th_lok_sabha.csv`

### Provenance
- Original filename: `opencity_mplads_16th_lok_sabha.csv`
- Relative path: `opencity_mplads_16th_lok_sabha.csv`
- Size (bytes): 83829
- SHA256: `75af7fc192aab5fe1a498408e6a471f77062429992d3e3d78047b57de603c8e0`
- Filesystem mtime (UTC date): 2026-09-09
- Source URL: https://data.opencity.in/dataset/0844e65b-76ff-422b-a213-2495aec592d9/resource/57baaa96-04ca-4328-86bc-17b455af1024/download/d6a40c40-f0bb-44d7-b697-fd4d74ffefd3.csv
- Extracted at: 2026-09-09
- Download date: 2026-09-09
- Publisher: OpenCity.in republication; catalog source cited as https://www.mplads.gov.in/mplads/AuthenticatedPages/Reports/Citizen/rptDetailsSummary.aspx (MoSPI MPLADS citizen report)
- Sidecar: C:/Users/MAHENDRA JALLI/Documents/SIH_project/data/raw/opencity_mplads_16th_lok_sabha.csv.provenance.json
- Notes: Original CSV bytes saved unmodified. Leading report-title rows are part of the source export and were not removed. MP-level fund-release/pending summary, not work-level records. Catalog page: https://data.opencity.in/dataset/lok-sabha-mp-local-area-development-funds-details/resource/57baaa96-04ca-4328-86bc-17b455af1024
- Missing provenance fields: (none)

- Rows observed: 569
- Columns observed: 20

| Field (as in file) | Observed pandas dtype | Inferred logical type | Likely role | Likely meaning | Missing % |
| --- | --- | --- | --- | --- | ---: |
| `State` | str | string | state | State / UT name as recorded in the extract | 0.00% |
| `House` | str | integer | house | Lok Sabha / Rajya Sabha (or equivalent) as recorded | 0.00% |
| `Sno` | str | integer | work_id | Work identifier or serial present in the extract | 0.00% |
| `MPName` | str | string | mp | MP name as recorded | 0.00% |
| `Constituency` | str | string | constituency | Parliamentary constituency as recorded | 0.00% |
| `District` | str | string | district | District name as recorded in the extract | 0.00% |
| `TotalEntitlementAmount_crore` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.18% |
| `TotalGOIRelease_crore` | str | float | other | Observed column; role not inferred from the name | 0.18% |
| `ReleasePendingAmount_crore` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.18% |
| `UnSanctionBalance_crore` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `UnspentBalance_crore` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `LastInstNumber1` | str | integer | other | Observed column; role not inferred from the name | 0.18% |
| `LastInstYear` | str | string | other | Observed column; role not inferred from the name | 0.18% |
| `LastReleaseDate` | str | string | other | Observed column; role not inferred from the name | 0.18% |
| `LastRelAmount_crore` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `PendingInstallmentNumberAndYear` | str | string | other | Observed column; role not inferred from the name | 65.91% |
| `ReasonsforNotRel` | str | string | other | Observed column; role not inferred from the name | 80.14% |
| `ls_start_year` | str | date | date | Date-like field as recorded in the extract | 0.00% |
| `ls_end_year` | str | date | date | Date-like field as recorded in the extract | 0.00% |
| `lok_sabha` | str | integer | house | Lok Sabha / Rajya Sabha (or equivalent) as recorded | 0.00% |

## `opencity_mplads_17th_lok_sabha.csv`

### Provenance
- Original filename: `opencity_mplads_17th_lok_sabha.csv`
- Relative path: `opencity_mplads_17th_lok_sabha.csv`
- Size (bytes): 48895
- SHA256: `a14011eae26dc1c60d4a16ddb092af5e0735ed915368b6afe8fdae084da9bb28`
- Filesystem mtime (UTC date): 2026-09-09
- Source URL: https://data.opencity.in/dataset/0844e65b-76ff-422b-a213-2495aec592d9/resource/e4524ed7-6c9b-41a5-ad0a-003358fdabca/download/4d2bc892-cd12-4f17-befa-aa7efb6e210b.csv
- Extracted at: 2026-09-09
- Download date: 2026-09-09
- Publisher: OpenCity.in republication; catalog source cited as https://www.mplads.gov.in/mplads/AuthenticatedPages/Reports/Citizen/rptDetailsSummary.aspx (MoSPI MPLADS citizen report)
- Sidecar: C:/Users/MAHENDRA JALLI/Documents/SIH_project/data/raw/opencity_mplads_17th_lok_sabha.csv.provenance.json
- Notes: Original CSV bytes saved unmodified. MP-level spending/utilisation summary (entitlement, GoI release, recommended cost, sanctioned cost, expenditure). Not work-level recommended/completed works. Catalog page: https://data.opencity.in/dataset/lok-sabha-mp-local-area-development-funds-details/resource/e4524ed7-6c9b-41a5-ad0a-003358fdabca
- Missing provenance fields: (none)

- Rows observed: 557
- Columns observed: 11

| Field (as in file) | Observed pandas dtype | Inferred logical type | Likely role | Likely meaning | Missing % |
| --- | --- | --- | --- | --- | ---: |
| `Sl No` | str | integer | work_id | Work identifier or serial present in the extract | 0.00% |
| `MP Name` | str | string | mp | MP name as recorded | 0.00% |
| `Constituency` | str | string | constituency | Parliamentary constituency as recorded | 0.00% |
| `Entitlement` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `FundReceivedGOI` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `AmountAvailable` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `WorksRecommCost` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `WSCost` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `ActualExpenditureIncurred` | str | float | amount | Monetary value (role/unit inferred from the column name only) | 0.00% |
| `UtilizationOverRelease` | str | float | other | Observed column; role not inferred from the name | 0.00% |
| `UnspentBalance` | str | float | other | Observed column; role not inferred from the name | 0.00% |

<!-- BEGIN CLEANED DATASET -->
## Cleaned work-level extract (`data/processed/mplads_works_cleaned.csv`)

Primary source: `github_vonter_india-mplads-works_MPLADS.csv` only. OpenCity files are not in this table.
`internal_project_id` is an internal surrogate (`internal:…`), not an official MPLADS work ID.
Original source cells are preserved in `source_*` columns. District, vendor, coordinates, and expenditure are absent and were not added.
Full limitations: `DATA_CLEANING_REPORT.md`.

| Field | Logical type | Kind | Meaning |
| --- | --- | --- | --- |
| `internal_project_id` | string | internal | SARVSAKSHI surrogate hash (`internal:…`). Not an official MPLADS ID. |
| `internal_id_kind` | string | internal | Always `internal_surrogate_hash`. |
| `internal_id_scheme` | string | internal | Hash recipe version, currently `sarvsakshi_internal_work_v1`. |
| `source_dataset` | string | provenance | Primary raw filename. |
| `source_first_row_number` | integer | provenance | 1-based data-row number of the kept source row. |
| `source_duplicate_count` | integer | provenance | How many raw rows shared this internal ID. |
| `source_mp_name` | string | source | Original `MP NAME`. |
| `source_work` | string | source | Original `WORK`. |
| `source_category` | string | source | Original `CATEGORY`. |
| `source_state` | string | source | Original `STATE`. |
| `source_constituency` | string | source | Original `CONSTITUENCY`. |
| `source_ida` | string | source | Original `IDA`. |
| `source_city` | string | source | Original `CITY`. |
| `source_ward` | string | source | Original `WARD`. |
| `source_block` | string | source | Original `BLOCK`. |
| `source_village` | string | source | Original `VILLAGE`. |
| `source_recommended_date` | string | source | Original `RECOMMENDED DATE`. |
| `source_allocation_amount` | string | source | Original `ALLOCATION AMOUNT`. |
| `source_ida_approval` | string | source | Original `IDA APPROVAL`. |
| `source_status` | string | source | Original `STATUS`. |
| `source_house` | string | source | Original `HOUSE`. |
| `mp_name` | string | normalized | Whitespace/Unicode-normalised MP name. Honorifics kept. |
| `work_description` | string | normalized | Whitespace/Unicode-normalised `WORK` text. |
| `category` | string | normalized | Canonical observed category spelling. |
| `state` | string | normalized | Whitespace-normalised state/UT name as recorded. |
| `constituency` | string | normalized | Whitespace-normalised constituency; source `nan` becomes empty. |
| `ida` | string | normalized | Whitespace-normalised implementing district authority; `_ida` suffix cased to `_IDA`. |
| `city` | string | normalized | Whitespace-normalised city text from source. Often empty. |
| `ward` | string | normalized | Whitespace-normalised ward text from source. Often empty. |
| `block` | string | normalized | Whitespace-normalised block text from source. |
| `village` | string | normalized | Whitespace-normalised village text from source. |
| `recommended_date` | date | normalized | ISO `YYYY-MM-DD` from `RECOMMENDED DATE`. |
| `allocation_amount` | integer | normalized | Numeric allocation as recorded. Unit unspecified in source. |
| `ida_approval` | string | normalized | Canonical observed IDA approval spelling. |
| `status` | string | normalized | Canonical observed STATUS. Blank if source blank. Not a new code list. |
| `house` | string | normalized | Lok Sabha / Rajya Sabha as recorded. |
| `lifecycle_stage` | string | internal | FUTURE / ONGOING / COMPLETED / UNKNOWN derived from observed STATUS only. |
<!-- END CLEANED DATASET -->
