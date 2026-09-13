# Synthetic enrichment schema

Layer: **SYNTHETIC HYBRID** prototype records in `data/synthetic/sarvsakshi_synthetic_enrichment.csv`.

This is not an official MPLADS schema. It is not loaded into the SQLite `project` table. Real observed fields use the `real_` prefix. Generated enrichment fields are marked SYNTHETIC in values and/or in this document.

Link to a real work: `internal_project_id` (SARVSAKSHI surrogate). Do not invent official MPLADS work IDs.

## Governance

| Field | Type | Kind | Meaning |
| --- | --- | --- | --- |
| `synthetic_record_id` | string | synthetic identity | Unique enrichment key `synthetic:enr:{seed}:{nnnnnn}`. Not an official MPLADS ID. |
| `internal_project_id` | string | real identity | Copy of the real cleaned-work surrogate. Join key to `mplads_works_cleaned.csv` / `project.internal_project_id`. |
| `record_mode` | string | governance | Always `HYBRID`. |
| `enrichment_source` | string | governance | Always `SYNTHETIC`. |
| `synthetic_as_of_date` | date | synthetic | Prototype clock used for overdue vs in-plan schedules (`2024-06-30`). |
| `scenario_type` | string | synthetic | Prototype mix label. Not a legal finding. |
| `demo_case_id` | string | synthetic | `GHOST` / `OVERBILL` / `STUCK` / `CLEAN` for the four controlled demo rows; otherwise empty. |
| `mixed_signals` | string | synthetic | Comma-separated signals when `scenario_type=MIXED`. |
| `overlap_group_id` | string | synthetic | Shared `synthetic:overlap:{seed}:{nnnn}` for OVERLAP / mixed-overlap clusters. |
| `anomaly_notes` | string | synthetic | Human-readable prototype note. Empty on NORMAL rows. |
| `synthetic_disclaimer` | string | governance | Required disclaimer on every row. |

## Real observed snapshot (`real_*`)

Copied from the cleaned extract for the linked work. These are **not** invented. Blank means the real cell was blank.

| Field | Type | Source cleaned column |
| --- | --- | --- |
| `real_state` | string | `state` |
| `real_constituency` | string | `constituency` |
| `real_category` | string | `category` |
| `real_work_description` | string | `work_description` |
| `real_allocation_amount` | integer | `allocation_amount` |
| `real_recommended_date` | date | `recommended_date` |
| `real_status` | string | `status` |
| `real_lifecycle_stage` | string | `lifecycle_stage` |
| `real_ida` | string | `ida` |
| `real_city` | string | `city` |
| `real_block` | string | `block` |
| `real_village` | string | `village` |
| `real_mp_name` | string | `mp_name` |
| `real_house` | string | `house` |

## Synthetic enrichment fields

None of these are official MPLADS values. Empty when the real status does not justify a schedule (typically Unsanctioned / blank status).

| Field | Type | Meaning |
| --- | --- | --- |
| `implementing_district` | string | SYNTHETIC place derived from real IDA text, else constituency/state. Always tagged `[SYNTHETIC]`. |
| `implementing_agency` | string | SYNTHETIC unit attached to the real IDA string. |
| `vendor_name` | string | SYNTHETIC vendor named from place + work-type keywords in the real description. |
| `sanction_date` | date | SYNTHETIC, `>= real_recommended_date`. Empty when unsanctioned. |
| `planned_start_date` | date | SYNTHETIC, `>= sanction_date`. |
| `planned_completion_date` | date | SYNTHETIC, `>= planned_start_date`. |
| `actual_start_date` | date | SYNTHETIC; present for ongoing/completed (and some time-anomaly) rows. |
| `actual_completion_date` | date | SYNTHETIC; normally present for completed, empty for ongoing. |
| `sanctioned_amount` | integer | SYNTHETIC; taken from real `allocation_amount` when a sanction schedule exists. |
| `expenditure_amount` | integer | SYNTHETIC. NORMAL: `<= sanctioned_amount`. COST/OVERBILL: may exceed it. |
| `latitude` | float | SYNTHETIC approximate point from state/constituency. Not official GPS. |
| `longitude` | float | SYNTHETIC approximate point from state/constituency. Not official GPS. |
| `coordinate_source` | string | States that coordinates are SYNTHETIC, not official GPS. |
| `project_area` | string | SYNTHETIC site text from village/block/city/constituency + work type. |
| `physical_progress_percent` | integer | 0–100. Unsanctioned/sanctioned NORMAL: 0. Completed: 100. |
| `milestone_number` | integer | SYNTHETIC current/latest milestone index (1-based). Empty when no schedule. |
| `milestone_amount` | integer | SYNTHETIC amount for that milestone. |
| `milestone_total_amount` | integer | SYNTHETIC sum of paid milestones. NORMAL: `<= sanctioned_amount`. |

## `scenario_type` values

| Value | Prototype meaning |
| --- | --- |
| `NORMAL` | Internally consistent enrichment. |
| `COST_ANOMALY` | Expenditure and/or milestone total exceed sanctioned amount. |
| `TIME_ANOMALY` | Overdue / low-progress / late-completion schedule. |
| `OVERLAP` | Shared nearby SYNTHETIC coordinates and vendor with other rows. |
| `EVIDENCE_GHOST` | Completed claim with missing or implausible coordinates. |
| `MIXED` | Two of the above signals. |
| `DEMO_CLEAN` | Controlled clean demo row. |
| `DEMO_OVERBILL` | Controlled cost demo row. |
| `DEMO_STUCK` | Controlled time demo row. |
| `DEMO_GHOST` | Controlled evidence demo row. |

## Constraints

Hard (generator bugs if broken):

- Unique `synthetic_record_id`
- One synthetic row per selected `internal_project_id`
- Every `internal_project_id` exists in the real cleaned extract
- `record_mode=HYBRID`, `enrichment_source=SYNTHETIC`
- Date order when both dates exist
- `physical_progress_percent` in 0–100
- NORMAL / `DEMO_CLEAN`: expenditure and milestone totals `<= sanctioned_amount`
- NORMAL completed: `actual_completion_date` present
- NORMAL ongoing and `DEMO_STUCK`: no `actual_completion_date`

Intended prototype signals (not bugs): COST overspend, TIME overdue, GHOST GPS gaps, OVERLAP clusters.
