# SYNTHETIC data quality report

Audit of the 10,000-record **HYBRID** enrichment layer in `data/synthetic/sarvsakshi_synthetic_enrichment.csv`.

This layer is a **SYNTHETIC prototype/testing set**. It does not represent real MPLADS population statistics and is not a legal fraud label set. The audit did not generate new data, did not modify the real extract, and did not modify the synthetic CSV.

- Audited at: 2026-09-10
- Synthetic SHA-256: `d1de1b151cd115f9e4c0ae291f585481527a1f02846cb593c66d6c819895f4f1`
- Real cleaned extract SHA-256: `fb4bd06a75a3f66d7bfc08d02b86c980932682926b441fc4371dca8afdd9dd64` (matches provenance; 56,138 rows unchanged)
- Existing tests: **all passed** (`pytest` in `backend/`)

Severity:

- **PASS** — required property holds
- **WARNING** — usable for controlled tests, but can mislead if treated as real MPLADS statistics or as a clean supervised-learning table
- **CRITICAL** — would break evaluation or let a model trivially recover the scenario label

---

## 1. Relationship to real projects

| Check | Result | Severity |
| --- | --- | --- |
| Every synthetic row has exactly one `internal_project_id` | 10,000 unique IDs, 0 duplicates | **PASS** |
| Every ID exists in the cleaned real extract | 0 unknown IDs | **PASS** |
| One synthetic row per linked real work | 1:1 (no duplicated real works in this layer) | **PASS** |
| `real_*` snapshot matches the cleaned extract | 0 mismatches on all 14 copied fields | **PASS** |
| Real extract / `data/raw/` / `project` table overwritten | Real SHA-256 unchanged; synthetic files live only under `data/synthetic/` | **PASS** |
| Governance labels | All 10,000 rows `record_mode=HYBRID`, `enrichment_source=SYNTHETIC` | **PASS** |

Copied real fields checked: state, constituency, category, work description, allocation, recommended date, status, lifecycle, IDA, city, block, village, MP name, house.

The synthetic file **adds** enrichment columns; it does not write those columns into `mplads_works_cleaned.csv` or SQLite `project`.

---

## 2. Distribution quality

This sample was **stratified for testing** (all 1,503 Completed and all 629 Ongoing were included). It is **not** a random 10k draw from the 56,138 real works.

| Dimension | Observation | Severity |
| --- | --- | --- |
| State coverage | All 33 real state/UT values appear. Andhra Pradesh share is close to real (6.32% vs 6.48%). Uttar Pradesh is oversampled (17.9% vs 10.9%). | **WARNING** |
| Constituency | 418 of 457 real constituencies. `Sitting Rajya Sabha` is the top bucket (2,101 rows, 21%), similar to the real extract (20.8%). Plus 114 `Nominated Rajya Sabha`. These are not geographic constituencies, so district/GPS fallback is weaker. | **WARNING** |
| Category | Mirrors the real extract: 9,892 / 10,000 `Normal/Others` (98.9% vs 98.7% real). Rare categories are present but too sparse for category-aware models. | **WARNING** |
| Status / lifecycle | Synthetic: Unsanctioned 51.7%, Sanctioned 25.0%, Completed 15.0%, Ongoing 6.3%. Real: 83.1% / 11.6% / 2.7% / 1.1%. **100% of real Completed and Ongoing works are in this file.** | **WARNING** |
| Sanctioned amount | Present on 4,632 rows (those with a synthetic sanction schedule). Always **equal** to real `allocation_amount`. Median 300,000. | **WARNING** |
| Expenditure | Same 4,632 rows. Median 170,444. NORMAL completed spends ~90–100% of sanctioned (mean 95.2%). COST/MIXED spend above sanctioned. 1,170 rows have expenditure 0 (sanctioned-not-started). | **PASS** (for testing) |
| Planned duration | 4,632 planned spans; median 128 days, IQR 75–189, max 501. Eleven TIME/MIXED rows have 2–14 day plans (generator artifact when overdue schedules are forced). | **WARNING** |

Amount units follow the real extract (unit still unspecified in source). Values are not independent government sanctions; they are copied allocations plus synthetic spend.

---

## 3. Logical realism

| Check | Result | Severity |
| --- | --- | --- |
| `recommended <= sanction <= planned start <= planned completion` | 0 violations (4,632 compared) | **PASS** |
| `actual start <= actual completion` | 0 violations (1,567 compared) | **PASS** |
| `physical_progress_percent` in 0–100 | 0 violations | **PASS** |
| NORMAL / DEMO_CLEAN expenditure `<=` sanctioned | 0 overspend | **PASS** |
| NORMAL / DEMO_CLEAN milestone total `<=` sanctioned | 0 violations | **PASS** |
| NORMAL completed have `actual_completion_date` | 0 missing | **PASS** |
| NORMAL ongoing have no final completion date | 0 leaks | **PASS** |
| Sanctioned amount vs real allocation | Equal whenever sanctioned is filled (4,632 / 4,632) | **WARNING** |
| Milestone internal consistency | `milestone_amount = total // number`. 1,750 / 2,835 rows have `amount * n != total` because of integer remainder; `amount * n <= total` always. | **WARNING** |
| Progress vs lifecycle (NORMAL) | Unsanctioned/blank/Sanctioned = 0; Ongoing mean ~49 (25–70); Completed = 100 | **PASS** |
| TIME_ANOMALY vs real status | 634 / 799 TIME_ANOMALY rows are real **Sanctioned** but have a synthetic `actual_start_date` and 5–18% progress. The real STATUS still says not started. | **WARNING** |
| Zero allocation | 9 real zero-allocation works; 2 COST rows have sanctioned 0 and expenditure 1 (ratio undefined / inf). | **WARNING** |

Unsanctioned emptiness (no sanction/expenditure/milestones on ~5,368 rows) is consistent with the real STATUS and is not a generator bug.

---

## 4. Scenario quality

Counts match the designed mix: NORMAL 6,999 + DEMO_CLEAN 1; COST 999 + DEMO_OVERBILL 1; TIME 799 + DEMO_STUCK 1; OVERLAP 500; GHOST 399 + DEMO_GHOST 1; MIXED 300.

### NORMAL / CLEAN — **PASS** (with one CLEAN-schedule warning)

- No overspend, no overlap group, GPS inside a broad India box, progress aligned with real status.
- **DEMO_CLEAN** (Kadapa, Sanctioned, allocation 3,500,000): expenditure 0, progress 0, dates ordered, AP coordinates. Filter: `demo_case_id=CLEAN`.
- **WARNING:** CLEAN planned start is 2024-06-23 vs sanction 2023-11-16 (~219 days). That gap is a generator “keep sanctioned works from looking overdue” artifact, not a real MPLADS delay.

### OVERBILL / COST — **PASS**

- 1,000 / 1,000 COST+DEMO_OVERBILL rows have expenditure > sanctioned (median ratio ~1.72, IQR ~1.54–1.93, max ~2.15 when sanctioned > 0).
- Milestone totals also exceed sanctioned on these rows.
- **DEMO_OVERBILL** (Eluru, Completed): sanctioned 3,550,000 vs expenditure **6,390,000** (1.80×). Filter: `demo_case_id=OVERBILL`.
- **WARNING:** two completed COST rows with real allocation 0 spend 1 rupee. The cost signal exists but is numerically degenerate.

### STUCK / TIME — **PASS** (signal is clear; status clash is a warning)

- TIME + DEMO_STUCK: planned completion 60–180 days before synthetic as-of 2024-06-30; 871 open overdue cases; non-completed progress 5–18%.
- **DEMO_STUCK** (Anantapur, Ongoing): planned completion 2024-04-11, progress **12%**, expenditure 108,000 / 1,000,000, no completion date. Filter: `demo_case_id=STUCK`.
- **WARNING:** most TIME rows are real **Sanctioned** with a synthetic start. That is a useful Plan-vs-Claim mismatch for engines, but it is not “stuck ongoing work” in the official STATUS sense.

### GHOST / EVIDENCE — **PASS** (location inconsistency is clear)

- 500 ghost-tagged rows (399 EVIDENCE_GHOST + 1 DEMO_GHOST + 100 MIXED): 213 missing GPS, 287 offshore (~lon &lt; 72, Arabian Sea). All have progress 100 and an actual completion date.
- **DEMO_GHOST** (Vizianagaram, Completed): AP work with coordinates **10.05, 68.4**. Filter: `demo_case_id=GHOST`.
- **WARNING:** 64 MIXED ghost rows have real status Sanctioned (49) or Ongoing (15) but synthetic completion + 100% progress. The location signal is still present; the lifecycle signal is mixed.

### MIXED — **PASS**

| `mixed_signals` | n | Independent signals observed |
| --- | ---: | --- |
| `COST_ANOMALY,TIME_ANOMALY` | 100 | 100/100 overspend **and** time overlay |
| `EVIDENCE_GHOST,COST_ANOMALY` | 100 | 100/100 overspend **and** missing (38) or offshore (62) GPS |
| `OVERLAP,COST_ANOMALY` | 100 | 100/100 overspend **and** overlap group id |

### OVERLAP — **PASS** for GPS/vendor clustering; **WARNING** for “full” overlap

- 226 groups, size 2–4 (no singletons), 100% shared vendor, max pairwise distance **0.29 km** (mean 0.13 km).
- **WARNING:** 349 / 500 OVERLAP-only rows are Unsanctioned with empty dates and amounts. Overlap here is **location + vendor only**, not amount/date overlap. Fine for a GPS-proximity test; weak for a multi-signal overlap engine.

---

## 5. Leakage risk

If a future model is trained to predict `scenario_type` (or “anomaly vs normal”) from this table, several columns **are the answer**. That is **CRITICAL** for feature hygiene, not a reason to discard the file as an evaluation set.

| Field | Why it leaks | Severity if used as a feature |
| --- | --- | --- |
| `scenario_type` | Direct label (`NORMAL`, `COST_ANOMALY`, `DEMO_*`, …) | **CRITICAL** |
| `demo_case_id` | Direct demo identity (`GHOST` / `OVERBILL` / `STUCK` / `CLEAN`) | **CRITICAL** |
| `mixed_signals` | Direct multi-label (`COST_ANOMALY,TIME_ANOMALY`, …) | **CRITICAL** |
| `anomaly_notes` | Empty on all 6,999 NORMAL rows; nonempty on every non-NORMAL row. Text also names the scenario. | **CRITICAL** |
| `overlap_group_id` | Nonempty iff OVERLAP or MIXED-overlap (600 rows). Perfect overlap indicator. | **CRITICAL** |
| `coordinate_source` | Default text on 9,500 rows; ghost-specific wording on all 500 ghost-tagged rows (`missing GPS` / `offshore` / `DEMO_GHOST`). | **CRITICAL** |
| `synthetic_disclaimer`, `record_mode`, `enrichment_source`, `synthetic_as_of_date` | Constants (no class split) | not a class leak; still not operational MPLADS fields |

**Constructed-target tautology (WARNING, not hidden leakage):**

- COST is almost exactly `expenditure_amount > sanctioned_amount`.
- TIME is almost exactly “planned completion before 2024-06-30 and low progress”.
- GHOST is almost exactly “completed-style progress with missing or lon &lt; 72 GPS”.

Those are the **intended test signals** for engines. They must not be treated as independent labels plus independent features in the same supervised model.

Vendor / district / agency strings all contain `SYNTHETIC` by design. That does not encode the scenario class (all 10,000 rows are marked).

---

## 6. Accidental artifacts

| Artifact | Detail | Severity |
| --- | --- | --- |
| Formulaic vendors | Names are `SYNTHETIC {place} {trade} {Contractor\|Constructions\|Agency}` with almost equal suffixes (3,347 / 3,299 / 3,354). Top names repeat tens of times in a few UP districts. | **WARNING** |
| Sanctioned ≡ allocation | No independent sanction variation. Cost tests are spend-vs-allocation, not sanction-vs-recommendation. | **WARNING** |
| Discrete progress spikes | 7,124 rows at 0%; 1,567 at 100%; TIME stuck in a 5–18 band. | **WARNING** (expected from rules) |
| Impossible / offshore GPS | Non-ghost: 0 missing, 0 outside a broad India box, 0 at (0,0). Ghost offshore points are **intentional**. DEMO_GHOST is a repeated (10.05, 68.4) pair. | **PASS** with intended ghost exception |
| Duplicated scenarios on one work | None (1:1) | **PASS** |
| Features that directly encode scenario | See section 5 | **CRITICAL** (exclude) |
| Short TIME plans | 11 rows with 2–14 day planned duration after overdue rewriting | **WARNING** |
| RS constituencies used as place | 2,215 Sitting/Nominated Rajya Sabha rows still get district/GPS from IDA or state centroid | **WARNING** |

No CRITICAL geographic values on NORMAL/COST/TIME/OVERLAP rows.

---

## Issue register

| ID | Topic | Severity | Notes |
| --- | --- | --- | --- |
| R1 | 1:1 real link; `real_*` exact | **PASS** | Safe join on `internal_project_id` |
| R2 | Real files unmodified | **PASS** | SHA-256 matches provenance |
| D1 | Status mix ≠ real MPLADS mix | **WARNING** | All completed/ongoing included on purpose |
| D2 | UP oversample; RS constituencies | **WARNING** | Do not cite as national MPLADS geography |
| D3 | Category ~99% Normal/Others | **WARNING** | Same limitation as the real extract |
| L1 | Date order and progress bounds | **PASS** | |
| L2 | TIME vs real Sanctioned status | **WARNING** | Synthetic start vs official STATUS |
| L3 | Milestone remainder | **WARNING** | Integer division; do not use `amount * n` as total |
| L4 | Sanctioned always = allocation | **WARNING** | |
| S1 | NORMAL/CLEAN consistency | **PASS** | CLEAN has a long sanction-to-start gap |
| S2 | COST/OVERBILL overspend | **PASS** | Two zero-allocation degenerate rows |
| S3 | STUCK/TIME delay | **PASS** | Clear vs as-of date |
| S4 | GHOST location inconsistency | **PASS** | 64 MIXED rows clash with real STATUS |
| S5 | MIXED dual signals | **PASS** | 100/100/100 |
| S6 | OVERLAP clusters | **PASS** | Weak on unsanctioned (no dates/amounts) |
| K1 | Direct label columns | **CRITICAL** | Must not be model inputs |
| A1 | Template vendor names | **WARNING** | |

---

## Safe for model testing

**Yes, for controlled testing and evaluation — not as a stand-in for real MPLADS statistics.**

Safe uses:

- Engine tests: cost (spend vs sanctioned/allocation), time (slippage vs `synthetic_as_of_date`), overlap (GPS proximity + shared vendor), evidence (missing/implausible GPS).
- Join tests: enrichment ⨝ cleaned extract on `internal_project_id`.
- Demo walkthroughs via `demo_case_id` ∈ {GHOST, OVERBILL, STUCK, CLEAN}.
- Held-out **evaluation labels** (`scenario_type`, `mixed_signals`, `demo_case_id`) stored separately from features.

Not safe uses:

- Estimating real MPLADS status, duration, expenditure, or district/vendor distributions.
- Training a supervised “fraud” or scenario classifier on this table with label columns left in the feature set (forbidden by project governance anyway: no legal fraud probability; D003).
- Treating synthetic GPS/district/vendor as official MPLADS values.

---

## Must be excluded from model features

Never feed these columns as predictors if the target is scenario, investigation priority derived from this mix, or “anomaly vs normal”:

1. `scenario_type`
2. `demo_case_id`
3. `mixed_signals`
4. `anomaly_notes`
5. `overlap_group_id` (evaluation key for overlap tests only)
6. `coordinate_source` (ghost wording is a perfect GHOST indicator)

Also keep out of operational feature stores (constants / governance, not measurements):

- `synthetic_disclaimer`
- `record_mode`
- `enrichment_source`
- `synthetic_as_of_date` (use as a clock parameter, not a learned feature)
- `synthetic_record_id` (row id, not a work attribute)

**Allowed operational-style inputs** (still SYNTHETIC, still labelled): `real_*` observed fields, synthetic dates, `sanctioned_amount`, `expenditure_amount`, milestone amounts, `physical_progress_percent`, `latitude` / `longitude`, `implementing_district`, `implementing_agency`, `vendor_name`, `project_area`.

Evaluation should compare engine outputs to held-out `scenario_type` / `demo_case_id`, and should remain explainable evidence — not a legal fraud probability.

---

## Tests

Existing backend tests were run after this audit (read-only). All passed, including `tests/test_synthetic_enrichment.py` against this CSV.

No datasets, generators, or engines were changed.
