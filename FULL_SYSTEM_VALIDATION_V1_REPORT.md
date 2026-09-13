# FULL-SYSTEM VALIDATION V1 REPORT

Validation of SARVSAKSHI as an integrated product. This is not a redesign, not a new intelligence engine, and not a model-training task.

**Overall result: PASS WITH LIMITATIONS**

The system is a coherent, reproducible, auditable decision-support layer. Frozen engines were not rewritten. Risk Fusion V2 remains `risk-fusion-v2`. No fraud probability is produced. No automatic sanction or payment occurs. REAL / HYBRID / SYNTHETIC separation is preserved. Limitations below are real and are not hidden.

---

## 1. Validation date

**2026-09-11**

## 2. Build / version information

| Item | Value |
|---|---|
| Git SHA | `badc511e4b99aca16431c3010532e1ca4e8d53e3` (`badc511`) |
| Backend package | `0.1.0` |
| Frontend package | `sarvsakshi-web@0.1.0` |
| Python | 3.14.7 |
| Node | v24.19.0 |
| Next.js (production build) | 15.5.25 |
| Cost engine | `cost-peer-v1.1` |
| Time engine | `time-peer-v1` |
| Risk Fusion V2 | `risk-fusion-v2` (unchanged; weights match `FROZEN_FUSION_V2_WEIGHTS`) |
| Cost ML artifact (local) | `cost-anomaly-v1-9d0c62e3b384` / schema `cost-features-v1` / hash `9d0c62e3b3843e607024cff72179295c3d258a9dfb909b3ab72aee05ec7f8bca` |
| Time ML artifact (local) | `time-anomaly-v1-0bbf0968b3ae` / schema `time-features-v1` / hash `0bbf0968b3aee7fec81f3bab3117ef5fc841ad8ed2754fa05d22ed9f6452eb3a` |

### Files created or changed in this task

| File | Why |
|---|---|
| `backend/tests/test_full_system_validation.py` | Integration tests for journeys, data-mode, demo cases, ML, context, V2, Copilot, security. |
| `backend/tests/test_db.py` | Expected tables now include `fusion_score_v2`, `milestone`, and Contextual Intelligence tables. |
| `data/processed/sarvsakshi.db` | Additive schema only: empty `external_source`, `external_context_snapshot`, `external_context_observation`. Project rows were not rewritten. |
| `FULL_SYSTEM_VALIDATION_V1_REPORT.md` | This report. |
| `ROADMAP.md` | Phase 9 Integration tests and Data validation only. |

No frozen engine, formula, threshold, demo scenario definition, or frontend visual identity was changed.

### Regression commands

| Command | Result |
|---|---|
| `python -m pytest` (backend) | **PASS** — 689 tests, exit 0 |
| `python -m pytest tests/test_db.py tests/test_full_system_validation.py` (after schema/test updates) | **PASS** — 30 tests, exit 0 |
| `npm test` (frontend) | **PASS** — 39 files, 104 tests |
| `npm run build` | **PASS** — compiled, typed, 11 routes generated |

---

## 3. Data foundation validated

**Status: PASS**

Hashes match prior data reports:

| Dataset | SHA-256 |
|---|---|
| Cleaned CSV | `fb4bd06a75a3f66d7bfc08d02b86c980932682926b441fc4371dca8afdd9dd64` |
| Raw extract | `aa1d0b7c9c6bbe014a1af772a22ab3dc0a6eb24d043695060abaa0f94333e413` |
| Synthetic enrichment CSV | `d1de1b151cd115f9e4c0ae291f585481527a1f02846cb593c66d6c819895f4f1` |

Live SQLite `data/processed/sarvsakshi.db` (read-only checks):

| Check | Result |
|---|---|
| Project rows | 56,138 |
| Distinct `internal_project_id` | 56,138 |
| Duplicate internal IDs | 0 |
| `is_synthetic = 1` project rows | 0 |
| Snapshot `record_count` | 56,138 |
| Evidence objects | 64 |
| Orphan evidence (`project_id` with no project) | 0 |
| Lifecycle | FUTURE 53,195 / ONGOING 629 / COMPLETED 1,503 / UNKNOWN 811 |
| Context tables present | yes, currently empty (0 source / 0 snapshot / 0 observation rows) |

Synthetic enrichment remains in `data/synthetic/` and is not stored as project rows.

---

## 4. REAL / HYBRID / SYNTHETIC validation

**Status: PASS**

- REAL project rows remain `is_synthetic = 0`.
- Demo cases bind to real AP extract identities and attach labelled HYBRID evidence. They are not converted to REAL.
- Isolated tests never persist SYNTHETIC as REAL.
- Cost V1.1 has no HYBRID-TEST mode; observed allocation evidence stays REAL when fused beside HYBRID objects.
- Time HYBRID_TEST stays `dataset_type == "HYBRID"` and does not silently become REAL.
- API governance checks reject filesystem paths and `model.joblib` leakage in representative payloads.

---

## 5. Future workflow result

**Status: PASS WITH LIMITATION**

New-project assessment uses `POST /api/v2/projects/assess`. It does not create a project row (`project_id` is null, `persisted` is false). Label is `NEW_PROJECT_ASSESSMENT`. Risk Fusion V2 is unavailable. `automatic_sanction` is false. `fraud_probability` is null. No historical Evidence Objects, citizen reports, expenditure, or completed status are invented. Time remains unscored (no execution dates).

### Live persist=false runs against the 56,138-row peer corpus

**A. Ordinary proposal** — Andhra Pradesh / KURNOOL / tanks / ₹500,000 / Unsanctioned / REAL

| Layer | Observed |
|---|---|
| Cost V1.1 | available; COST_ANOMALY score **66**; 330 peers; broader category fallback |
| Time V1 | INSUFFICIENT_EVIDENCE; score null |
| Overlap V1 | NOT_LINKED; overlap score 56 |
| Compliance V1 | R015 TRIGGERED (see limitation) |
| ML | SCORED **47**; `cost-anomaly-v1-9d0c62e3b384` |
| Context | state population **52,787,000**; `OBSERVED_EXTERNAL_INDICATOR`; REAL; not a project-specific fact |
| Risk Fusion V2 | unavailable |

**B. Unusual high-allocation proposal** — same identity, ₹50,000,000

| Layer | Observed |
|---|---|
| Cost V1.1 | score **100** |
| ML anomaly | **90** |
| Separation | Cost 100 and ML 90 remain separate fields |

**C. Incomplete proposal** — `{ "state": "Andhra Pradesh" }` only

| Layer | Observed |
|---|---|
| Cost V1.1 | unavailable |
| ML | INCONCLUSIVE |
| Overlap | INSUFFICIENT |
| Compliance | R015 still TRIGGERED (same IDA-empty limitation) |

**D. HYBRID label on an otherwise identical ordinary payload**

HYBRID is preserved on the response. Time is still INCONCLUSIVE (no fabricated execution dates). Population remains a REAL external statistic, not a project fact.

**Limitation:** `ProjectAssessRequest` has no IDA field. `assess_new_project` hardcodes `ida=""`, so R015 triggers on new-project assess. This is not a false compliance **pass**. The frozen API was not redesigned in this task.

Isolated tests also cover the three scenarios plus the HYBRID label on a temp database.

---

## 6. Ongoing workflow result

**Status: PASS WITH LIMITATION**

Live REAL sample: project id **21192**, ARAKU(ST), ₹285,000, ONGOING, mobile sanitation equipment.

| Layer | Observed |
|---|---|
| Cost V1.1 | WITHIN_PEER_RANGE; score 19; confidence 82; 20 peers |
| Time V1 REAL | INSUFFICIENT_EVIDENCE (no verified execution dates) |
| Compliance | NO_RULES_TRIGGERED on assessable rules; spend rule R004 NOT_ASSESSABLE |
| Passport / lifecycle | ONGOING; no automatic sanction |

HYBRID ONGOING demo STUCK (id **52862**) was used for the full journey: Passport → Lifecycle → Plan → Claim → Evidence → Milestone → Cost/Time → Context → Risk V2 → Graph → Copilot → officer `NEED_MORE_INFO`. Officer decision did not mutate Investigation Priority. No payment/fund release.

**Limitation:** REAL GPS, satellite imagery, and execution dates are unavailable on this extract. Those layers correctly remain INCONCLUSIVE / UNAVAILABLE rather than inventing history.

---

## 7. Completed workflow result

**Status: PASS WITH LIMITATION**

Live REAL sample: project id **5263**, ONGOLE, ₹500,000, COMPLETED, roads.

| Layer | Observed |
|---|---|
| Cost V1.1 | score 0; 115 peers |
| Time V1 REAL | INSUFFICIENT_EVIDENCE |
| Historical evidence | not fabricated to fill module gaps |

HYBRID COMPLETED demo GHOST (id **53637**) carries stored evidence (22 objects) and stored V2 IP 28 / EC 33 / REVIEW. Completed-project evidence is not confused with `NEW_PROJECT_ASSESSMENT`.

---

## 8. Four demo case results

**Status: PASS WITH LIMITATION**

Existing demo configuration and fixtures were used. Scenario definitions were not rewritten to force INSPECT / FRAUD / SAFE. All four cases: `data_mode=HYBRID`, `is_synthetic=0` on the base project, `fusion_v2_unchanged=true`, `fraud_conclusion=false`, `automatic_sanction=false`, `automatic_payment=false`. Fused V2 evidence IDs are a subset of stored evidence IDs.

### GHOST

| Field | Value |
|---|---|
| Project id / source | **53637** / `WS/MP521/2023-2024/3061` |
| Constituency / amount | VIZIANAGARAM / ₹7,378,000 |
| Lifecycle | COMPLETED |
| Evidence | 22 objects |
| Major signals | Cost 100 REAL WHY_FLAGGED; Geo mismatch 100 HYBRID WHY_FLAGGED; Time 34 WHY_NOT_FLAGGED; satellite availability flagged; citizen aggregate NOT_ASSESSABLE; Need/Impact INCONCLUSIVE |
| Stored V2 | IP **28**, EC **33**, **REVIEW**, `risk-fusion-v2` |
| Live recompute (persist=false) | same IP 28 / EC 33 / REVIEW |
| Milestone / Copilot / officer | available; Copilot grounded; officer actions human-controlled |
| Not forced | GHOST → INSPECT |

### OVER-BILL (`OVERBILL`)

| Field | Value |
|---|---|
| Project id / source | **22177** / `WS/MP523/2023-2024/51495` |
| Constituency / amount / category | ELURU / ₹3,550,000 / Repair and Renovation |
| Lifecycle | COMPLETED |
| Evidence | 5 objects |
| Major signals | Cost INCONCLUSIVE (sparse repair peers, score null, confidence 0.06); Compliance WHY_FLAGGED; Time 0 WHY_NOT_FLAGGED; PCE WHY_FLAGGED; Milestone WHY_FLAGGED |
| Stored V2 | none |
| Live recompute (persist=false) | IP **9**, EC **21**, **NEED_MORE_INFORMATION** |
| Not forced | OVER-BILL → FRAUD |

Cost INCONCLUSIVE is evidence-supported: Repair and Renovation does not yield a usable peer group. That is not a legal over-billing finding.

### STUCK

| Field | Value |
|---|---|
| Project id / source | **52862** / `WS/MP531/2023-2024/3961` |
| Constituency / amount | ANANTAPUR / ₹1,000,000 |
| Lifecycle | ONGOING |
| Evidence | 5 objects |
| Major signals | Time 93 HYBRID WHY_FLAGGED; Cost 50 REAL WHY_NOT_FLAGGED; Compliance WHY_NOT_FLAGGED; PCE INCONCLUSIVE; Milestone WHY_FLAGGED |
| Stored V2 | none |
| Live recompute (persist=false) | IP **15**, EC **29**, **MONITOR** |
| Not forced | STUCK → FRAUD |

### CLEAN

| Field | Value |
|---|---|
| Project id / source | **26946** / `WS/MP526/2023-2024/42089` |
| Constituency / amount | KADAPA / ₹3,500,000 / Sanctioned |
| Lifecycle | FUTURE |
| Evidence | 27 objects |
| Major signals | Cost 100 REAL WHY_FLAGGED; image reuse WHY_FLAGGED; compliance WHY_FLAGGED; Time REAL NOT_ASSESSABLE; citizen supporting WHY_NOT_FLAGGED / aggregate INCONCLUSIVE |
| Stored V2 | IP **20**, EC **29**, **MONITOR** (lags current evidence set) |
| Live recompute (persist=false) | IP **27**, EC **25**, **NEED_MORE_INFORMATION** |
| Not forced | CLEAN → SAFE |

CLEAN is not a guaranteed low-risk case. Observed allocation vs peers is flagged at 100. The system reports what the evidence supports.

**Limitation:** CLEAN stored `fusion_score_v2` snapshot (IP 20) lags live recompute from current Evidence Objects (IP 27). Formula unchanged. Append-only evidence can change recomputed V2. Demo API uses `persist=False`, so officers see the live recompute.

---

## 9. Cost validation

**Status: PASS**

Independent Cost V1.1 checks (in-memory peers, engine unchanged):

| Case | Result |
|---|---|
| Normal peer comparison | WITHIN_PEER_RANGE; deterministic on repeat |
| Elevated allocation | flagged; anomaly score present |
| Sparse peer group | INSUFFICIENT_EVIDENCE; score null |
| No peer group | INSUFFICIENT_EVIDENCE; score null |
| Chamber constituency | exclusion reason mentions chamber/house; may still score on AP fallback |

ML anomaly score and Cost V1.1 allocation anomaly score remain separate concepts. They are not merged.

---

## 10. Time validation

**Status: PASS**

| Mode | Result |
|---|---|
| REAL without verified execution dates | INSUFFICIENT_EVIDENCE; score null; `dataset_type=REAL` |
| Repeat REAL | identical null score |
| HYBRID_TEST with labelled synthetic schedule | `time_mode=HYBRID_TEST`; `dataset_type=HYBRID` |
| HYBRID_TEST without schedule | remains HYBRID; does not become REAL |

---

## 11. Overlap validation

**Status: PASS**

Overlap V1 REAL results flow into Relationship Graph V1. Graph `project_node` is PROJECT. `dataset_type` is REAL. `SIMILAR_TO` edges, when present, are explainable from overlap matches. No fabricated relationships were required. Overlap is not reimplemented inside Fusion V2.

---

## 12. Compliance validation

**Status: PASS WITH LIMITATION**

TRIGGERED / NOT_TRIGGERED / NOT_ASSESSABLE remain distinct. Missing expenditure (R004) is NOT_ASSESSABLE, not a pass. Missing IDA on a stored project is not the same status as a project with IDA.

**Limitation:** new-project assess always supplies empty IDA, so R015 triggers there. Documented; API not redesigned.

---

## 13. Evidence validation

**Status: PASS**

Representative coexistence (isolated DB): Cost, Time, Overlap, Compliance, Graph, Need, Context, and append-only ML objects. Each item carries provenance, data mode, and no fraud-probability wording.

Generating a second ML observation creates a **new** `evidence_id`; the first is not overwritten.

Risk Fusion V2 evidence IDs are disjoint from ML evidence IDs. Group breakdown has no `ml` group.

Live demo evidence types observed: cost, time, overlap, compliance, graph, image, forensics, geo, satellite, citizen, milestone, pce, need.

---

## 14. ML validation

**Status: PASS WITH LIMITATION**

| Check | Result |
|---|---|
| `POST /api/v2/ml/predict` with artifact | 200; model version, feature schema version, training data hash returned |
| Repeat inference | identical `ml_anomaly_score` |
| Missing model directory | HTTP 503 `model_missing`; no silent fallback |
| Missing required features | INCONCLUSIVE or null score |
| Version mismatch | 409/422/400/503 |
| `POST /api/v2/projects/assess` | `NEW_PROJECT_ASSESSMENT`; V2 unavailable |
| `POST /api/v2/projects/{id}/ml-evidence` | append-only Evidence Object |
| Fraud probability | always null |
| Legal conclusion | not produced |

ML anomaly score ≠ fraud probability.

**Limitation:** model artifacts are gitignored. They are present in this local checkout. A fresh clone without artifacts correctly returns `model_missing`.

---

## 15. Contextual intelligence validation

**Status: PASS WITH LIMITATION**

| Check | Result |
|---|---|
| `GET /api/v2/projects/{id}/context` | population AVAILABLE with source URL, retrieval date, reference year, STATE geographic level, unit, REAL data mode, `OBSERVED_EXTERNAL_INDICATOR` |
| Notes | regional statistic is not a project beneficiary / project-specific fact |
| `GET /api/v2/context/sources` | registry returns items |
| `POST /api/v2/projects/{id}/context/refresh` | 200 |
| Cost / Risk Fusion unchanged flags | true |
| Unsupported district SoR / NFHS | not fabricated (prior module report; empty live observation tables after rollback) |

Live production context tables exist after the schema fix and currently have **0** persisted rows. New-project assess does not persist context onto a project.

**Limitation found and fixed:** production SQLite initially lacked these three tables, so live `assess_new_project` crashed with `no such table: external_context_snapshot`. Additive `Base.metadata.create_all` added empty tables. Project count remained 56,138.

---

## 16. Risk Fusion V2 validation

**Status: PASS**

Before/after engine version: **`risk-fusion-v2`**.

Frozen weights (unchanged):

```
cost 0.14, time 0.10, overlap 0.10, compliance 0.10, graph 0.08,
document 0.06, image 0.06, forensics 0.05, geospatial 0.08, satellite 0.07,
citizen 0.06, milestone 0.05, pce 0.05, need 0.00
```

Sum = 1.00. Matches `FROZEN_FUSION_V2_WEIGHTS`.

| Check | Result |
|---|---|
| Intended Evidence Objects only | ML and context signal types are **not** in `SIGNAL_TYPE_TO_GROUP` |
| Missing ≠ zero | empty evidence → IP 0 with unavailable groups; one cost group → 0 < IP < 100 |
| Missing-signal penalty | unavailable weight is not redistributed |
| Conflict pairs | HYBRID citizen + PCE fuse without formula change |
| REAL/HYBRID/SYNTHETIC | reliability mix and EC caps unchanged |
| ML not in formula | confirmed in isolation and on mixed-evidence project |
| Contextual signals not in formula | confirmed |
| Determinism | same evidence → same Investigation Priority |

Investigation Priority is a review ranking, not a legal finding.

---

## 17. Graph validation

**Status: PASS**

Graph nodes include the subject PROJECT. Dataset type follows the requested mode. SIMILAR_TO is overlap-derived where overlap produced matches. Graph is not fused into Investigation Priority as a rewritten overlap engine. Need remains weight 0 in V2.

---

## 18. Document / Blueprint validation

**Status: PASS**

Upload → extract → labelled fields. Text PDF returns `EXTRACTED` / `pdf_text`. No new OCR/LLM extractor was introduced. Isolated tests cover plan-attach conflict state (`PLAN DATA CONFLICT`) from Document V1.

---

## 19. Image / Forensics validation

**Status: PASS WITH LIMITATION**

PNG upload succeeds. Forensics runs on the stored image. Original bytes unmodified. AI-generation forensic signal remains INCONCLUSIVE / unavailable as designed. No perfect detection claim.

Demo GHOST/CLEAN carry labelled HYBRID image reuse / forensic objects. Those are fixtures, not official photographs.

---

## 20. Geospatial validation

**Status: PASS WITH LIMITATION**

REAL project without coordinates → INCONCLUSIVE / UNAVAILABLE, not a fabricated GPS match. HYBRID demo GHOST stores `GEOSPATIAL_LOCATION_MISMATCH` score 100 with labelled SYNTHETIC coordinates. 500 m threshold is a prototype, not an official MPLADS rule.

---

## 21. Satellite validation

**Status: PASS WITH LIMITATION**

Default provider path returns UNAVAILABLE / INCONCLUSIVE. No fake imagery and no fake change detection. Demo fixtures may attach labelled HYBRID satellite-availability objects; they are not official remote-sensing products.

---

## 22. Need & Impact validation

**Status: PASS WITH LIMITATION**

Need & Impact endpoints are reachable. Need group weight in V2 is **0**. High need is not high investigation priority. GHOST stored Need/Impact/Priority objects are INCONCLUSIVE. New-project / CLEAN planning remains “need more information” where inputs are insufficient. Not a sanction.

---

## 23. Milestone validation

**Status: PASS**

Advisor recommendations observed: PROCEED / HOLD / INSPECT / INCONCLUSIVE. Officer actions include NEED MORE INFORMATION. No `/payments` or `/pfms` routes. `funds_released` / `payment_executed` / `automatic_sanction` remain false on evidence facts. Officer decision is separate from model output.

---

## 24. Jan-Sakshi validation

**Status: PASS WITH LIMITATION**

Missing GPS → INCONCLUSIVE (or rejected/accepted per existing rules). Raw citizen latitude is not returned on the submission payload. Response states the 500 m restriction is **not an official MPLADS rule**. Satisfaction rating and text are accepted. Watermark is a presentation copy; original image bytes stay unchanged (prior Jan-Sakshi tests plus this validation). Aggregate sample safeguard remains; one report is not treated as truth.

---

## 25. Copilot validation

**Status: PASS**

STUCK HYBRID journey asked all seven required questions against stored evidence, deterministic template provider (`used_llm=false`):

1. What evidence exists for this project?
2. What is the main anomaly signal?
3. Which model generated the ML score?
4. What external context is available?
5. Is the ML score a fraud probability?
6. Why is this project being reviewed?
7. What evidence is missing?

Answers are evidence-grounded. ML is not presented as fraud. Missing evidence is acknowledged. Recommended actions stay in MONITOR / REVIEW / INSPECT / NEED MORE INFORMATION. No payment or sanction recommendation.

---

## 26. Search / Passport validation

**Status: PASS**

Isolated checks: AP default scope, work-description partial match, Scheme ID lookup, MP name, constituency options cascade, Passport identity per id. Navigating from project A to project B does not reuse A’s `internal_project_id` or Scheme ID.

Live AP extract identities used in this report (21192, 5263, 217, demo ids) load as distinct passports.

Frontend search/passport component tests remain green. **No live browser session** was available to click the cascade; see section 35.

---

## 27. Frontend validation

**Status: PASS WITH LIMITATION**

Component and page tests cover dashboard, search, Passport, Investigation Workspace, lifecycle, evidence, risk, graph, Jan-Sakshi, demo, new-project assessment, and contextual intelligence.

Production build routes:

| Route | Kind |
|---|---|
| `/` | dashboard (static) |
| `/search` | search |
| `/projects/[id]` | Passport |
| `/projects/[id]/investigate` | Investigation Workspace |
| `/projects/[id]/graph` | graph |
| `/jan-sakshi` | Jan-Sakshi |
| `/demo`, `/demo/[caseId]` | demo |
| `/assess-new-project` | new-project assessment |
| `/need-impact` | Need & Impact |
| `/reviews`, `/login` | gated officer surfaces |

No UI redesign was performed.

**Limitation:** no interactive browser smoke test. Verification is Vitest + `npm run build` only.

---

## 28. API integration validation

**Status: PASS**

Representative chains (isolated + live read-only):

- Demo case GET → stored evidence → V2 recompute (`persist=False`)
- STUCK: Passport → lifecycle → plan → claims → evidence → milestones → cost → time → context → risk → graph → Copilot → officer decision
- REAL FUTURE/ONGOING/COMPLETED: Passport → cost → time → compliance → lifecycle
- New-project assess (not persisted)

Consistent project identifiers. Unavailable vs inconclusive vs scored remain distinct. No internal filesystem paths or model artifact paths in responses. Officer decision does not mutate V2 scores.

---

## 29. Database integrity validation

**Status: PASS**

- 56,138 real project records remain.
- No duplicate `internal_project_id`.
- Real project records were not rewritten for this validation.
- Synthetic enrichment remains a separate CSV.
- Demo evidence remains available (64 evidence objects, all attached to valid projects).
- Additive context tables are empty and did not alter project rows.

`init_db()` was **not** used on production (it can `drop_all` if schema is marked stale).

---

## 30. Determinism validation

**Status: PASS**

| Layer | Repeat check |
|---|---|
| Cost V1.1 | identical score |
| ML inference (same loaded model/input) | identical `ml_anomaly_score` |
| Risk Fusion V2 | identical Investigation Priority |
| Time REAL | identical null score |
| Copilot deterministic fallback | template mode, `used_llm=false` |
| Evidence IDs | append-only new ML ids; not in-place replacement |

Append-only creation is not the same as deterministic replacement. CLEAN stored vs live V2 difference is explained by additional evidence, not formula drift.

---

## 31. Security validation

**Status: PASS**

| Check | Result |
|---|---|
| Client-side model upload | no `/api/v2/ml/upload` or `/api/v2/ml/models` |
| Arbitrary artifact replacement via API | not exposed |
| Payment / PFMS | 404/405 |
| Filesystem path exposure | not present in representative API bodies |
| `data/raw` mutation | none |
| Real project record mutation | none in this task |
| Append-only evidence | ML second POST creates a new id |
| Provenance | required on mixed evidence items |

---

## 32. Defects found

1. **Production SQLite missing Contextual Intelligence tables**  
   `external_source`, `external_context_snapshot`, `external_context_observation` were defined in models and isolated tests (`init_db()`), but were absent from `data/processed/sarvsakshi.db`. Live `assess_new_project` failed with `no such table: external_context_snapshot`.

2. **New-project assess always triggers R015**  
   Request schema has no IDA field; engine hardcodes `ida=""`. Not a false pass. Frozen API; not treated as an integration bug requiring a redesign.

3. **CLEAN stored V2 snapshot lags live evidence**  
   Stored IP 20 MONITOR vs live IP 27 NEED_MORE_INFORMATION. Formula unchanged.

---

## 33. Defects fixed

1. **Contextual tables** — smallest targeted fix: `Base.metadata.create_all` only. Three empty tables added. Project count still 56,138. Regression: expected-table test + live table-name assertion. Isolated validation tests and `tests/test_db.py` pass. Full pytest had already passed after the additive schema change; the two files were re-run after the assertion update (30 passed).

No formulas, thresholds, or demo scenario definitions were changed.

---

## 34. Remaining limitations

- No live browser session during this validation.
- REAL extract has no verified execution dates, project GPS, or satellite provider → Time / Geo / Satellite honestly INCONCLUSIVE or UNAVAILABLE.
- New-project assess has no IDA field, so R015 triggers.
- CLEAN stored Fusion V2 snapshot can lag append-only evidence; demo GET recomputes with `persist=False`.
- OVERBILL and STUCK have no stored `fusion_score_v2` row; live recompute is the officer-facing value.
- ML artifacts are local/gitignored; missing artifacts yield explicit 503.
- Isolation Forest cost-anomaly is unsupervised; it is not a fraud classifier and is not fused into V2.
- Contextual observations are regional statistics, not project facts; live context tables are empty until a persist path writes them.
- 500 m citizen geofence is a prototype, not an official MPLADS rule.
- Image AI-generation detection remains unavailable / INCONCLUSIVE.
- Coastal Andhra coverage is still not decided (unchanged roadmap item).
- Comparable Projects UI remains incomplete (unchanged roadmap item).

---

## 35. Browser availability during validation

**UNAVAILABLE**

No interactive browser session was used. Frontend verification was performed through Vitest component/page tests (104 passed) and the Next.js production build (exit 0). This report does **not** claim manual browser verification.

---

## 36. Final PASS / FAIL matrix

| # | Item | Status |
|---|---|---|
| 1 | Validation date / build | PASS |
| 2 | Data foundation | PASS |
| 3 | REAL / HYBRID / SYNTHETIC | PASS |
| 4 | Future / new-project workflow | PASS WITH LIMITATION |
| 5 | Ongoing workflow | PASS WITH LIMITATION |
| 6 | Completed workflow | PASS WITH LIMITATION |
| 7 | Demo GHOST | PASS WITH LIMITATION |
| 8 | Demo OVER-BILL | PASS WITH LIMITATION |
| 9 | Demo STUCK | PASS WITH LIMITATION |
| 10 | Demo CLEAN | PASS WITH LIMITATION |
| 11 | Cost V1.1 | PASS |
| 12 | Time V1 | PASS |
| 13 | Overlap V1 | PASS |
| 14 | Compliance V1 | PASS WITH LIMITATION |
| 15 | Evidence objects | PASS |
| 16 | ML | PASS WITH LIMITATION |
| 17 | Contextual intelligence | PASS WITH LIMITATION |
| 18 | Risk Fusion V2 | PASS |
| 19 | Relationship Graph | PASS |
| 20 | Document / Blueprint | PASS |
| 21 | Image / Forensics | PASS WITH LIMITATION |
| 22 | Geospatial | PASS WITH LIMITATION |
| 23 | Satellite | PASS WITH LIMITATION |
| 24 | Need & Impact | PASS WITH LIMITATION |
| 25 | Milestone Advisor | PASS |
| 26 | Jan-Sakshi | PASS WITH LIMITATION |
| 27 | Investigation Copilot | PASS |
| 28 | Search / Passport | PASS |
| 29 | Frontend | PASS WITH LIMITATION |
| 30 | API integration | PASS |
| 31 | Database integrity | PASS |
| 32 | Determinism | PASS |
| 33 | Security | PASS |
| 34 | Backend tests | PASS |
| 35 | Frontend tests | PASS |
| 36 | Production build | PASS |
| 37 | Browser smoke | UNAVAILABLE |

No matrix row is FAIL.

---

## 37. Overall system readiness assessment

**PASS WITH LIMITATIONS**

SARVSAKSHI behaves as one product across FUTURE, ONGOING, and COMPLETED paths, across REAL data and HYBRID controlled demos, and across the frozen intelligence / evidence / fusion / graph / ML / context / Copilot / officer stack.

Ready for the next planned phase (**Final UI/UX Redesign**) with the limitations above visible to operators:

- AI recommends. Authorized officers decide.
- Investigation Priority and Evidence Confidence are review rankings, not legal conclusions.
- INCONCLUSIVE, UNAVAILABLE, NEED MORE INFORMATION, and low Investigation Priority are valid, evidence-supported outcomes.
- Demo nicknames (GHOST, OVER-BILL, STUCK, CLEAN) are not guaranteed legal labels.

Not in scope for this task, and not marked complete: Final UI Redesign, Deployment, SIH Demo Rehearsal, Presentation, Viva.
