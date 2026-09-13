# SARVSAKSHI data profiling report

Phase 2 — raw extract inspection only. This document records **observed** files and fields.
It does not invent missing values, does not declare legal fraud, and does not freeze a Coastal Andhra district list.

- Profiled at (UTC): 2026-09-09T18:11:09+00:00
- Raw directory: `C:\Users\MAHENDRA JALLI\Documents\SIH_project\data\raw`
- Tabular datasets profiled: 4
- Skipped names: ['.gitkeep', 'github_vonter_india-mplads-works_MPLADS.csv.provenance.json', 'opencity_mplads_15th_lok_sabha.csv.provenance.json', 'opencity_mplads_16th_lok_sabha.csv.provenance.json', 'opencity_mplads_17th_lok_sabha.csv.provenance.json']

## Dataset `github_vonter_india-mplads-works_MPLADS.csv`

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

### Shape
- Rows: 60359
- Columns: 15
- Header row index (0-based): 0
- Sheet: (n/a — not a multi-sheet workbook, or single default)
- Load notes: ["delimiter detected as ';'"]

### Columns
| Column | Pandas dtype | Logical type | Likely role | Missing n | Missing % | Unique (non-null) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `MP NAME` | str | string | mp | 0 | 0.00% | 633 |
| `WORK` | str | string | description | 0 | 0.00% | 20735 |
| `CATEGORY` | str | string | work_type | 0 | 0.00% | 4 |
| `STATE` | str | string | state | 0 | 0.00% | 33 |
| `CONSTITUENCY` | str | string | constituency | 5 | 0.01% | 456 |
| `IDA` | str | string | agency | 0 | 0.00% | 699 |
| `CITY` | str | string | location | 46910 | 77.72% | 2140 |
| `WARD` | str | string | location | 47085 | 78.01% | 4666 |
| `BLOCK` | str | string | location | 14169 | 23.47% | 5965 |
| `VILLAGE` | str | string | location | 14165 | 23.47% | 29881 |
| `RECOMMENDED DATE` | str | date | date | 0 | 0.00% | 280 |
| `ALLOCATION AMOUNT` | str | integer | amount | 0 | 0.00% | 3391 |
| `IDA APPROVAL` | str | string | other | 0 | 0.00% | 3 |
| `STATUS` | str | string | status | 811 | 1.34% | 4 |
| `HOUSE` | str | string | house | 0 | 0.00% | 2 |

### Column details

#### `MP NAME`

- Likely meaning: MP name as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Manoj Rajoria', 'Mr Gopal Jee Thakur', 'Pradyut Bordoloi', 'Shri Bhartruhari Mahtab', 'Shivkumar Chanabasappa Udasi', 'Shri Abdul Khaleque', 'Gaddam Ranjith Reddy', 'Dr Sukanta Majumdar']

#### `WORK`

- Likely meaning: Work or project title/description
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['NA - Installing community drinking water plants', 'NA - Street lights', 'NA - Construction of roads, link roads, pathways or any other road with or without drainage system', 'NA - Setting up public non-conventional energy plants', 'NA - Construction of boundary walls of existing public and community buildings', 'NA - Construction of community centers and community halls', 'NA - Construction of buildings for community cultural activities', 'NA - Construction of additional rooms and halls in the existing public and community building']

#### `CATEGORY`

- Likely meaning: Work type/category/sector as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Normal/Others', 'Repair and Renovation', 'Trust and Society', 'Bar and Associations']

#### `STATE`

- Likely meaning: State / UT name as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Rajasthan', 'Bihar', 'Assam', 'Odisha', 'Karnataka', 'Telangana', 'West Bengal', 'Jharkhand']

#### `CONSTITUENCY`

- Likely meaning: Parliamentary constituency as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['KARAULI-DHOLPUR(SC)', 'DARBHANGA', 'NOWGONG', 'CUTTACK', 'HAVERI', 'BARPETA', 'CHELVELLA', 'BALURGHAT']

#### `IDA`

- Likely meaning: Implementing or executing agency name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['DISTRICT COLLECTOR DHOLPUR_IDA', 'DISTRICT MAGISTRATE DARBANGA_IDA', 'DEPUTY COMMISSIONER NOWGONG_IDA', 'DISTRICT COLLECTOR CUTTACK_IDA', 'DEPUTY COMMISSIONER HAVERI_IDA', 'DEPUTY COMMISSIONER BARPETA_IDA', 'DISTRICT COLLECTOR VIKARABAD_IDA', 'DISTRICT MAGISTRATE DINAJPUR DAKSHIN_IDA']

#### `CITY`

- Likely meaning: Place/location text (not necessarily GPS)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Dhaulpur', 'Benipur', 'Balurghat', 'Medinipur', 'Kharagpur', 'Berhampore', 'Hirekerur', 'Haveri']

#### `WARD`

- Likely meaning: Place/location text (not necessarily GPS)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Dhaulpur (M) - Ward No.10', 'Benipur (M) - Ward No. 07', 'Benipur (M) - Ward No. 29', 'Benipur (M) - Ward No. 10', 'Baidyanathpara (OG) - Ward No.25', 'Medinipur (M) - Ward No.9', 'Kharagpur (M) - Ward No.23', 'Baharampur (M) - Ward No.22']

#### `BLOCK`

- Likely meaning: Place/location text (not necessarily GPS)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Rajakhera', 'Manigachhi', 'Sepau', 'Tardih', 'Darbhanga', 'Nagaon', 'Bari', 'DARBHANGA']

#### `VILLAGE`

- Likely meaning: Place/location text (not necessarily GPS)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Nadauli', 'Jagdishpur', 'Kaithri', 'Chandaur', 'Kotma', 'Lehara', 'Belaur', 'Raghopur']

#### `RECOMMENDED DATE`

- Likely meaning: Date-like field as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2024-03-04', '2024-03-03', '2024-03-02', '2024-03-01', '2024-02-29', '2024-02-28', '2024-02-27', '2024-02-26']
- Date parseable: 60359 (100.00%); invalid non-null: 0; convention tried: monthfirst; min=2023-04-26; max=2024-03-04

#### `ALLOCATION AMOUNT`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['100000', '487000', '500000', '300000', '600000', '1000000', '499000', '150000']
- Numeric parseable: 60359 (100.00%); min=0.0; max=150000000.0; negatives=0; zeros=9; suspected unit=unspecified

#### `IDA APPROVAL`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Action Pending', 'Approved by IDA', 'Rejected by IDA']

#### `STATUS`

- Likely meaning: Reported work/project status
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Unsanctioned', 'Ongoing', 'Sanctioned', 'Completed']

#### `HOUSE`

- Likely meaning: Lok Sabha / Rajya Sabha (or equivalent) as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Lok Sabha', 'Rajya Sabha']

### Duplicates
- Extra full-row duplicates (beyond the first copy): 4221
- Duplicate groups: 2416
- Likely ID columns: (none observed)
- Extra duplicates on likely ID columns: {}

### Observed values of interest
- State values (top): [('Uttar Pradesh', 6616), ('Bihar', 5706), ('Odisha', 4832), ('Tamil Nadu', 4576), ('Andhra Pradesh', 3944), ('Karnataka', 3906), ('Rajasthan', 3859), ('Punjab', 3324), ('Telangana', 2526), ('West Bengal', 2526), ('Madhya Pradesh', 2504), ('Jharkhand', 2259), ('Haryana', 1906), ('Uttarakhand', 1824), ('Gujarat', 1754), ('Assam', 1735), ('Chhattisgarh', 1594), ('Himachal Pradesh', 1240), ('Jammu And Kashmir', 852), ('Maharashtra', 816), ('Kerala', 584), ('Arunachal Pradesh', 332), ('Meghalaya', 266), ('Goa', 172), ('Tripura', 165), ('Mizoram', 119), ('Sikkim', 112), ('Manipur', 73), ('Delhi', 72), ('Andaman And Nicobar Islands', 59), ('Lakshadweep', 42), ('Puducherry', 38), ('Nagaland', 26)]
- District values (top): (no district column inferred)
- Project/work description fields: WORK
- Implementing agency fields: IDA
- Vendor/contractor fields: (none observed)
- Status fields: STATUS
- Latitude/longitude/location fields: CITY, WARD, BLOCK, VILLAGE
- Date fields: RECOMMENDED DATE
- Monetary fields: ALLOCATION AMOUNT

### Andhra Pradesh in this file
- State column used: `STATE`
- District column used: (none observed)
- Total Andhra Pradesh records (name-match on state values): 3944
- AP state-value variants observed: [('Andhra Pradesh', 3944)]
- Coastal/region fields observed: (none observed)
- Coastal correspondence: No coastal-region field was observed. Andhra Pradesh district names are listed with counts only. Correspondence to a Coastal Andhra pilot cannot be decided from this extract. No final Coastal Andhra district list is asserted.
- No final Coastal Andhra district list is asserted from these extracts. Report observed Andhra Pradesh districts and let the team decide the pilot set.

| Andhra Pradesh district (as recorded) | Records | Missing description % | Missing amount % | Missing date % | Missing agency % | Missing status % | Missing location % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| (none observed) | 0 | n/a | n/a | n/a | n/a | n/a | n/a |

Unmatched (non-AP) state values (top):

- Uttar Pradesh: 6616
- Bihar: 5706
- Odisha: 4832
- Tamil Nadu: 4576
- Karnataka: 3906
- Rajasthan: 3859
- Punjab: 3324
- Telangana: 2526
- West Bengal: 2526
- Madhya Pradesh: 2504
- Jharkhand: 2259
- Haryana: 1906
- Uttarakhand: 1824
- Gujarat: 1754
- Assam: 1735
- Chhattisgarh: 1594
- Himachal Pradesh: 1240
- Jammu And Kashmir: 852
- Maharashtra: 816
- Kerala: 584

### Intelligence field support (this file)
- Cost Intelligence candidate fields: ALLOCATION AMOUNT, STATE, CATEGORY, WORK
- Time Intelligence candidate fields: RECOMMENDED DATE, STATUS
- Overlap / duplicate-detection candidate fields: WORK, CITY, WARD, BLOCK, VILLAGE, ALLOCATION AMOUNT, RECOMMENDED DATE, CONSTITUENCY, IDA, MP NAME
- Relationship Graph candidate fields: IDA, STATE, CATEGORY, ALLOCATION AMOUNT, RECOMMENDED DATE, WORK, CONSTITUENCY, MP NAME, HOUSE
- Evidence / Project Digital Passport candidate fields: WORK, CATEGORY, STATE, CONSTITUENCY, MP NAME, HOUSE, IDA, ALLOCATION AMOUNT, RECOMMENDED DATE, STATUS, CITY, WARD, BLOCK, VILLAGE
- Note: No latitude/longitude columns were inferred; GPS proximity overlap is unavailable from this file.
- Note: No vendor/contractor column was inferred; vendor nodes in the relationship graph are unavailable from this file.
- Note: No image/photo column was inferred; photo evidence is not present in this extract.

## Dataset `opencity_mplads_15th_lok_sabha.csv`

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

### Shape
- Rows: 549
- Columns: 20
- Header row index (0-based): 3
- Sheet: (n/a — not a multi-sheet workbook, or single default)
- Load notes: ['header detected at row index 3 (0-based in file preview)']

### Columns
| Column | Pandas dtype | Logical type | Likely role | Missing n | Missing % | Unique (non-null) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `State` | str | string | state | 0 | 0.00% | 36 |
| `House` | str | integer | house | 0 | 0.00% | 1 |
| `Sno` | str | integer | work_id | 0 | 0.00% | 549 |
| `MPName` | str | string | mp | 0 | 0.00% | 549 |
| `Constituency` | str | string | constituency | 1 | 0.18% | 542 |
| `District` | str | string | district | 0 | 0.00% | 432 |
| `TotalEntitlementAmount_crore` | str | float | amount | 2 | 0.36% | 45 |
| `TotalGOIRelease_crore` | str | float | other | 1 | 0.18% | 37 |
| `ReleasePendingAmount_crore` | str | float | amount | 3 | 0.55% | 13 |
| `UnSanctionBalance_crore` | str | float | other | 0 | 0.00% | 276 |
| `UnspentBalance_crore` | str | float | other | 0 | 0.00% | 157 |
| `LastInstNumber1` | str | integer | other | 3 | 0.55% | 3 |
| `LastInstYear` | str | string | other | 3 | 0.55% | 4 |
| `LastReleaseDate` | str | string | other | 3 | 0.55% | 216 |
| `LastRelAmount_crore` | str | float | amount | 0 | 0.00% | 4 |
| `PendingInstallmentNumberAndYear` | str | string | other | 204 | 37.16% | 18 |
| `ReasonsforNotRel` | str | string | other | 539 | 98.18% | 4 |
| `ls_start_year` | str | date | date | 0 | 0.00% | 1 |
| `ls_end_year` | str | date | date | 0 | 0.00% | 1 |
| `lok_sabha` | str | integer | house | 0 | 0.00% | 1 |

### Column details

#### `State`

- Likely meaning: State / UT name as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['A & N Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', 'D & N Haveli']

#### `House`

- Likely meaning: Lok Sabha / Rajya Sabha (or equivalent) as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['1']
- Numeric parseable: 549 (100.00%); min=1.0; max=1.0; negatives=0; zeros=0; suspected unit=n/a

#### `Sno`

- Likely meaning: Work identifier or serial present in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['1', '2', '3', '4', '5', '6', '7', '8']
- Numeric parseable: 549 (100.00%); min=1.0; max=549.0; negatives=0; zeros=0; suspected unit=n/a

#### `MPName`

- Likely meaning: MP name as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Shri Bishnu Pada Ray', 'Shri Asaduddin Owaisi', 'Shri Bapiraju Kanumuri', 'Shri Aruna Kumar Vundavalli', 'Panabaka Lakshmi', 'Dr. Chinta Mohan', 'Dr. Jhansi Lakshmi Botcha', 'Dr. Gaddam Vivekanand']

#### `Constituency`

- Likely meaning: Parliamentary constituency as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['ANDAMAN & NICOBAR ISLANDS', 'HYDERABAD', 'NARASAPURAM', 'RAJAHMUNDRY', 'BAPATLA', 'TIRUPATI(SC)', 'VIZIANAGARAM', 'PEDDAPALLE(SC)']

#### `District`

- Likely meaning: District name as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['ANDAMANS', 'HYDERABAD', 'WEST GODAVARI', 'EAST GODAVARI', 'PRAKASAM', 'CHITTOOR', 'VIZIANAGARAM', 'KARIMNAGAR']

#### `TotalEntitlementAmount_crore`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['20', '19', '21.5', '16.5', '19.48', '21.98', '11.98', '6.98']
- Numeric parseable: 547 (100.00%); min=6.98; max=25.5; negatives=0; zeros=0; suspected unit=crore

#### `TotalGOIRelease_crore`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['20', '19', '16.5', '19.48', '16.98', '11.97', '19.09', '16.59']
- Numeric parseable: 548 (100.00%); min=7.0; max=23.0; negatives=0; zeros=0; suspected unit=crore

#### `ReleasePendingAmount_crore`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['0', '2.5', '5', '0.01', '-4.99', '10', '7.5', '12.5']
- Numeric parseable: 546 (100.00%); min=-12.64; max=12.5; negatives=5; zeros=196; suspected unit=crore

#### `UnSanctionBalance_crore`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2.24', '1.83', '1.26', '4.09', '1.78', '0', '0.03', '0.7']
- Numeric parseable: 549 (100.00%); min=-6.01; max=7.5; negatives=61; zeros=33; suspected unit=crore

#### `UnspentBalance_crore`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['0.77', '0', '1.46', '1.02', '0.09', '1.19', '2.01', '2.08']
- Numeric parseable: 549 (100.00%); min=-2.5; max=8.3; negatives=7; zeros=351; suspected unit=crore

#### `LastInstNumber1`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2', '1', '3']
- Numeric parseable: 546 (100.00%); min=1.0; max=3.0; negatives=0; zeros=0; suspected unit=n/a

#### `LastInstYear`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2013-2014', '2012-2013', '2010-2011', '2011-2012']

#### `LastReleaseDate`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['14-02-2014', '17-12-2014', '9/3/18', '8/9/14', '8/1/15', '3/6/14', '6/12/13', '22-04-2015']

#### `LastRelAmount_crore`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2.5', '1', '4', '0']
- Numeric parseable: 549 (100.00%); min=0.0; max=4.0; negatives=0; zeros=3; suspected unit=crore

#### `PendingInstallmentNumberAndYear`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['3 / 2010-2011,3 / 2013-2014', '3 / 2013-2014', '3 / 2010-2011,3 / 2011-2012,3 / 2013-2014', '2 / 2013-2014,3 / 2013-2014,3 / 2010-2011,3 / 2011-2012', '3 / 2011-2012,3 / 2013-2014', '2 / 2013-2014,3 / 2013-2014', '2 / 2013-2014', '2 / 2013-2014,3 / 2013-2014,3 / 2011-2012']

#### `ReasonsforNotRel`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Bank Statement Awaited, Eligible MPR not Received, Provisional Utilisation Certificate Pending.', 'Audit Certificate Pending, Bank Statement Awaited, Eligible MPR not Received, Utilisation Certificate Pending.', 'Eligible MPR not Received.', 'Eligible MPR not Received, Provisional Utilisation Certificate Pending.']

#### `ls_start_year`

- Likely meaning: Date-like field as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2009']
- Date parseable: 549 (100.00%); invalid non-null: 0; convention tried: dayfirst; min=2009-01-01; max=2009-01-01

#### `ls_end_year`

- Likely meaning: Date-like field as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2014']
- Date parseable: 549 (100.00%); invalid non-null: 0; convention tried: dayfirst; min=2014-01-01; max=2014-01-01

#### `lok_sabha`

- Likely meaning: Lok Sabha / Rajya Sabha (or equivalent) as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['15']
- Numeric parseable: 549 (100.00%); min=15.0; max=15.0; negatives=0; zeros=0; suspected unit=n/a

### Duplicates
- Extra full-row duplicates (beyond the first copy): 0
- Duplicate groups: 0
- Likely ID columns: Sno
- Extra duplicates on likely ID columns: {'Sno': 0}

### Observed values of interest
- State values (top): [('Uttar Pradesh', 80), ('Maharashtra', 48), ('West Bengal', 44), ('Andhra Pradesh', 42), ('Bihar', 40), ('Tamil Nadu', 39), ('Madhya Pradesh', 29), ('Karnataka', 28), ('Gujarat', 26), ('Rajasthan', 25), ('Odisha', 21), ('Kerala', 20), ('Assam', 14), ('Jharkhand', 14), ('Punjab', 13), ('Chhattisgarh', 11), ('Haryana', 10), ('Delhi', 7), ('Jammu & Kashmir', 6), ('Himachal Pradesh', 5), ('Uttarakhand', 5), ('Nominated', 3), ('Arunachal Pradesh', 2), ('Goa', 2), ('Manipur', 2), ('Meghalaya', 2), ('Tripura', 2), ('A & N Islands', 1), ('Chandigarh', 1), ('D & N Haveli', 1), ('Daman & Diu', 1), ('Lakshadweep', 1), ('Mizoram', 1), ('Nagaland', 1), ('Puducherry', 1), ('Sikkim', 1)]
- District values (top): [('NORTH TWENTY FOUR PARGANAS', 5), ('THANE', 4), ('PUNE', 4), ('MUMBAI SUBURBAN', 4), ('MURSHIDABAD', 4), ('SOUTH TWENTY FOUR PARGANAS', 4), ('EAST GODAVARI', 3), ('PATNA', 3), ('COMMISSIONER NORTH DELHI MUNICIPAL CORPORATION', 3), ('BENGALURU URBAN', 3), ('ERNAKULAM', 3), ('JAIPUR', 3), ('CHENNAI', 3), ('PASCHIMI MEDINIPUR', 3), ('BURDWAN', 3), ('HOOGHLY', 3), ('HOWRAH', 3), ('HYDERABAD', 2), ('WEST GODAVARI', 2), ('PRAKASAM', 2), ('CHITTOOR', 2), ('VIZIANAGARAM', 2), ('KARIMNAGAR', 2), ('MAHBUBNAGAR', 2), ('ANANTAPUR', 2), ('CUDDAPAH', 2), ('RANGAREDDY', 2), ('NALGONDA', 2), ('KURNOOL', 2), ('KRISHNA', 2), ('GUNTUR', 2), ('WARANGAL', 2), ('VISAKHAPATNAM', 2), ('MEDAK', 2), ('NOWGONG', 2), ('BETTIAH (W.CHAMPARAN)', 2), ('MUZAFFARPUR', 2), ('SITAMARHI', 2), ('MADHUBANI', 2), ('SIWAN', 2), ('SAMASTIPUR', 2), ('AURANGABAD', 2), ('BILASPUR', 2), ('COMMISSIONER EAST DELHI MUNICIPAL CORPORATION', 2), ('COMMISSIONER SOUTH DELHI MUNICIPAL CORPORATION', 2), ('VADODARA', 2), ('AHMEDABAD', 2), ('SURAT', 2), ('HAMIRPUR', 2), ('MANDI', 2), ('RANCHI', 2), ('BELAGAVI', 2), ('THIRUVANANTHAPURAM', 2), ('MALAPPURAM', 2), ('PALAKKAD', 2), ('KOLLAM', 2), ('KOZHIKODE', 2), ('JALGAON', 2), ('AHMADNAGAR', 2), ('NASHIK', 2), ('MUMBAI CITY', 2), ('KOLHAPUR', 2), ('NAGPUR', 2), ('SOLAPUR', 2), ('GANJAM', 2), ('JODHPUR', 2), ('VELLORE', 2), ('VILLUPURAM', 2), ('TIRUVANNAMALAI', 2), ('COIMBATORE', 2), ('TIRUNELVELI', 2), ('CUDDALORE', 2), ('KANCHIPURAM', 2), ('AZAMGARH', 2), ('SITAPUR', 2), ('AGRA', 2), ('GONDA', 2), ('JAUNPUR', 2), ('ALLAHABAD', 2), ('DEORIA', 2)]
- Project/work description fields: (none observed)
- Implementing agency fields: (none observed)
- Vendor/contractor fields: (none observed)
- Status fields: (none observed)
- Latitude/longitude/location fields: (none observed)
- Date fields: ls_start_year, ls_end_year
- Monetary fields: TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore

### Andhra Pradesh in this file
- State column used: `State`
- District column used: `District`
- Total Andhra Pradesh records (name-match on state values): 42
- AP state-value variants observed: [('Andhra Pradesh', 42)]
- Coastal/region fields observed: (none observed)
- Coastal correspondence: No coastal-region field was observed. Andhra Pradesh district names are listed with counts only. Correspondence to a Coastal Andhra pilot cannot be decided from this extract. No final Coastal Andhra district list is asserted.
- No final Coastal Andhra district list is asserted from these extracts. Report observed Andhra Pradesh districts and let the team decide the pilot set.

| Andhra Pradesh district (as recorded) | Records | Missing description % | Missing amount % | Missing date % | Missing agency % | Missing status % | Missing location % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EAST GODAVARI | 3 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| HYDERABAD | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| WEST GODAVARI | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| PRAKASAM | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| CHITTOOR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| VIZIANAGARAM | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| KARIMNAGAR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| MAHBUBNAGAR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| ANANTAPUR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| CUDDAPAH | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| RANGAREDDY | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| NALGONDA | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| KURNOOL | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| KRISHNA | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| GUNTUR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| WARANGAL | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| VISAKHAPATNAM | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| MEDAK | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| SRIKAKULAM | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| NIZAMABAD | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| NELLORE | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| ADILABAD | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| KHAMMAM | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |

Unmatched (non-AP) state values (top):

- Uttar Pradesh: 80
- Maharashtra: 48
- West Bengal: 44
- Bihar: 40
- Tamil Nadu: 39
- Madhya Pradesh: 29
- Karnataka: 28
- Gujarat: 26
- Rajasthan: 25
- Odisha: 21
- Kerala: 20
- Assam: 14
- Jharkhand: 14
- Punjab: 13
- Chhattisgarh: 11
- Haryana: 10
- Delhi: 7
- Jammu & Kashmir: 6
- Himachal Pradesh: 5
- Uttarakhand: 5

### Intelligence field support (this file)
- Cost Intelligence candidate fields: TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, District, State
- Time Intelligence candidate fields: ls_start_year, ls_end_year
- Overlap / duplicate-detection candidate fields: TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Sno, District, Constituency, MPName
- Relationship Graph candidate fields: Sno, District, State, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Constituency, MPName, House, lok_sabha
- Evidence / Project Digital Passport candidate fields: Sno, State, District, Constituency, MPName, House, lok_sabha, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year
- Note: No latitude/longitude columns were inferred; GPS proximity overlap is unavailable from this file.
- Note: No implementing-agency column was inferred; agency nodes in the relationship graph are unavailable from this file.
- Note: No vendor/contractor column was inferred; vendor nodes in the relationship graph are unavailable from this file.
- Note: No image/photo column was inferred; photo evidence is not present in this extract.

## Dataset `opencity_mplads_16th_lok_sabha.csv`

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

### Shape
- Rows: 569
- Columns: 20
- Header row index (0-based): 3
- Sheet: (n/a — not a multi-sheet workbook, or single default)
- Load notes: ['header detected at row index 3 (0-based in file preview)']

### Columns
| Column | Pandas dtype | Logical type | Likely role | Missing n | Missing % | Unique (non-null) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `State` | str | string | state | 0 | 0.00% | 37 |
| `House` | str | integer | house | 0 | 0.00% | 1 |
| `Sno` | str | integer | work_id | 0 | 0.00% | 569 |
| `MPName` | str | string | mp | 0 | 0.00% | 569 |
| `Constituency` | str | string | constituency | 0 | 0.00% | 541 |
| `District` | str | string | district | 0 | 0.00% | 440 |
| `TotalEntitlementAmount_crore` | str | float | amount | 1 | 0.18% | 14 |
| `TotalGOIRelease_crore` | str | float | other | 1 | 0.18% | 13 |
| `ReleasePendingAmount_crore` | str | float | amount | 1 | 0.18% | 8 |
| `UnSanctionBalance_crore` | str | float | other | 0 | 0.00% | 334 |
| `UnspentBalance_crore` | str | float | other | 0 | 0.00% | 320 |
| `LastInstNumber1` | str | integer | other | 1 | 0.18% | 2 |
| `LastInstYear` | str | string | other | 1 | 0.18% | 5 |
| `LastReleaseDate` | str | string | other | 1 | 0.18% | 210 |
| `LastRelAmount_crore` | str | float | amount | 0 | 0.00% | 2 |
| `PendingInstallmentNumberAndYear` | str | string | other | 375 | 65.91% | 12 |
| `ReasonsforNotRel` | str | string | other | 456 | 80.14% | 13 |
| `ls_start_year` | str | date | date | 0 | 0.00% | 1 |
| `ls_end_year` | str | date | date | 0 | 0.00% | 1 |
| `lok_sabha` | str | integer | house | 0 | 0.00% | 1 |

### Column details

#### `State`

- Likely meaning: State / UT name as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['A & N Islands', 'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chandigarh', 'Chhattisgarh', 'D & N Haveli']

#### `House`

- Likely meaning: Lok Sabha / Rajya Sabha (or equivalent) as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['7']
- Numeric parseable: 569 (100.00%); min=7.0; max=7.0; negatives=0; zeros=0; suspected unit=n/a

#### `Sno`

- Likely meaning: Work identifier or serial present in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['1', '2', '3', '4', '5', '6', '7', '8']
- Numeric parseable: 569 (100.00%); min=1.0; max=569.0; negatives=0; zeros=0; suspected unit=n/a

#### `MPName`

- Likely meaning: MP name as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Shri Bishnu Pada Ray', 'Dr. Vara Prasadarao Velagapalli', 'Dr. Ravindra Babu Pandula', 'Dr. Hari Babu Kambhampati', 'Dr. Naramalli Sivaprasad', 'Shri Ashok Gajapati Raju Pusapati-Ex', 'Shri Gokaraju Ganga Raju', 'Shri J.C. Divakar Reddy']

#### `Constituency`

- Likely meaning: Parliamentary constituency as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['ANDAMAN & NICOBAR ISLANDS', 'TIRUPATI(SC)', 'AMALAPURAM(SC)', 'VISAKHAPATNAM', 'CHITTOOR', 'VIZIANAGARAM', 'NARASAPURAM', 'ANANTAPUR']

#### `District`

- Likely meaning: District name as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['ANDAMANS', 'NELLORE', 'EAST GODAVARI', 'VISAKHAPATNAM', 'CHITTOOR', 'VIZIANAGARAM', 'WEST GODAVARI', 'ANANTAPUR']

#### `TotalEntitlementAmount_crore`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['25', '22.5', '27.5', '20', '15', '17.5', '7.5', '32.5']
- Numeric parseable: 568 (100.00%); min=2.5; max=37.5; negatives=0; zeros=0; suspected unit=crore

#### `TotalGOIRelease_crore`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['25', '22.5', '17.5', '20', '15', '7.5', '30', '5']
- Numeric parseable: 568 (100.00%); min=2.5; max=37.5; negatives=0; zeros=0; suspected unit=crore

#### `ReleasePendingAmount_crore`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['0', '2.5', '7.5', '5', '10', '17.5', '12.5', '15']
- Numeric parseable: 568 (100.00%); min=0.0; max=17.5; negatives=0; zeros=366; suspected unit=crore

#### `UnSanctionBalance_crore`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['1.22', '0.3', '-1.69', '0.1', '0.34', '1.13', '-4.96', '-7.32']
- Numeric parseable: 569 (100.00%); min=-15.9; max=17.68; negatives=202; zeros=13; suspected unit=crore

#### `UnspentBalance_crore`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2.5', '6.28', '3.3', '2.33', '3.87', '2.34', '4.58', '4.39']
- Numeric parseable: 569 (100.00%); min=-0.72; max=17.64; negatives=3; zeros=23; suspected unit=crore

#### `LastInstNumber1`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2', '1']
- Numeric parseable: 568 (100.00%); min=1.0; max=2.0; negatives=0; zeros=0; suspected unit=n/a

#### `LastInstYear`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2018-2019', '2017-2018', '2016-2017', '2015-2016', '2014-2015']

#### `LastReleaseDate`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['29-01-2019', '17-09-2018', '26-09-2019', '11/3/20', '4/9/19', '8/2/19', '13-05-2022', '1/7/19']

#### `LastRelAmount_crore`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2.5', '0']
- Numeric parseable: 569 (100.00%); min=0.0; max=2.5; negatives=0; zeros=1; suspected unit=crore

#### `PendingInstallmentNumberAndYear`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2 / 2018-2019', '1 / 2018-2019,2 / 2018-2019,2 / 2017-2018', '1 / 2018-2019,2 / 2018-2019', '1 / 2017-2018,1 / 2018-2019,2 / 2018-2019,2 / 2017-2018', '2 / 2017-2018', '1 / 2016-2017,1 / 2017-2018,1 / 2018-2019,2 / 2018-2019,2 / 2015-2016,2 / 2017-2018,2 / 2016-2017', '2 / 2018-2019,2 / 2016-2017', '1 / 2016-2017']

#### `ReasonsforNotRel`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['Audit Certificate Pending, Eligible MPR not Received, Utilisation Certificate Pending.', 'Eligible MPR not Received, Provisional Utilisation Certificate Pending.', 'Audit Certificate Pending, Eligible MPR not Received, Provisional Utilisation Certificate Pending.', 'Bank Statement Awaited, Eligible MPR not Received, Provisional Utilisation Certificate Pending.', 'Audit Certificate Pending, Utilisation Certificate Pending.', 'Eligible MPR not Received, Utilisation Certificate Pending.', 'Audit Certificate Pending, Eligible MPR not Received.', 'Incorrect Audit Certificate.']

#### `ls_start_year`

- Likely meaning: Date-like field as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2014']
- Date parseable: 569 (100.00%); invalid non-null: 0; convention tried: dayfirst; min=2014-01-01; max=2014-01-01

#### `ls_end_year`

- Likely meaning: Date-like field as recorded in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2019']
- Date parseable: 569 (100.00%); invalid non-null: 0; convention tried: dayfirst; min=2019-01-01; max=2019-01-01

#### `lok_sabha`

- Likely meaning: Lok Sabha / Rajya Sabha (or equivalent) as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['16']
- Numeric parseable: 569 (100.00%); min=16.0; max=16.0; negatives=0; zeros=0; suspected unit=n/a

### Duplicates
- Extra full-row duplicates (beyond the first copy): 0
- Duplicate groups: 0
- Likely ID columns: Sno
- Extra duplicates on likely ID columns: {'Sno': 0}

### Observed values of interest
- State values (top): [('Uttar Pradesh', 83), ('Maharashtra', 50), ('West Bengal', 46), ('Bihar', 41), ('Tamil Nadu', 39), ('Madhya Pradesh', 31), ('Karnataka', 30), ('Rajasthan', 27), ('Andhra Pradesh', 25), ('Gujarat', 25), ('Odisha', 22), ('Kerala', 21), ('Telangana', 18), ('Assam', 15), ('Punjab', 15), ('Jharkhand', 14), ('Chhattisgarh', 11), ('Haryana', 10), ('Delhi', 7), ('Jammu & Kashmir', 7), ('Uttarakhand', 5), ('Himachal Pradesh', 4), ('Meghalaya', 3), ('Arunachal Pradesh', 2), ('Goa', 2), ('Manipur', 2), ('Nagaland', 2), ('Nominated', 2), ('Tripura', 2), ('A & N Islands', 1), ('Chandigarh', 1), ('D & N Haveli', 1), ('Daman & Diu', 1), ('Lakshadweep', 1), ('Mizoram', 1), ('Puducherry', 1), ('Sikkim', 1)]
- District values (top): [('NORTH TWENTY FOUR PARGANAS', 6), ('MUMBAI SUBURBAN', 5), ('SOUTH TWENTY FOUR PARGANAS', 5), ('PUNE', 4), ('EAST GODAVARI', 3), ('VISAKHAPATNAM', 3), ('PATNA', 3), ('COMMISSIONER SOUTH DELHI MUNICIPAL CORPORATION', 3), ('BENGALURU URBAN', 3), ('MALAPPURAM', 3), ('THIRUVANANTHAPURAM', 3), ('THANE', 3), ('CHENNAI', 3), ('GORAKHPUR', 3), ('ALLAHABAD', 3), ('HOOGHLY', 3), ('PASCHIMI MEDINIPUR', 3), ('MURSHIDABAD', 3), ('BURDWAN', 3), ('PURBA MEDINIPUR', 3), ('HOWRAH', 3), ('NELLORE', 2), ('CHITTOOR', 2), ('WEST GODAVARI', 2), ('ANANTAPUR', 2), ('GUNTUR', 2), ('KRISHNA', 2), ('KURNOOL', 2), ('PRAKASAM', 2), ('NOWGONG', 2), ('MUZAFFARPUR', 2), ('BETTIAH (W.CHAMPARAN)', 2), ('MADHUBANI', 2), ('SARAN', 2), ('SAMASTIPUR', 2), ('MOTHIHARI (E.CHAMPARAN)', 2), ('ARARIA', 2), ('AURANGABAD', 2), ('COMMISSIONER NORTH DELHI MUNICIPAL CORPORATION', 2), ('COMMISSIONER EAST DELHI MUNICIPAL CORPORATION', 2), ('AHMEDABAD', 2), ('RAJKOT', 2), ('SURAT', 2), ('SRINAGAR', 2), ('RANCHI', 2), ('SHIVAMOGGA', 2), ('BALLARI', 2), ('BELAGAVI', 2), ('ERNAKULAM', 2), ('PALAKKAD', 2), ('KOZHIKODE', 2), ('KOLLAM', 2), ('JHABUA', 2), ('SHAHDOL', 2), ('JALGAON', 2), ('Palghar', 2), ('NASHIK', 2), ('KOLHAPUR', 2), ('AHMADNAGAR', 2), ('NAGPUR', 2), ('BHANDARA', 2), ('SOLAPUR', 2), ('WEST GARO HILLS', 2), ('DIMAPUR', 2), ('KANDHAMAL', 2), ('GANJAM', 2), ('AMRITSAR', 2), ('LUDHIANA', 2), ('JAIPUR', 2), ('ALWAR', 2), ('AJMER', 2), ('VILLUPURAM', 2), ('CUDDALORE', 2), ('TIRUVANNAMALAI', 2), ('VELLORE', 2), ('KANCHIPURAM', 2), ('TIRUNELVELI', 2), ('THANJAVUR', 2), ('ERODE', 2), ('Hanumakonda', 2)]
- Project/work description fields: (none observed)
- Implementing agency fields: (none observed)
- Vendor/contractor fields: (none observed)
- Status fields: (none observed)
- Latitude/longitude/location fields: (none observed)
- Date fields: ls_start_year, ls_end_year
- Monetary fields: TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore

### Andhra Pradesh in this file
- State column used: `State`
- District column used: `District`
- Total Andhra Pradesh records (name-match on state values): 25
- AP state-value variants observed: [('Andhra Pradesh', 25)]
- Coastal/region fields observed: (none observed)
- Coastal correspondence: No coastal-region field was observed. Andhra Pradesh district names are listed with counts only. Correspondence to a Coastal Andhra pilot cannot be decided from this extract. No final Coastal Andhra district list is asserted.
- No final Coastal Andhra district list is asserted from these extracts. Report observed Andhra Pradesh districts and let the team decide the pilot set.

| Andhra Pradesh district (as recorded) | Records | Missing description % | Missing amount % | Missing date % | Missing agency % | Missing status % | Missing location % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EAST GODAVARI | 3 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| VISAKHAPATNAM | 3 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| NELLORE | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| CHITTOOR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| WEST GODAVARI | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| ANANTAPUR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| GUNTUR | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| KRISHNA | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| KURNOOL | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| PRAKASAM | 2 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| VIZIANAGARAM | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| SRIKAKULAM | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |
| CUDDAPAH | 1 | n/a | 0.00% | 0.00% | n/a | n/a | n/a |

Unmatched (non-AP) state values (top):

- Uttar Pradesh: 83
- Maharashtra: 50
- West Bengal: 46
- Bihar: 41
- Tamil Nadu: 39
- Madhya Pradesh: 31
- Karnataka: 30
- Rajasthan: 27
- Gujarat: 25
- Odisha: 22
- Kerala: 21
- Telangana: 18
- Assam: 15
- Punjab: 15
- Jharkhand: 14
- Chhattisgarh: 11
- Haryana: 10
- Delhi: 7
- Jammu & Kashmir: 7
- Uttarakhand: 5

### Intelligence field support (this file)
- Cost Intelligence candidate fields: TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, District, State
- Time Intelligence candidate fields: ls_start_year, ls_end_year
- Overlap / duplicate-detection candidate fields: TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Sno, District, Constituency, MPName
- Relationship Graph candidate fields: Sno, District, State, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Constituency, MPName, House, lok_sabha
- Evidence / Project Digital Passport candidate fields: Sno, State, District, Constituency, MPName, House, lok_sabha, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year
- Note: No latitude/longitude columns were inferred; GPS proximity overlap is unavailable from this file.
- Note: No implementing-agency column was inferred; agency nodes in the relationship graph are unavailable from this file.
- Note: No vendor/contractor column was inferred; vendor nodes in the relationship graph are unavailable from this file.
- Note: No image/photo column was inferred; photo evidence is not present in this extract.

## Dataset `opencity_mplads_17th_lok_sabha.csv`

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

### Shape
- Rows: 557
- Columns: 11
- Header row index (0-based): 0
- Sheet: (n/a — not a multi-sheet workbook, or single default)
- Load notes: (none)

### Columns
| Column | Pandas dtype | Logical type | Likely role | Missing n | Missing % | Unique (non-null) |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `Sl No` | str | integer | work_id | 0 | 0.00% | 557 |
| `MP Name` | str | string | mp | 0 | 0.00% | 557 |
| `Constituency` | str | string | constituency | 0 | 0.00% | 542 |
| `Entitlement` | str | float | other | 0 | 0.00% | 13 |
| `FundReceivedGOI` | str | float | other | 0 | 0.00% | 14 |
| `AmountAvailable` | str | float | amount | 0 | 0.00% | 553 |
| `WorksRecommCost` | str | float | amount | 0 | 0.00% | 552 |
| `WSCost` | str | float | amount | 0 | 0.00% | 554 |
| `ActualExpenditureIncurred` | str | float | amount | 0 | 0.00% | 554 |
| `UtilizationOverRelease` | str | float | other | 0 | 0.00% | 554 |
| `UnspentBalance` | str | float | other | 0 | 0.00% | 553 |

### Column details

#### `Sl No`

- Likely meaning: Work identifier or serial present in the extract
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['1', '2', '3', '4', '5', '6', '7', '8']
- Numeric parseable: 557 (100.00%); min=1.0; max=557.0; negatives=0; zeros=0; suspected unit=n/a

#### `MP Name`

- Likely meaning: MP name as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['kuldeep rai sharma', 'Srinivas Kesineni', 'Kuruva Gorantla Madhav', 'MVVV Satyanarayana', 'Raghu Ramakrishna Raju Kanumuru', 'Maddila Gurumoorthy', 'Beesetti Venkata Satyavathi', 'Talari Rangaiah']

#### `Constituency`

- Likely meaning: Parliamentary constituency as recorded
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['ANDAMAN AND NICOBAR ISLANDS', 'VIJAYAWADA', 'HINDUPUR', 'MVVV VISAKHAPATNAM', 'NARASAPURAM', 'TIRUPATI(SC)', 'ANAKAPALLE', 'ANANTAPUR']

#### `Entitlement`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['17', '12', '24.5', '27', '19.5', '5', '29.5', '34.5']
- Numeric parseable: 557 (100.00%); min=5.0; max=34.5; negatives=0; zeros=0; suspected unit=n/a

#### `FundReceivedGOI`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['5', '9.5', '7', '2', '17', '12', '19.5', '2.5']
- Numeric parseable: 557 (100.00%); min=0.0; max=24.5; negatives=0; zeros=1; suspected unit=n/a

#### `AmountAvailable`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['5.2038', '15.3459', '18.5668', '9.6406', '11.7435', '12.6146', '16.1463', '10.9197']
- Numeric parseable: 557 (100.00%); min=0.0; max=24.6557; negatives=0; zeros=1; suspected unit=unspecified

#### `WorksRecommCost`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['18.2939', '36.0984', '34.0322', '8.9386', '12.35', '25.9159', '20.8276', '27.7902']
- Numeric parseable: 557 (100.00%); min=0.0; max=39.1381; negatives=0; zeros=2; suspected unit=unspecified

#### `WSCost`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['10.9222', '22.8532', '25.2437', '8.6086', '6.96', '22.5134', '15.7482', '22.5322']
- Numeric parseable: 557 (100.00%); min=0.0; max=25.2437; negatives=0; zeros=2; suspected unit=unspecified

#### `ActualExpenditureIncurred`

- Likely meaning: Monetary value (role/unit inferred from the column name only)
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2.5269', '12.5675', '16.1535', '7.6388', '2.1454', '10', '13.3994', '9.7397']
- Numeric parseable: 557 (100.00%); min=0.0; max=18.6401; negatives=0; zeros=3; suspected unit=unspecified

#### `UtilizationOverRelease`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['50.538', '130.289474', '168.036842', '107.697143', '40.908', '498', '189.42', '137.138571']
- Numeric parseable: 557 (100.00%); min=0.0; max=498.0; negatives=0; zeros=3; suspected unit=n/a

#### `UnspentBalance`

- Likely meaning: Observed column; role not inferred from the name
- Meaning basis: column name heuristic; not an official data dictionary from the publisher
- Sample values (observed, truncated): ['2.6769', '2.7784', '2.4133', '2.0018', '9.5981', '2.6146', '2.7469', '1.18']
- Numeric parseable: 557 (100.00%); min=-1.8604; max=17.7231; negatives=2; zeros=3; suspected unit=n/a

### Duplicates
- Extra full-row duplicates (beyond the first copy): 0
- Duplicate groups: 0
- Likely ID columns: Sl No
- Extra duplicates on likely ID columns: {'Sl No': 0}

### Observed values of interest
- State values (top): (no state column inferred)
- District values (top): (no district column inferred)
- Project/work description fields: (none observed)
- Implementing agency fields: (none observed)
- Vendor/contractor fields: (none observed)
- Status fields: (none observed)
- Latitude/longitude/location fields: (none observed)
- Date fields: (none observed)
- Monetary fields: AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred

### Andhra Pradesh in this file
- State column used: (none observed)
- District column used: (none observed)
- Total Andhra Pradesh records (name-match on state values): 0
- AP state-value variants observed: (none)
- Coastal/region fields observed: (none observed)
- Coastal correspondence: No state column was observed, so Andhra Pradesh rows cannot be counted from this file. No Coastal Andhra district list is asserted.
- No final Coastal Andhra district list is asserted from these extracts. Report observed Andhra Pradesh districts and let the team decide the pilot set.

| Andhra Pradesh district (as recorded) | Records | Missing description % | Missing amount % | Missing date % | Missing agency % | Missing status % | Missing location % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| (none observed) | 0 | n/a | n/a | n/a | n/a | n/a | n/a |

### Intelligence field support (this file)
- Cost Intelligence candidate fields: AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred
- Time Intelligence candidate fields: (none observed)
- Overlap / duplicate-detection candidate fields: AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred, Sl No, Constituency, MP Name
- Relationship Graph candidate fields: Sl No, AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred, Constituency, MP Name
- Evidence / Project Digital Passport candidate fields: Sl No, Constituency, MP Name, AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred
- Note: No date column was inferred; Time Intelligence cannot be supported from this file yet.
- Note: No latitude/longitude columns were inferred; GPS proximity overlap is unavailable from this file.
- Note: No implementing-agency column was inferred; agency nodes in the relationship graph are unavailable from this file.
- Note: No vendor/contractor column was inferred; vendor nodes in the relationship graph are unavailable from this file.
- Note: No image/photo column was inferred; photo evidence is not present in this extract.

## Combined Andhra Pradesh view

- State column used: `STATE`
- District column used: `District`
- Total Andhra Pradesh records (name-match on state values): 4011
- AP state-value variants observed: [('Andhra Pradesh', 4011)]
- Coastal/region fields observed: (none observed)
- Coastal correspondence: Combined Andhra Pradesh district counts across profiled extracts. Files may have different grain (work-level vs MP-level) and are not merged. No final Coastal Andhra district list is asserted.
- No final Coastal Andhra district list is asserted from these extracts. Report observed Andhra Pradesh districts and let the team decide the pilot set.

| Andhra Pradesh district (as recorded) | Records | Missing description % | Missing amount % | Missing date % | Missing agency % | Missing status % | Missing location % |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| EAST GODAVARI | 6 | n/a | n/a | n/a | n/a | n/a | n/a |
| VISAKHAPATNAM | 5 | n/a | n/a | n/a | n/a | n/a | n/a |
| WEST GODAVARI | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| PRAKASAM | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| CHITTOOR | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| ANANTAPUR | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| KURNOOL | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| KRISHNA | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| GUNTUR | 4 | n/a | n/a | n/a | n/a | n/a | n/a |
| VIZIANAGARAM | 3 | n/a | n/a | n/a | n/a | n/a | n/a |
| CUDDAPAH | 3 | n/a | n/a | n/a | n/a | n/a | n/a |
| NELLORE | 3 | n/a | n/a | n/a | n/a | n/a | n/a |
| HYDERABAD | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| KARIMNAGAR | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| MAHBUBNAGAR | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| RANGAREDDY | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| NALGONDA | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| WARANGAL | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| MEDAK | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| SRIKAKULAM | 2 | n/a | n/a | n/a | n/a | n/a | n/a |
| NIZAMABAD | 1 | n/a | n/a | n/a | n/a | n/a | n/a |
| ADILABAD | 1 | n/a | n/a | n/a | n/a | n/a | n/a |
| KHAMMAM | 1 | n/a | n/a | n/a | n/a | n/a | n/a |

## Combined intelligence field support

- Cost Intelligence candidate fields: ALLOCATION AMOUNT, STATE, CATEGORY, WORK, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, District, State, AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred
- Time Intelligence candidate fields: RECOMMENDED DATE, STATUS, ls_start_year, ls_end_year
- Overlap / duplicate-detection candidate fields: WORK, CITY, WARD, BLOCK, VILLAGE, ALLOCATION AMOUNT, RECOMMENDED DATE, CONSTITUENCY, IDA, MP NAME, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Sno, District, Constituency, MPName, AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred, Sl No, MP Name
- Relationship Graph candidate fields: IDA, STATE, CATEGORY, ALLOCATION AMOUNT, RECOMMENDED DATE, WORK, CONSTITUENCY, MP NAME, HOUSE, Sno, District, State, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Constituency, MPName, House, lok_sabha, Sl No, AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred, MP Name
- Evidence / Project Digital Passport candidate fields: WORK, CATEGORY, STATE, CONSTITUENCY, MP NAME, HOUSE, IDA, ALLOCATION AMOUNT, RECOMMENDED DATE, STATUS, CITY, WARD, BLOCK, VILLAGE, Sno, State, District, Constituency, MPName, House, lok_sabha, TotalEntitlementAmount_crore, ReleasePendingAmount_crore, LastRelAmount_crore, ls_start_year, ls_end_year, Sl No, MP Name, AmountAvailable, WorksRecommCost, WSCost, ActualExpenditureIncurred
- Note: No latitude/longitude columns were inferred; GPS proximity overlap is unavailable from this file.
- Note: No vendor/contractor column was inferred; vendor nodes in the relationship graph are unavailable from this file.
- Note: No image/photo column was inferred; photo evidence is not present in this extract.
- Note: No implementing-agency column was inferred; agency nodes in the relationship graph are unavailable from this file.
- Note: No date column was inferred; Time Intelligence cannot be supported from this file yet.

## Join keys with Recommended Works

Observed column-name and role overlaps only. Files are not merged and values are not assumed to match.
- Recommended Works dataset used for comparison: `github_vonter_india-mplads-works_MPLADS.csv`

| Other dataset | Recommended Works column | Other column | Match kind | Likely role | Note |
| --- | --- | --- | --- | --- | --- |
| `opencity_mplads_15th_lok_sabha.csv` | `STATE` | `State` | normalized_column_name | state | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_15th_lok_sabha.csv` | `CONSTITUENCY` | `Constituency` | normalized_column_name | constituency | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_15th_lok_sabha.csv` | `HOUSE` | `House` | normalized_column_name | house | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_15th_lok_sabha.csv` | `MP NAME` | `MPName` | likely_role | mp | Same inferred role from column names. Values are not assumed to match; files are not merged. |
| `opencity_mplads_15th_lok_sabha.csv` | `HOUSE` | `lok_sabha` | likely_role | house | Same inferred role from column names. Values are not assumed to match; files are not merged. |
| `opencity_mplads_16th_lok_sabha.csv` | `STATE` | `State` | normalized_column_name | state | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_16th_lok_sabha.csv` | `CONSTITUENCY` | `Constituency` | normalized_column_name | constituency | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_16th_lok_sabha.csv` | `HOUSE` | `House` | normalized_column_name | house | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_16th_lok_sabha.csv` | `MP NAME` | `MPName` | likely_role | mp | Same inferred role from column names. Values are not assumed to match; files are not merged. |
| `opencity_mplads_16th_lok_sabha.csv` | `HOUSE` | `lok_sabha` | likely_role | house | Same inferred role from column names. Values are not assumed to match; files are not merged. |
| `opencity_mplads_17th_lok_sabha.csv` | `MP NAME` | `MP Name` | normalized_column_name | mp | Same normalized column name. Values are not assumed to match; files are not merged. |
| `opencity_mplads_17th_lok_sabha.csv` | `CONSTITUENCY` | `Constituency` | normalized_column_name | constituency | Same normalized column name. Values are not assumed to match; files are not merged. |

## Coastal Andhra decision

No final Coastal Andhra district list is asserted from these extracts. Report observed Andhra Pradesh districts and let the team decide the pilot set.

D014 remains: initial pilot is Coastal Andhra Pradesh **subject to actual data availability**.

<!-- BEGIN CLEANED DATASET -->
## Work-level cleaning (Phase 2)

The primary free work-level extract was cleaned without modifying `data/raw/` and without merging OpenCity MP-level files.
See `DATA_CLEANING_REPORT.md` for data quality, limitations, lifecycle mapping, and engine-field sufficiency.

### Cleaning run counts

- Raw rows: 60359
- Cleaned rows: 56138
- Andhra Pradesh cleaned rows: 3640
- Extra exact source duplicates: 4221

No Coastal Andhra district list is asserted (the work-level file has no District column).
<!-- END CLEANED DATASET -->
