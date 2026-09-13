# Compliance Engine V1 report

Date: 2026-09-10  
Engine: `compliance-rules-v1`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID execution fields: `data/synthetic/` only, labelled HYBRID/TEST

This engine is a **transparent, deterministic MPLADS guideline-rule evaluator**. It is **not** an ML model. It does **not** assign Investigation Priority and does not produce a legal finding.

Cost Intelligence V1.1, Time Intelligence V1, and Overlap Intelligence V1 are frozen and were not modified.

---

## Dual mode

| Mode | Inputs | What is evaluated |
| --- | --- | --- |
| **REAL** | Observed extract fields only: recommendation date, status, IDA text, allocation, category, house, place text | Rules that need sanction date, completion date, expenditure, district, vendor, GPS, SC/ST share, amount unit, or the official 2023 ineligible-works list return **NOT_ASSESSABLE**. |
| **HYBRID_TEST** | Same observed fields plus synthetic sanction/completion dates and sanctioned/expenditure amounts | Timeline and spend-versus-sanction rules can be TRIGGERED or NOT_TRIGGERED. Outputs are labelled HYBRID/TEST. |

The real extract has **no** verified district, vendor, GPS, verified expenditure, verified sanction date, verified completion date, or labelled amount unit. Those fields are never invented.

`scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, and `coordinate_source` are excluded from rule inputs. Held-out labels are attached only after evaluation.

---

## Architecture

Rules live in `rules/mplads_compliance_v1.json`. The evaluator loads that file and applies each rule to a project/evidence context. Evaluation logic is data-driven (`operator`, fields, thresholds). Python does not hard-code MPLADS conditions outside the catalog and the small operator set.

Possible rule result states:

- `TRIGGERED`
- `NOT_TRIGGERED`
- `NOT_ASSESSABLE`

Project-level `compliance_status`:

- `RULES_TRIGGERED` — at least one TRIGGERED rule
- `NO_RULES_TRIGGERED` — at least one assessable NOT_TRIGGERED rule and none triggered
- `INCONCLUSIVE` — every rule is NOT_ASSESSABLE

HTTP: `GET /api/v1/projects/{id}/compliance` (`mode=real` or `hybrid-test`).

The engine persists a compliance `evidence_object` with rule IDs and guideline references. It does not write fusion scores.

---

## 1. Rule inventory

| Rule | Category | Severity | Condition (sourced) | Typical REAL result |
| --- | --- | --- | ---: | --- |
| R001 | SANCTION_TIMELINE | attention | Sanction/rejection within 45 days of receipt (Para 3.2.4) | NOT_ASSESSABLE (no sanction date / IDA receipt date) |
| R002 | COMPLETION_TIMELINE | attention | Completion generally within one year of sanction (Para 3.2.12) | NOT_ASSESSABLE (no sanction/completion date) |
| R003 | PAYMENT_TIMELINE | watch | No payment recorded within three months of sanction (MoSPI monitoring described in LS SQ *44) | NOT_ASSESSABLE (no payment date / verified expenditure) |
| R004 | COST_ESTIMATION | attention | Recorded spend above sanctioned amount (IDA examines cost estimation / compliance) | NOT_ASSESSABLE (no verified expenditure) |
| R005 | SC_EARMARK | watch | ≥ 15% of annual entitlement for SC-inhabited areas (Para 5.4.1) | NOT_ASSESSABLE (no SC share / MP-year totals) |
| R006 | ST_EARMARK | watch | ≥ 7.5% of annual entitlement for ST-inhabited areas (Para 5.4.1) | NOT_ASSESSABLE |
| R007 | ENTITLEMENT_CEILING | attention | FY sanctioned total ≤ MP entitlement including interest/redistribution | NOT_ASSESSABLE (no MP-year totals; amount unit unspecified) |
| R008 | OUTSIDE_CONSTITUENCY | watch | Outside constituency/state ceiling raised to Rs. 50 lakh in 2023 | NOT_ASSESSABLE (no verified district; unit unspecified) |
| R009 | INELIGIBLE_WORKS | attention | 2023 illustrative eligible/ineligible list | NOT_ASSESSABLE (2023 list not stored in this repository; no keyword dictionary) |
| R010 | STATUTORY_CLEARANCE | attention | Statutory/regulatory clearances before sanction | NOT_ASSESSABLE |
| R011 | OM_UNDERTAKING | watch | User-agency O&M undertaking before sanction | NOT_ASSESSABLE |
| R012 | PUBLIC_USE_PLAQUE | info | Completed work put to public use; plaque may be placed | NOT_ASSESSABLE (no plaque/completion evidence) |
| R013 | GEOGRAPHIC_ELIGIBILITY | watch | LS in constituency; RS in State of election; nominated as provided | NOT_ASSESSABLE (extract constituency is not a verified work district) |
| R014 | ENTITLEMENT_CEILING | watch | Annual entitlement Rs. 5 crore; not applied without a known amount unit | NOT_ASSESSABLE (`amount_unit` unspecified) |
| R015 | IMPLEMENTING_AUTHORITY | info | Recommendation is forwarded to an IDA; blank IDA on the record triggers | Assessable: NOT_TRIGGERED when IDA text is present |
| R016 | ADMISSIBLE_WORKS | info | Repair and maintenance of public assets is admissible under Guidelines 2023 | NOT_TRIGGERED for observed `Repair and Renovation`; otherwise NOT_ASSESSABLE |

No 2016 negative list is encoded. Guidelines 2023 changed repair/maintenance admissibility, so applying the older list would be incorrect.

---

## 2. Source references

The full 2023 PDF is **not** stored in this repository (`data/guidelines/` is empty). Rules are grounded only in cited official/public material:

| Source ID | What was used | URL |
| --- | --- | --- |
| LS-SQ-44-2026-07-22 | Para 3.2.4 (45 days), Para 3.2.6 (MCC exclusion, not applied), Para 3.2.12 (one year), clearances/O&M undertaking, 3-month no-payment monitoring | https://sansad.in/getFile/lsapps/loksabhaquestions/annex/188/AS44_hNPX9H.pdf |
| LS-USQ-2887-2026-08-05 | Para 5.4.1 SC 15% / ST 7.5%; Para 5.4.2 interchangeability (not applied) | https://sansad.in/getFile/lsapps/loksabhaquestions/annex/188/AU2887_YqZH4s.pdf |
| MOSPI-MPLADS-ABOUT | Repair admissible; Rs. 50 lakh outside constituency/state; IDA receives recommendations; cost estimation; FY entitlement ceiling; plaque/public use; LS/RS/nominated geography; illustrative eligible/ineligible list exists | https://www.mospi.gov.in/about-us/mplads |
| MPLADS-PORTAL-ABOUT | Annual entitlement ₹5 crore from FY 2011-12 | https://mplads.mospi.gov.in/digigov/landingpage.html |
| MPLADS-GOV-HOME | Rs. 5 crore entitlement; LS/RS recommendation geography | https://mplads.gov.in/ |
| GUIDELINES-2023-PDF | Cited by MoSPI as the English Guidelines 2023 PDF; **not downloaded into the repo** | https://www.mplads.gov.in/MPLADS/UploadedFiles/MPLADSGuidelines2023_English_.pdf |

Para 3.2.6 MCC days are documented as a limitation of R001. They are not subtracted, because an MCC calendar is unavailable.

---

## 3. Available / unavailable fields

### Available on REAL works

`internal_project_id`, MP name, work description, category, state, constituency, IDA, sparse place text, recommended date, allocation amount (unit unspecified), IDA approval, status, house, lifecycle stage.

### Unavailable (not invented)

- verified district
- verified expenditure / payment date
- vendor
- GPS
- verified sanction date
- verified completion date
- source amount unit
- SC/ST area flags and MP-year entitlement totals
- official 2023 ineligible-work match
- statutory clearance / O&M undertaking / plaque evidence

HYBRID_TEST may attach synthetic `sanction_date`, planned/actual dates, `sanctioned_amount`, `expenditure_amount`, and `as_of_date` for controlled tests only.

---

## 4. Triggered examples

These HYBRID/TEST rows are **not** real government findings.

### HYBRID — DEMO_OVERBILL (project 22177, ELURU, Completed)

- R004 **TRIGGERED** (attention): synthetic expenditure 6,390,000 vs sanctioned 3,550,000.
- R001 / R002 **NOT_TRIGGERED** (sanction 15 days after recommendation; completion 207 days after sanction).
- R016 **NOT_TRIGGERED** (observed category is Repair and Renovation; repair is admissible under Guidelines 2023).
- Held-out label `OVERBILL` was **not** a rule input.

### HYBRID — COST_ANOMALY (project 25533, ARAKU(ST), Completed)

- R004 **TRIGGERED** (attention): synthetic expenditure 401,258 vs sanctioned 194,840.
- R001 / R002 **NOT_TRIGGERED**.
- Held-out label `COST_ANOMALY` was attached after evaluation.

### HYBRID — DEMO_CLEAN (project 26946, KADAPA, Sanctioned)

- R004 **NOT_TRIGGERED** (expenditure 0 ≤ sanctioned 3,500,000).
- R003 **TRIGGERED** (watch): synthetic expenditure 0, 227 days after synthetic sanction 2023-11-16 versus as-of 2024-06-30. This is a HYBRID clock on a sanctioned-not-started prototype row. It is not a real MPLADS payment delay.
- R001 **NOT_TRIGGERED** (17 days from recommendation 2023-10-30 to sanction 2023-11-16).

Unit tests also cover constructed TRIGGERED cases (45-day gap, spend above sanctioned, blank IDA, SC share below 15%).

---

## 5. NOT_ASSESSABLE examples

### REAL — Unsanctioned (project 217, HINDUPUR)

- R001 **NOT_ASSESSABLE**: "Sanction-date evidence is unavailable in the current real dataset. Date of receipt by the Implementing District Authority is also unavailable."
- Same for R002–R014 except R015.
- R015 **NOT_TRIGGERED**: IDA `DISTRICT COLLECTOR SRI SATHYA SAI_IDA` is recorded.
- Observed STATUS=Unsanctioned is **not** treated as a verified open 45-day SLA clock.

### REAL — Completed (project 5263, ONGOLE)

- R002 / R012 **NOT_ASSESSABLE**: completion-date and plaque evidence are unavailable. Observed STATUS=Completed is not a plaque or public-use inspection record.

### REAL — Repair and Renovation (project 3348, SRIKAKULAM)

- R016 **NOT_TRIGGERED**: sourced 2023 repair/maintenance admissibility.
- R009 **NOT_ASSESSABLE**: the official 2023 illustrative list is not in the repository.

### HYBRID — DEMO_STUCK (project 52862, ANANTAPUR, Ongoing)

- R003 **NOT_ASSESSABLE**: synthetic expenditure 108,000 is recorded, but there is no payment date, so the three-month payment clock cannot be verified.
- R002 **NOT_TRIGGERED**: sanction 2023-08-22 to as-of 2024-06-30 is 313 days (≤ 365). This is HYBRID/TEST, not a real delay statistic.

---

## 6. Limitations

- This is rule-trace, not a legal conclusion and not Investigation Priority.
- The official Guidelines 2023 PDF was not ingested. Rules that need the illustrative eligible/ineligible annex remain NOT_ASSESSABLE.
- Amount-unit unspecified: Rs. 5 crore and Rs. 50 lakh ceilings are not applied to `allocation_amount`.
- 45-day SLA uses HYBRID `sanction_date` versus observed `recommended_date` as a proxy for IDA receipt. That proxy is documented and is not an official receipt clock.
- Para 3.2.12 hilly-terrain exception cannot be verified.
- Para 5.4.2 SC/ST interchangeability cannot be applied (no population composition).
- HYBRID results must not be presented as real government findings. DEMO_CLEAN triggering R003 is a prototype zero-spend clock, not an official PFMS result.
- One citizen report, satellite measurement, or vendor identity is out of scope for this engine.

---

## Tests

**265** backend tests passed (0 failed), including loader, malformed catalogs, TRIGGERED / NOT_TRIGGERED / NOT_ASSESSABLE, severity, determinism, explanation wording, source-reference preservation, no fabricated REAL fields, and held-out label isolation.

CLI:

```powershell
cd backend
python -m app.engines.compliance.evaluate_run
```
