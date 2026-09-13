# SARVSAKSHI synthetic enrichment

This folder is a **SYNTHETIC prototype/testing layer**. It is **not** a government dataset and must not be presented as official MPLADS data.

The 56,138 cleaned works in `data/processed/mplads_works_cleaned.csv` remain the real extract. This layer does not modify, overwrite, or duplicate that file, `data/raw/`, or the SQLite `project` table.

## What this is

Each row is a **HYBRID** enrichment record:

- `record_mode = HYBRID`
- `enrichment_source = SYNTHETIC`
- `internal_project_id` links to one real cleaned work (SARVSAKSHI surrogate, not an official MPLADS ID)
- `synthetic_record_id` is a synthetic key (`synthetic:enr:…`) and is not an official MPLADS ID

Observed real fields are copied with a `real_` prefix so they stay distinguishable from generated enrichment fields (district, agency, vendor, dates, expenditure, coordinates, milestones).

District, agency, vendor, and coordinates are **logically associated** with the real state / constituency / IDA text where possible, and are always marked `SYNTHETIC`. They are not official MPLADS values.

## Files

| File | Purpose |
| --- | --- |
| `sarvsakshi_synthetic_enrichment.csv` | 10,000 HYBRID enrichment records |
| `sarvsakshi_synthetic_enrichment.provenance.json` | Seed, source SHA-256, scenario counts, disclaimer |
| `SCHEMA.md` | Field dictionary for this layer |
| `VALIDATION_REPORT.md` | Last validation run (labels, constraints, samples) |
| `README.md` | This file |

## Regenerate (reproducible)

From `backend/`, with seed `26102`:

```powershell
python -m app.pipeline.synthetic_run
```

Validate only:

```powershell
python -m app.pipeline.synthetic_run --validate-only
```

The same seed against the same cleaned extract produces the same CSV. The generator refuses to write under `data/raw/` or `data/processed/`.

## Prototype scenario mix

These percentages are for prototype testing only. They are **not** fraud labels and are **not** a legal conclusion.

| scenario_type | Count | Share |
| --- | ---: | ---: |
| `NORMAL` + `DEMO_CLEAN` | 7000 | 70% |
| `COST_ANOMALY` + `DEMO_OVERBILL` | 1000 | 10% |
| `TIME_ANOMALY` + `DEMO_STUCK` | 800 | 8% |
| `OVERLAP` | 500 | 5% |
| `EVIDENCE_GHOST` + `DEMO_GHOST` | 400 | 4% |
| `MIXED` | 300 | 3% |
| **Total** | **10000** | 100% |

`MIXED` rows combine two signals in `mixed_signals` (`COST_ANOMALY,TIME_ANOMALY`, `EVIDENCE_GHOST,COST_ANOMALY`, or `OVERLAP,COST_ANOMALY`).

Unsanctioned real works keep empty sanction / expenditure / milestone fields. That missingness is expected, not a generator bug.

## Controlled demo cases

Filter `demo_case_id` for the four SIH demo hosts. All four are Andhra Pradesh real works with SYNTHETIC enrichment.

| demo_case_id | scenario_type | Real status | Real constituency | `internal_project_id` |
| --- | --- | --- | --- | --- |
| `GHOST` | `DEMO_GHOST` | Completed | VIZIANAGARAM | `internal:464569d6e0e8fa677cd826b350df9c2c0bd680a7665587cadd63e93e2b357d29` |
| `OVERBILL` | `DEMO_OVERBILL` | Completed | ELURU | `internal:eab396eafd121f6c8426cb285be2078aa7cfc6fe718050d6eb7340208318e762` |
| `STUCK` | `DEMO_STUCK` | Ongoing | ANANTAPUR | `internal:639b82094c0b023fa8fd1047f88e87a608a92f59442a74bf086ab25d4a2274c5` |
| `CLEAN` | `DEMO_CLEAN` | Sanctioned | KADAPA | `internal:e714d635eb46ac65589489b3972d8cf896f9c2b7baaaeb753bf3e312929fc3b9` |

## Generation rules (short)

- Seed: `26102`
- Synthetic as-of date: `2024-06-30` (aligned with the 2023–24 recommended-work snapshot, not live government time)
- `recommended_date <= sanction_date <= planned_start_date <= planned_completion_date`
- `actual_start_date <= actual_completion_date` when both exist
- Completed NORMAL rows have `actual_completion_date`
- Ongoing NORMAL / STUCK rows do not have a final completion date
- NORMAL expenditure and milestone totals stay `<= sanctioned_amount`
- `physical_progress_percent` is 0–100
- COST / OVERBILL rows intentionally spend above sanctioned amount for prototype tests
- Coordinates are approximate SYNTHETIC points, not surveyed GPS

## Out of scope

This slice does not start Time, Overlap, Compliance, Risk, Graph, Copilot, or frontend work, and does not add synthetic columns to the real `project` table.
