# Time Intelligence V1 report

Date: 2026-09-10  
Engine: `time-peer-v1`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID schedules: `data/synthetic/` only, labelled HYBRID/TEST

This engine measures **Time Anomaly**: schedule and progress timing versus a plan and comparable works, when those dates exist. It does **not** measure a legal finding, expenditure delay, or fused Investigation Priority.

Cost Intelligence V1.1 is frozen and was not modified.

---

## Dual mode

| Mode | Inputs | What is scored |
| --- | --- | --- |
| **REAL** | Observed `recommended_date` + `status` / lifecycle only | No planned/actual duration. No slippage. Time Anomaly score is **not** produced. Recommendation vintage versus same-status peers is context only. |
| **HYBRID_TEST** | Synthetic planned/actual dates and `physical_progress_percent` | Closed: planned vs actual duration and finish delay. Open: elapsed time, % of planned time consumed, physical vs linear expected progress. Outputs are labelled HYBRID/TEST. |

The real extract has **no** verified sanction, start, completion, expenditure, or duration. Duration is never fabricated from recommendation date.

Synthetic dates are **not** actual MPLADS execution history and must not be cited as real delay statistics.

`scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, and `coordinate_source` are excluded from model inputs. Held-out labels are attached only after scoring.

---

## Peer strategy

Same constituency-first ladder as Cost V1.1 (D016):

1. Same geographic constituency + same category + similar work title  
2. Same geographic constituency + broader category  
3. Same Andhra Pradesh state + same category + similar work title  
4. Same Andhra Pradesh state + broader comparable work title  

Skipped when the constituency is blank or a house/chamber label. MP name is not a geography key. Minimum 5 usable peers for a peer **scope**. Peers are never fabricated.

REAL peers also require the same observed status and a recommendation date.  
HYBRID peers must share the same date family (open vs closed) and a positive planned duration. Closed peers also need a positive actual duration.

HYBRID can still score against the **own plan** when peers are insufficient. REAL cannot score without execution dates, even with peers.

---

## Score formula

Score is produced only when sufficient timing evidence exists (HYBRID_TEST with a valid planned duration > 0). Range 0–100. Review flag 60. Early / on-plan maps to 0. Only the late / behind-schedule direction contributes.

**Closed (actual completion present):**

\[
\mathrm{delay} = \max(0,\ \mathrm{actual\ duration} - \mathrm{planned\ duration},\ \mathrm{actual\ completion} - \mathrm{planned\ completion})
\]

\[
\mathrm{plan\ score} = \min\left(100,\ \mathrm{round}(100 \cdot \mathrm{delay} / \mathrm{planned\ duration})\right)
\]

If plan score is 0, Time Anomaly is 0 (on plan is not a delay). If 5+ closed peers exist, blend 60% plan + 40% late-only peer duration modified-z.

**Open (no actual completion):**

\[
\mathrm{time\ consumed} = 100 \cdot \max(0,\ \mathrm{elapsed}) / \mathrm{planned\ duration}
\]

Expected progress = \(\min(100,\ \mathrm{time\ consumed})\) — a **linear** mapping, not a construction S-curve.

Mismatch score: 80 percentage points behind (time consumed − physical progress) maps to 100. Example: 70% of planned time consumed, 20% physical progress → mismatch 50 → score 62, flagged.

Overdue days past planned completion (while progress < 100) map the same way as closed delay. Own score = max(mismatch, overdue). Optional 70/30 blend with peer mismatch when 5+ open peers exist.

Invalid date order (negative duration, completion before start) → no score.

---

## Legitimate context

Delay is not automatically treated as suspicious. V1 has no verified contextual explanations (weather, land, utilities, etc.). When a delay is measured:

**Delay detected; cause not established from available data.**

Future recorded context codes can be attached without changing the score mapping.

---

## Evidence Confidence

Separate from Time Anomaly.

- REAL: capped at 25. Recommendation date + status are weak timing evidence.  
- HYBRID_TEST: capped at 72 because dates are SYNTHETIC, not government execution truth.  
- Invalid dates: 0.  
- Missing recommended date in REAL: 0.

---

## Validation

All **175** backend tests passed, including:

- real-data mode with recommendation date + status only  
- missing execution dates (no fabricated duration)  
- valid planned/actual dates  
- negative duration  
- completion before start  
- ongoing progress mismatch (70/20)  
- completed delay  
- normal schedule  
- severe delay  
- insufficient peers  
- fallback peer scope  
- score monotonicity  
- evidence confidence  
- explanation correctness (WHY FLAGGED / WHY NOT FLAGGED / INCONCLUSIVE)  
- hybrid label leakage  

---

## 10 examples (5 REAL, 5 HYBRID/TEST)

HYBRID `scenario_type` / `demo_case_id` were attached **after** scoring.

### Real

| Project | Dataset | Status | Time mode | Peer scope | n | Planned dur. | Actual dur. | Slippage | Progress | Time Anomaly | Evidence Confidence |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: |
| 217 Hindupur crematorium | REAL | Unsanctioned | REAL | constituency + broader category | 61 | — | — | — | — | — | 16 |
| 4744 Guntur roads | REAL | Sanctioned | REAL | AP state + category + title | 22 | — | — | — | — | — | 18 |
| 21192 Araku mobile sanitation | REAL | Ongoing | REAL | none | 0 | — | — | — | — | — | 12 |
| 5263 Ongole roads | REAL | Completed | REAL | AP state + category + title | 37 | — | — | — | — | — | 18 |
| 846 Sitting RS water tankers | REAL | Unsanctioned | REAL | none | 0 | — | — | — | — | — | 12 |

217 explanation (inconclusive): Recommendation 2024-03-03; vintage versus 61 same-status Hindupur works is context only. No execution dates. Duration not fabricated.

21192 explanation (inconclusive): Observed Ongoing, but start/completion dates are absent. Fewer than 5 same-status title/category peers after the ladder.

846 explanation (inconclusive): `Sitting Rajya Sabha` is a chamber label, not geographic constituency. No Time Anomaly score.

### HYBRID/TEST

| Project | Dataset | Status | Time mode | Peer scope | n | Planned dur. | Actual / elapsed | Slippage | Progress | Time Anomaly | Evidence Confidence | Held-out label |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| 52862 DEMO_STUCK Anantapur rooms | HYBRID | Ongoing | HYBRID_TEST | constituency + broader category | 20 | 222 | elapsed 302 | 80 | 12% | **93** | 46 | STUCK |
| 26946 DEMO_CLEAN Kadapa culverts | HYBRID | Sanctioned | HYBRID_TEST | none | 0 | 184 | elapsed 7 | 0 | 0% | 5 | 48 | CLEAN |
| 22177 DEMO_OVERBILL Eluru lift irrigation | HYBRID | Completed | HYBRID_TEST | none | 0 | 249 | actual 185 | −60 | 100% | 0 | 56 | OVERBILL |
| 53637 DEMO_GHOST Vizianagaram prosthetics | HYBRID | Completed | HYBRID_TEST | constituency + broader category | 6 | 165 | actual 162 | 6 | 100% | 34 | 46 | GHOST |
| 5460 TIME_ANOMALY Guntur boundary wall | HYBRID | Sanctioned | HYBRID_TEST | none | 0 | 45 | elapsed 120 | 75 | 14% | **100** | 56 | TIME_ANOMALY |

52862 explanation (why flagged): 136% of planned time consumed, 12% physical progress, 80 days past planned completion. Score 93. Delay detected; cause not established from available data. HYBRID/TEST only.

26946 explanation (why not flagged): 3.8% of planned time consumed, 0% progress, not overdue. Score 5. Linear mapping is aligned. Not a real MPLADS delay statistic.

22177 explanation (why not flagged): Completed 60 days earlier than planned duration. Time engine does not score the OVERBILL expenditure signal (that is Cost Intelligence).

5460 explanation (why flagged): 266.7% of a 45-day synthetic plan consumed, 14% progress. Score 100. Held-out TIME_ANOMALY label was not a model input. Short planned spans are a known generator artifact, not a real MPLADS duration.

---

## Remaining limitations

- Real works cannot support schedule slippage, expected completion, or execution-duration peer comparison  
- Observation clock for REAL vintage is the extract download date (2026-09-09), not a completion date  
- HYBRID dates are SYNTHETIC; Evidence Confidence is capped  
- Expected progress is linear, not an engineering model  
- State fallback is Andhra Pradesh only  
- No verified delay-cause context in current data  
- This slice does not implement Overlap, Compliance, Risk Fusion, Relationship Graph, Copilot, frontend, citizen, milestone, or satellite
