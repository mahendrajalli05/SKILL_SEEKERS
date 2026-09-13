# Risk Fusion V2 report

Date: 2026-09-10  
Engine: `risk-fusion-v2`  
HTTP: `GET /api/v2/projects/{id}/risk`  
V1.1 remains: `GET /api/v1/projects/{id}/risk` (`risk-fusion-v1.1`)

This slice adds **Risk Fusion V2**, the next Investigation Priority layer. It consumes stored Evidence Objects from frozen V1/V1.1 engines. It does **not** determine fraud, does not output a fraud probability, does not sanction a project, and does not release funds.

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1 scoring, Relationship Graph V1, Image Evidence V1, Image Forensics V1, Geospatial V1, Satellite V1, Document/Blueprint V1, Plan→Claim→Evidence V1, Milestone Advisor V1, Jan-Sakshi V1, Need & Impact V1, Investigation Copilot V1 architecture (retrieval/intent/templates only extended for V2).

---

## What V2 adds

V1.1 fused four integrated engines (Cost / Schedule / Overlap / Compliance) and reserved 30% as not-yet-integrated. V2 consumes every Evidence Object that actually exists for the project and:

- maps each object into an explicit catalog group
- discounts correlated representations of the same underlying signal
- keeps Investigation Priority and Evidence Confidence separate
- returns `CONFLICTING_EVIDENCE` when assessable sources disagree
- treats unavailable / not-assessable / low-confidence / negative / positive as distinct states
- recomputes deterministically from the current evidence set and appends an immutable history snapshot

A project with only one weak or even one strong signal does **not** become 100/100. Missing group weights are not redistributed.

---

## 1. Evidence catalog

Prototype design parameters only. **These are not official MoSPI or MPLADS weights.**

| Evidence type | Group | Max weight | Confidence factor | Correlation family |
| --- | --- | ---: | --- | --- |
| `allocation_cost_anomaly` | Cost | 0.14 | object confidence × peer quality when present | independent |
| `time_anomaly` | Time | 0.10 | object confidence | independent |
| `potential_overlap` | Overlap | 0.10 | object confidence | `SEMANTIC_SIMILARITY` |
| `mplads_compliance` | Compliance | 0.10 | object confidence; score mapped from disposition/severity (rules not re-run) | independent |
| `relationship_graph` | Graph | 0.08 | object confidence | `SEMANTIC_SIMILARITY` when strongest relationship is overlap/`SIMILAR_TO` |
| `document` | Document / blueprint | 0.06 | object / extraction confidence | `PLAN_CLAIM_DOC` with PCE |
| `IMAGE_*` (non-forensic) | Image evidence | 0.06 | object confidence | `IMAGE_FAMILY` with forensics when both flagged |
| `IMAGE_FORENSIC_*` | Image forensics | 0.05 | object confidence; AI-generation capped at 50 | `IMAGE_FAMILY` |
| `GEOSPATIAL_*` | Geospatial | 0.08 | object confidence | `LOCATION_FAMILY` (independent sensor vs satellite) |
| `SATELLITE_*` | Satellite | 0.07 | object confidence; availability/inconclusive not scored | `LOCATION_FAMILY` |
| `CITIZEN_*` | Citizen / Jan-Sakshi | 0.06 | object confidence; one report capped at 40, 3+ at 70 | location-driven citizen vs geospatial |
| `milestone` | Milestone | 0.05 | object confidence | `PLAN_CLAIM_PROGRESS` with PCE |
| `plan_claim_evidence` | Plan / claim / evidence | 0.05 | object confidence | PCE family |
| `NEED_*` / `IMPACT_*` / `PRIORITY_*` | Need / impact | **0.00** | not fused | planning score, not investigation risk |

Weights of the 13 investigation groups sum to **1.00**. Need & Impact is catalogued and shown, but high need is not high Investigation Priority.

Only Evidence Objects that exist for the requested data mode are used. Missing groups are not fabricated.

---

## 2. Correlation / double-counting

The score distinguishes **independent corroboration** from **multiple representations of the same evidence**.

| Rule | When | Treatment |
| --- | --- | --- |
| Duplicate `evidence_id` | same object listed twice | dropped |
| Within a group | several image/citizen objects | group score = max mapped score, not a sum |
| Overlap + Graph | graph strongest relationship is `SIMILAR_TO` / overlap-derived | weaker keep-factor **0.25** |
| Overlap + Graph | graph also has a non-overlap independent signal | weaker keep-factor **0.50** |
| Image + Forensics | both flagged | weaker keep-factor **0.50** |
| PCE + Milestone | both assessable | weaker keep-factor **0.30** (Milestone reuses PCE) |
| Document + PCE | PCE assessable | document keep-factor **0.35** |
| Citizen location + Geospatial | both flagged location mismatch | citizen keep-factor **0.40** |
| Geospatial + Satellite | both assessable | **no IP discount** (independent sensors); conflict handled in confidence |

Worked example (the requested case): Overlap = 90, Graph = 95, graph strongest relationship is the same similarity edge. V2 does not treat these as two fully independent 90+/95 signals. The weaker group is kept at 25%.

---

## 3. Investigation Priority formula

Displayed Investigation Priority remains **0–100**.

Let \(s_g \in [0,100]\) be the group mapped score when the group is `ASSESSABLE` or `LOW_CONFIDENCE`.

\[
s_g^{\mathrm{adj}} = s_g \cdot (0.55 + 0.45 \cdot c_g)
\]

\[
\mathrm{contribution}_g = w_g \cdot s_g^{\mathrm{adj}} \cdot k_g
\]

\(c_g\) is group confidence in \([0,1]\). \(k_g\) is the correlation keep-factor (1.00 if independent).

\[
\mathrm{Raw\ Risk} = \sum_g \mathrm{contribution}_g
\]

\[
\mathrm{Investigation\ Priority} = \mathrm{clip}(\mathrm{round}(\mathrm{Raw\ Risk}),\, 0,\, 100)
\]

Missing-signal treatment:

- `UNAVAILABLE`, `NOT_ASSESSABLE`, `INCONCLUSIVE`, and Need/Impact contribute **0**
- their weights are **not** redistributed
- unavailable ≠ zero-risk evidence
- unavailable ≠ suspicious

Bounds:

- Cost = 100 only, \(c=1\), others missing → IP ≈ \(0.14 \times 100 = 14\) (not 100)
- All investigation groups = 100 and independent → IP = 100
- No assessable groups → IP = 0, explanation `INSUFFICIENT_EVIDENCE`

Mapped scores for engines that do not emit a 0–100 anomaly score (compliance, many image/geo/satellite/citizen/PCE/milestone objects) are **prototype fusion mappings from disposition and signal type**. They do not change those engines.

---

## 4. Evidence Confidence

Evidence Confidence is **not** the average of source scores.

\[
\begin{aligned}
\mathrm{EC}_{raw} = 100 \cdot (
  &0.25 \cdot \mathrm{coverage} +
  0.20 \cdot \mathrm{quality} +
  0.20 \cdot \mathrm{independence} + \\
  &0.15 \cdot \mathrm{extraction} +
  0.10 \cdot \mathrm{reliability} +
  0.10 \cdot \mathrm{completeness}
) \\
\mathrm{EC}_{raw} &\leftarrow \mathrm{EC}_{raw} \cdot (0.25 + 0.75 \cdot \mathrm{quality}) \\
\mathrm{EC}_{raw} &\leftarrow \mathrm{EC}_{raw} \cdot (1 - 0.18 \cdot n_{conflicts}) \quad \text{if conflicts}
\end{aligned}
\]

Then clip to 0–100 and cap by data mode: REAL 92, HYBRID 74, SYNTHETIC 56. No assessable groups cap at 20.

| Term | Meaning |
| --- | --- |
| coverage | assessable investigation groups / 13 |
| quality | weight-mean of group confidences |
| independence | distinct correlation families among assessable groups; bonus if two independent groups are flagged |
| extraction | mean object confidence, blended with peer quality when present |
| reliability | REAL 1.00 / HYBRID 0.80 / SYNTHETIC 0.55 |
| completeness | available investigation weight / 1.00 |
| quality gate | low extraction confidence cannot produce high EC |

---

## 5. Conflicting evidence

If two assessable groups in a documented pair have opposite polarity, V2 returns **`CONFLICTING_EVIDENCE`**. It does not force a single conclusion. Confidence is lowered. Both contributions remain visible.

Documented pairs include citizen vs milestone / PCE / satellite, milestone vs satellite, PCE vs satellite, and geospatial vs satellite.

Example: citizen reports incomplete + milestone indicates complete + satellite inconclusive → `CONFLICTING_EVIDENCE` (citizen vs milestone). Satellite stays inconclusive, not suspicious.

---

## 6. Missing-data states

| State | Meaning | IP effect |
| --- | --- | --- |
| `UNAVAILABLE` | no Evidence Object for the group | 0; not suspicious |
| `NOT_ASSESSABLE` | object exists; engine could not assess | 0; not low risk |
| `INCONCLUSIVE` | insufficient engine evidence | 0; not low risk |
| `LOW_CONFIDENCE` | assessable but \(c_g < 0.30\) | contributes, reduced by confidence |
| `NEGATIVE_SIGNAL` | `WHY_FLAGGED` / mismatch | contributes |
| `POSITIVE_SIGNAL` | `WHY_NOT_FLAGGED` / consistent | contributes (usually near 0) |
| `NOT_USED_FOR_INVESTIGATION` | Need & Impact planning score | 0 |

---

## 7. REAL / HYBRID / SYNTHETIC

The V2 result retains `data_mode`.

- REAL never consumes HYBRID/SYNTHETIC objects.
- HYBRID prefers HYBRID objects and includes REAL Cost (Cost V1.1 has no HYBRID-TEST mode).
- If a major contribution (≥ 5 effective points) relies on SYNTHETIC or HYBRID evidence, the explanation discloses that. Synthetic results are not government findings.

---

## 8. Explanation

Every result answers **WHY?** in officer language, for example:

Investigation Priority: 78/100  
Evidence Confidence: 74/100  
Top contributing evidence groups: Cost; Compliance; Geospatial  
Correlated evidence discounted: Graph/Overlap shared semantic signal  
Unavailable: verified execution history; full expenditure history; satellite  
Recommendation: INSPECT  

It does not say “fraud detected”.

The contribution breakdown exposes, for every group:

- signal / group
- raw evidence score
- confidence
- effective contribution
- dependency/correlation adjustment
- source / evidence IDs

---

## 9. Temporal updates and officer decisions

V2 recomputes from the **current** evidence set. Historical Evidence Objects are not mutated.

Tables:

- `fusion_score_v2` — latest result per `(project_id, data_mode)`
- `fusion_score_v2_history` — append-only snapshots (`evidence_fingerprint`, payload, scores)

V1.1 `fusion_score` is not overwritten.

Officer decisions remain `CONFIRM CONCERN` / `DISMISS` / `NEED MORE INFORMATION`. They snapshot V1.1 and V2 scores and must not change them.

---

## 10. Thresholds and recommendation

Prototype bands on displayed Investigation Priority. **Not official government thresholds.**

| Investigation Priority | Band |
| ---: | --- |
| 0–24 | LOW |
| 25–44 | MEDIUM |
| 45–100 | HIGH |

Recommendations:

| Condition | Action |
| --- | --- |
| no assessable groups | NEED MORE INFORMATION |
| Evidence Confidence < 28 | NEED MORE INFORMATION |
| IP ≥ 45 and Evidence Confidence < 40 | NEED MORE INFORMATION |
| IP ≤ 24 | MONITOR |
| IP 25–44 | REVIEW |
| IP ≥ 45 with adequate confidence | INSPECT |

High priority + low confidence is conservative: **NEED MORE INFORMATION**, not a highly certain conclusion. There is no automatic sanction and no automatic payment.

---

## 11. API

`GET /api/v2/projects/{id}/risk?data_mode=REAL|HYBRID|SYNTHETIC`

Returns Investigation Priority, Evidence Confidence, `risk_class`, recommendation, contributing / independent / discounted / unavailable / not-assessable / conflicting groups, evidence IDs, data mode, explanation, fingerprint.

`GET /api/v1/projects/{id}/risk` remains Risk Fusion V1.1.

---

## 12. Frontend and Copilot

Investigation Workspace shows V2: Investigation Priority, Evidence Confidence, WHY?, contribution breakdown, independent vs correlated evidence, conflicting evidence, unavailable evidence, recommendation.

Passport still shows V1.1 Risk display. The rest of the application was not redesigned.

Copilot was not rebuilt. Retrieval now includes the V2 snapshot (`persist=False` unless already stored). New intents:

- “Why is the new score higher?”
- “Which evidence contributed most?”
- “Which evidence was discounted as correlated?”
- “What evidence is conflicting?”

---

## 13. V1.1 vs V2 (same evaluation projects)

V1.1 display IP = Raw Risk / 0.70 over four engines. V2 does not rescale the large unavailable field/image/geo/satellite/citizen/milestone mass onto 0–100. On REAL works that only have Cost/Overlap/Compliance/Graph, V2 Investigation Priority is therefore **lower** than V1.1 display IP. That is intended: missing field evidence is a coverage gap, not a silent 100.

| Project | Mode | V1.1 IP (report) | V2 IP | V2 EC | V2 top groups | V2 discounted | V2 recommendation |
| ---: | --- | ---: | ---: | ---: | --- | --- | --- |
| 846 | REAL | 16 | 9 | 25 | Overlap, Graph | Graph | NEED MORE INFORMATION |
| 232 | REAL | 19 | 11 | 35 | Overlap, Graph | Graph | MONITOR |
| 21769 | REAL | 41 | 16 | 31 | Cost, Overlap, Graph | Graph | MONITOR |
| 26946 | HYBRID | 59 | 20 | 30 | Cost, Compliance | Graph | MONITOR |
| 52862 | HYBRID | 52 | 23 | 37 | Time, Graph, Cost | Overlap | MONITOR |
| 22177 | HYBRID | 17 | 6 | 18 | Compliance | none | NEED MORE INFORMATION |

No accuracy claim is made. There is no independent labelled investigation dataset.

---

## 14. Evaluation (15 REAL + 15 HYBRID)

Held-out `scenario_type` / `demo_case_id` were attached **after** fusion. Field/image/citizen/milestone objects were not present on these rows, so they are listed unavailable (not suspicious). Graph vs Overlap correlation fired on most overlap-heavy titles.

### REAL

| Project | Case | Priority | Confidence | Top groups | Discounted | Conflicting | Unavailable (abbrev.) | Rec. |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 846 | water tanks | 9 | 25 | Overlap 75, Graph 74 | Graph | none | doc/image/geo/sat/citizen/milestone/PCE | NEED MORE INFORMATION |
| 232 | roads | 11 | 35 | Overlap 88, Graph 100 | Graph | none | same | MONITOR |
| 217 | with place | 9 | 26 | Overlap 81, Graph 66 | Graph | none | same | NEED MORE INFORMATION |
| 3348 | repair | 12 | 28 | Graph 100, Overlap 78, Cost 19 | Overlap | none | same | MONITOR |
| 3715 | Kurnool | 6 | 23 | Overlap 47, Cost 21 | none | none | same | NEED MORE INFORMATION |
| 21769 | Eluru high amount | 16 | 31 | Cost 67, Overlap 81, Graph 32 | Graph | none | same | MONITOR |
| 5263 | completed | 12 | 35 | Overlap 100, Graph 100 | Graph | none | same | MONITOR |
| 21192 | ongoing | 14 | 35 | Overlap 97, Graph 100, Cost 19 | Graph | none | same | MONITOR |
| 233 | extra | 16 | 35 | Overlap 79, Cost 50, Graph 97 | Graph | none | same | MONITOR |
| 234 | extra | 5 | 23 | Overlap 54 | none | none | same | NEED MORE INFORMATION |
| 855 | extra | 9 | 25 | Overlap 75, Graph 74 | Graph | none | same | NEED MORE INFORMATION |
| 875 | extra | 7 | 28 | Overlap 75, Graph 67 | Graph | none | same | MONITOR |
| 1037 | extra | 11 | 35 | Overlap 96, Graph 98 | Graph | none | same | MONITOR |
| 1038 | extra | 14 | 35 | Overlap 96, Graph 98, Cost 22 | Graph | none | same | MONITOR |
| 1065 | extra | 11 | 35 | Overlap 86, Graph 100 | Graph | none | same | MONITOR |

### HYBRID

| Project | Case | Priority | Confidence | Top groups | Discounted | Conflicting | Rec. | Held-out label |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- |
| 23028 | overlap A | 16 | 35 | Graph 100, Cost 49, Overlap 72 | Overlap | none | MONITOR | OVERLAP |
| 9982 | overlap B | 10 | 35 | Graph 100, Overlap 76 | Overlap | none | MONITOR | OVERLAP |
| 26946 | DEMO_CLEAN | 20 | 30 | Cost 100, Compliance 60 | Graph | none | MONITOR | CLEAN |
| 22177 | DEMO_OVERBILL | 6 | 18 | Compliance 80 | none | none | NEED MORE INFORMATION | OVERBILL |
| 52862 | DEMO_STUCK | 23 | 37 | Time 93, Graph 98, Cost 50 | Overlap | none | MONITOR | STUCK |
| 53637 | DEMO_GHOST | 16 | 27 | Cost 100, Overlap 35, Time 34 | none | none | NEED MORE INFORMATION | GHOST |
| 46124 | NORMAL | 17 | 35 | Cost 55, Graph 100, Overlap 73 | Overlap | none | MONITOR | NORMAL |
| 15149 | overlap GPS | 11 | 35 | Overlap 91, Graph 100 | Graph | none | MONITOR | OVERLAP |
| 16180 | MIXED | 17 | 40 | Overlap 93, Compliance 80, Graph 100 | Graph | none | MONITOR | MIXED |
| 25533 | COST_ANOMALY | 17 | 40 | Overlap 93, Compliance 80, Graph 100 | Graph | none | MONITOR | COST_ANOMALY |
| 47627 | extra | 11 | 36 | Overlap 90, Graph 100 | Graph | none | MONITOR | EVIDENCE_GHOST |
| 49815 | extra | 22 | 37 | Time 100, Graph 100, Cost 37 | Overlap | none | MONITOR | TIME_ANOMALY |
| 50902 | extra | 16 | 40 | Overlap 90, Compliance 60, Graph 100 | Graph | none | MONITOR | NORMAL |
| 7519 | extra | 10 | 26 | Overlap 61, Cost 29, Graph 62 | Graph | none | NEED MORE INFORMATION | NORMAL |
| 11565 | extra | 10 | 35 | Graph 100, Overlap 75 | Overlap | none | MONITOR | NORMAL |

DEMO_OVERBILL remains low because Cost is often unavailable and missing weight is not redistributed. That is not a claim that over-billing is absent. DEMO_CLEAN can still have a high allocation Cost signal; the held-out CLEAN label is not a fusion input.

Conflicting-evidence behaviour was verified on controlled fixtures (citizen incomplete vs milestone complete vs satellite inconclusive), not on these 30 extract rows.

---

## 15. Tests

Backend suite passed (exit 0), including frozen Cost/Time/Overlap/Compliance/Evidence/Fusion V1.1 suites plus Risk Fusion V2:

1. all major evidence groups present  
2. only one evidence group (not 100/100)  
3. missing evidence  
4. correlated overlap + graph  
5. independent corroborating evidence  
6. conflicting evidence  
7. high priority + low confidence → NEED MORE INFORMATION  
8. low priority + high confidence  
9–11. REAL / HYBRID / SYNTHETIC retained and disclosed  
12. duplicate evidence IDs ignored  
13–14. unavailable vs not-assessable  
15–16. bounded 0–100 and deterministic  
17. monotonicity  
18–19. historical reproducibility; new evidence changes the result; prior history unchanged  
20. officer decision does not change V1.1 or V2 scores  
21–23. no-fraud wording; no automatic sanction; no automatic payment  
24. provenance / evidence IDs preserved  

Frontend: 73 tests passed. Next.js build succeeded.

```powershell
cd backend
python -m pytest
python -m app.engines.fusion_v2.evaluate_run

cd ..\frontend
npm test
npm run build
```

---

## 16. Limitations

- Prototype weights and thresholds are not official MoSPI/MPLADS parameters.  
- V2 cannot invent field, image, satellite, or citizen evidence that was never stored.  
- Overlap V1 still flags generic repeated titles; V2 inherits that review-queue signal and then discounts Graph when it is the same similarity edge.  
- Compliance and several verification engines have no native 0–100 anomaly score; fusion mappings are documented prototypes.  
- Citizen evidence remains supporting only (single-report cap).  
- Image-forensics AI-generation is a weak optional signal (capped).  
- Need & Impact is not an investigation-risk input.  
- High Investigation Priority is not fraud.  
- No labelled investigation dataset exists, so no accuracy metric is claimed.

---

## 17. Governance safeguards

- Terminology: Investigation Priority and Evidence Confidence only.  
- No legal fraud finding, fraud probability, automatic sanction, or PFMS/payment release.  
- AI recommends. Authorized officers decide (`MONITOR` / `REVIEW` / `INSPECT` / `NEED MORE INFORMATION`).  
- Inconclusive and not-assessable states are preserved.  
- REAL / HYBRID / SYNTHETIC remain distinguishable.  
- Synthetic/HYBRID major contributions are disclosed.  
- Frozen engines were not rewritten.

STOP.
