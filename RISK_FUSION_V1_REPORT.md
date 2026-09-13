# Risk Fusion V1 report

Date: 2026-09-10  
Engine: `risk-fusion-v1`  
HTTP: `GET /api/v1/projects/{id}/risk`  
Baseline: 56,138 real SQLite `project` rows  
HYBRID layer: `data/synthetic/` only, labelled HYBRID/TEST

This engine **consumes Evidence Objects** from Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, and Compliance Engine V1. It produces **Investigation Priority** and **Evidence Confidence**. It does **not** determine fraud, does not output a fraud probability, and does not change those engines’ scores.

Cost V1.1, Time V1, Overlap V1, Compliance V1, and Evidence Object V1 remain frozen.

---

## Exact formula

Weights below are **prototype weights only. They are not official MoSPI weights.**

### Investigation Priority

Let \(s_i \in [0,100]\) be the assessable risk score of signal \(i\), and \(w_i\) its planned weight.

\[
\mathrm{IP} = \mathrm{clip}_{[0,100]}\left(\mathrm{round}\left(\sum_{i \in \mathcal{A}} w_i \cdot s_i\right)\right)
\]

\(\mathcal{A}\) is the set of **assessable** integrated signals (disposition `WHY_FLAGGED` or `WHY_NOT_FLAGGED` with a usable score). Rounding is non-negative half-up (`int(x + 0.5)`), then clipped to 0–100.

Unavailable, `NOT_ASSESSABLE`, `INCONCLUSIVE`, and not-yet-integrated slots contribute **0** and **their weights are not redistributed**.

Theoretical V1 maximum: \(0.70 \times 100 = 70\), because 30% is reserved and unused.

### Evidence Confidence (separate)

\[
C_{\mathrm{cov}} = \frac{\sum_{i \in \mathcal{A}} w_i}{0.70},\quad
C_{\mathrm{qual}} = \frac{\sum_{i \in \mathcal{A}} w_i \cdot c_i}{\sum_{i \in \mathcal{A}} w_i},\quad
C_{\mathrm{ind}} = \frac{|\mathcal{A}|}{4}
\]

\(c_i\) is the Evidence Object confidence in \([0,1]\). If Cost supplies `peer_quality`, \(c_i = 0.70 \cdot \mathrm{confidence} + 0.30 \cdot (\mathrm{peer\_quality}/100)\).

\[
\mathrm{EC}_{\mathrm{raw}} = 100 \cdot \bigl(0.40\,C_{\mathrm{cov}} + 0.35\,C_{\mathrm{qual}} + 0.15\,C_{\mathrm{ind}} + 0.10 \cdot 0\bigr)
\]

The \(0.10 \cdot 0\) term is the reserved 30% (always unavailable in V1). It is documented, not silently dropped.

Mode caps: REAL 90, HYBRID 72, SYNTHETIC 55.

If no assessable signal exists, EC uses a small fraction of `NOT_ASSESSABLE` object confidences, capped at 18, or 0 if no objects exist.

Investigation Priority is **not** copied into Evidence Confidence. High priority with low confidence is not a highly certain conclusion.

---

## Weights

| Slot | Weight | Source |
| --- | ---: | --- |
| Cost | 25% | Cost Evidence Object `allocation_cost_anomaly` score |
| Schedule | 15% | Time Evidence Object `time_anomaly` score |
| Overlap | 15% | Overlap Evidence Object `potential_overlap` score |
| Compliance | 15% | mapped from compliance evidence (see below) |
| Field evidence | 5% | not yet integrated |
| Relationship graph | 5% | not yet integrated |
| Citizen evidence | 4% | not yet integrated |
| Geospatial | 4% | not yet integrated |
| Image | 4% | not yet integrated |
| Document | 4% | not yet integrated |
| Milestone | 4% | not yet integrated |
| **Total** | **100%** | |

Integrated subtotal 70%. Reserved future subtotal 30%.

Cost, Time, and Overlap scores are used as stored on the Evidence Object. Fusion does not re-run peer selection, embeddings, or guideline rules.

Compliance has no engine 0–100 anomaly score. Fusion maps **evidence fields only**:

- `WHY_NOT_FLAGGED` → 0
- `WHY_FLAGGED` → severity `info` 40 / `watch` 60 / `attention` 80, plus 10 per extra triggered rule ID, capped at +20
- `NOT_ASSESSABLE` / `INCONCLUSIVE` → no score (not treated as low risk)

---

## Handling of unavailable signals

| State | Effect on IP | Effect on EC |
| --- | --- | --- |
| `ASSESSABLE` | \(w_i s_i\) | coverage, quality, independence |
| `NOT_ASSESSABLE` | 0; weight unused | weak presence only if no assessable signals |
| `UNAVAILABLE` (engine not stored) | 0; weight unused | lowers coverage |
| `NOT_YET_INTEGRATED` (future 30%) | 0; never invented | \(0.10 \times 0\) term |

Do **not** interpret unused weight as “the work is clean.” Low evidence and low risk are reported separately.

Example: Cost 72, Overlap 83, Compliance 60 (watch), Time unavailable:

\[
\mathrm{IP} = 0.25\cdot 72 + 0.15\cdot 83 + 0.15\cdot 60 = 39
\]

That is **not** renormalized to ~81. The 15% schedule weight and 30% reserved weight stay unused.

---

## Recommended action

Not a legal or administrative decision.

| Investigation Priority | Band | Action |
| --- | --- | --- |
| 0–24 | LOW | MONITOR |
| 25–44 | MEDIUM | REVIEW |
| 45–59 | HIGH | INSPECT |
| 60–100 | HIGH | INVESTIGATE |

Explanation types: `WHY_FLAGGED`, `WHY_NOT_FLAGGED`, `INCONCLUSIVE`, `INSUFFICIENT_EVIDENCE`.

---

## Data modes

| Mode | Meaning |
| --- | --- |
| REAL | observed MPLADS evidence only |
| HYBRID | observed fields plus synthetic enrichment |
| SYNTHETIC | fully synthetic test records |

Cost V1.1 has no HYBRID-TEST mode. When `data_mode=HYBRID`, REAL Cost evidence may be fused with HYBRID Time/Overlap/Compliance. Cost scores are not modified. The fused result is labelled HYBRID.

Held-out columns are **not** fusion inputs:

`scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, `coordinate_source`

They are attached only after scoring for evaluation.

---

## Duplicate evidence

One Evidence Object per fusion slot. Duplicate `evidence_id` values are dropped. If two objects share a slot, fusion keeps one deterministically (preferred data mode, then lexicographically greater `evidence_id`). Scores are never summed across duplicates.

---

## Architecture

`backend/app/engines/fusion/` consumes stored or in-memory Evidence Objects. HTTP: `GET /api/v1/projects/{id}/risk`.

Response includes `investigation_priority`, `evidence_confidence`, `contributing_signals`, `unavailable_signals`, `explanation`, `recommended_action`, `data_mode`, `evidence_ids`. It does **not** expose a fraud probability.

`fusion_score` stores Investigation Priority and Evidence Confidence (plus V1 payload). Additive columns: `data_mode`, `recommended_action`, `explanation_type`, `payload_json`.

---

## Tests

**326** backend tests passed (0 failed), including prior Cost/Time/Overlap/Compliance/Evidence suites plus Risk Fusion V1:

1. all four signals available  
2. only one signal available  
3. missing signals  
4. `NOT_ASSESSABLE` evidence  
5. low risk  
6. medium risk  
7. high risk  
8. low evidence confidence  
9. conflicting signals  
10. duplicate evidence prevention  
11. deterministic output  
12. bounded 0–100 scores  
13. monotonicity  
14. REAL vs HYBRID distinction  
15. forbidden synthetic-label leakage  
16. explanation correctness  
17. recommendation mapping  
18. unavailable-signal reporting  

```powershell
cd backend
python -m pytest
python -m app.engines.fusion.evaluate_run
```

---

## 10 REAL examples

Schedule is **not assessable** on REAL works (no execution dates). Overlap often flags generic repeated titles; that is a source-text limitation, not a legal duplicate finding. Weights are not renormalized, so a single overlap flag does not become a high Investigation Priority.

| Project | Case | IP | EC | Band | Action | Contributing | Unavailable (integrated) |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| 846 | water tankers | 11 | 40 | LOW | MONITOR | Overlap 75, Compliance 0 | Cost, Schedule |
| 232 | Hindupur roads | 13 | 65 | LOW | MONITOR | Overlap 88, Compliance 0, Cost 0 | Schedule |
| 217 | Hindupur crematorium | 12 | 58 | LOW | MONITOR | Overlap 81, Compliance 0, Cost 0 | Schedule |
| 3348 | Srikakulam halls | 16 | 60 | LOW | MONITOR | Overlap 78, Cost 19, Compliance 0 | Schedule |
| 3715 | Kurnool school rooms | 12 | 58 | LOW | MONITOR | Overlap 47, Cost 21, Compliance 0 | Schedule |
| 21769 | Eluru water tanks | **29** | 62 | MEDIUM | REVIEW | Overlap 81, Cost 67, Compliance 0 | Schedule |
| 5263 | Ongole roads | 15 | 65 | LOW | MONITOR | Overlap 100, Compliance 0, Cost 0 | Schedule |
| 21192 | Araku sanitation | 19 | 65 | LOW | MONITOR | Overlap 97, Cost 19, Compliance 0 | Schedule |
| 233 | Anakapalle borewells | 24 | 65 | LOW | MONITOR | Overlap 79, Cost 50, Compliance 0 | Schedule |
| 234 | Anakapalle multi-gym | 8 | 58 | LOW | MONITOR | Overlap 54, Compliance 0, Cost 0 | Schedule |

21769 (why flagged): Cost 67 from constituency/state water-tank peers plus overlap 81. IP 29 is MEDIUM because unused schedule and reserved weights are not redistributed. Evidence Confidence 62 is separate. Not a legal finding.

3715 (why not flagged): Cost 21 and overlap 47 are below engine review flags; compliance assessable rules were not triggered.

234 (why not flagged): 22% semantic similarity; same constituency/category is not enough for overlap.

Reserved 30% (field, graph, citizen, geospatial, image, document, milestone) is unavailable on every row.

---

## 10 HYBRID evaluation examples

HYBRID `scenario_type` / `demo_case_id` / `mixed_signals` were attached **after** fusion. Synthetic dates, GPS, and expenditure are not official MPLADS values. Evidence Confidence is capped at 72.

| Project | Case | IP | EC | Band | Action | Contributing | Held-out label (after scoring) |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| 23028 | overlap group A | 23 | 65 | LOW | MONITOR | Overlap 72, Cost 49, Compliance 0 | OVERLAP |
| 9982 | overlap group B | 11 | 65 | LOW | MONITOR | Overlap 76, Compliance 0, Cost 0 | OVERLAP |
| 26946 | DEMO_CLEAN | **41** | 71 | MEDIUM | REVIEW | Cost 100, Compliance 60, Overlap 43, Schedule 5 | CLEAN |
| 22177 | DEMO_OVERBILL | 12 | 47 | LOW | MONITOR | Compliance 80, Overlap 0, Schedule 0 | OVERBILL |
| 52862 | DEMO_STUCK | **37** | 72 | MEDIUM | REVIEW | Schedule 93, Overlap 68, Cost 50, Compliance 0 | STUCK |
| 53637 | DEMO_GHOST | **35** | 72 | MEDIUM | REVIEW | Cost 100, Overlap 35, Schedule 34, Compliance 0 | GHOST |
| 46124 | NORMAL | 25 | 65 | MEDIUM | REVIEW | Overlap 73, Cost 55, Compliance 0 | NORMAL |
| 15149 | overlap GPS 119 m | 14 | 65 | LOW | MONITOR | Overlap 91, Compliance 0, Cost 0 | OVERLAP |
| 16180 | MIXED overlap+cost | **26** | 72 | MEDIUM | REVIEW | Overlap 93, Compliance 80, Cost 0, Schedule 0 | MIXED `OVERLAP,COST_ANOMALY` |
| 25533 | COST_ANOMALY | **26** | 72 | MEDIUM | REVIEW | Overlap 93, Compliance 80, Schedule 2, Cost 0 | COST_ANOMALY |

DEMO_CLEAN can still have a high **allocation** Cost signal: the held-out CLEAN label describes expenditure staying within sanctioned amount. Cost V1.1 compares recorded allocation with Kadapa peers (7× gap). Fusion does not treat the CLEAN label as an input. R003 (watch) also triggered on the synthetic zero-spend clock — HYBRID/TEST only.

DEMO_OVERBILL: Compliance R004 maps to 80 (synthetic spend above sanctioned). Cost V1.1 is allocation-vs-peers and was not assessable. IP 12 remains LOW because unused Cost weight is not redistributed. That is expected, not a claim that over-billing is absent.

DEMO_STUCK: Schedule 93 plus overlap 68 → IP 37 REVIEW. Cause of delay is not established.

COST_ANOMALY / MIXED: Compliance R004 (expenditure vs sanctioned) is the spend signal. Allocation Cost Anomaly can still be 0 when the recorded allocation matches peers.

---

## Synthetic evaluation methodology

1. Run frozen Cost, Time, Overlap, and Compliance engines.  
2. Convert results through existing Evidence Object adapters.  
3. Fuse using only Evidence Object fields.  
4. Attach HYBRID labels **after** scoring.  
5. Do not train a fusion model on scenario labels. There is no supervised fraud classifier.

This is a **controlled test**, not a labelled independent fraud dataset. Do **not** cite precision, recall, or “model accuracy.” Held-out scenario types are generator rules (spend vs sanction, overdue progress, GPS clusters), not legal findings.

---

## Limitations

- Prototype weights are not official MoSPI weights.  
- V1 maximum IP is 70 because 30% is reserved. High Investigation Priority is not fraud.  
- REAL Time Anomaly is not assessable; duration is not fabricated.  
- Overlap V1 often flags generic repeated titles; fusion inherits that review-queue signal.  
- Compliance REAL cannot assess most timeline/spend rules; R015 IDA presence is often the only assessable rule (score 0).  
- Cost V1.1 does not use expenditure; HYBRID overspend appears through Compliance, not Cost.  
- Field, graph, citizen, geospatial, image, document, and milestone evidence are unavailable. No values were invented.  
- No claim of detection accuracy without a properly labelled independent dataset.  
- This slice does not implement Relationship Graph, Digital Passport UI, Plan/Claim/Evidence UI, documents, vision, geo, citizen, milestone, Copilot, or frontend redesign.

STOP. Graph, Passport, Copilot, and frontend were not built in this slice.
