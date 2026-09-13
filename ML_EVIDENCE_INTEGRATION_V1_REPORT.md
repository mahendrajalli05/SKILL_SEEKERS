# ML → Evidence Integration V1 report

Date: 2026-09-10  
Layer: `ml-evidence-integration-v1`  
HTTP:

- `POST /api/v2/projects/{id}/ml-evidence`
- `GET  /api/v1/projects/{id}/evidence` (existing; now includes ML objects)
- `POST /api/v2/ml/predict` and `POST /api/v2/projects/assess` remain `NEW_PROJECT_ASSESSMENT` and do not persist

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 core schema/validation, Risk Fusion V1.1, Risk Fusion V2 formula, Relationship Graph V1, Search, Plan → Claim → Evidence, Document/Blueprint, Image Evidence, Image Forensics, Geospatial, Satellite, Need & Impact, Milestone Advisor, Jan-Sakshi, Investigation Copilot architecture, Lifecycle orchestration, Demo cases.

**ML anomaly score is NOT a fraud probability.**

---

## 1. What was added

A thin adapter converts an existing Isolation Forest prediction into a canonical Evidence Object V1 row and persists it append-only.

```
Existing ML inference (cost-anomaly-v1 / time-anomaly-v1)
        ↓
Normalized ML finding (UNUSUAL_PATTERN / ELEVATED_ANOMALY_SIGNAL / INCONCLUSIVE)
        ↓
Evidence Object V1 (engine=ml, signal=ML_ANOMALY_SIGNAL)
        ↓
append-only persist (does not replace historical ML observations)
        ↓
GET /api/v1/projects/{id}/evidence
        ↓
Passport / Investigation Workspace / Copilot structured retrieval
```

The layer does **not** retrain models, duplicate feature engineering, write `fusion_score`, or change Investigation Priority.

---

## 2. Existing Evidence Object schema reused

No new evidence tables. No new required Evidence Object fields.

Reused as-is:

| Field | ML use |
| --- | --- |
| `evidence_id` | `ev:ml:{project}:ML_ANOMALY_SIGNAL:{mode}:{digest}` with an observation token so retrains append |
| `engine_name` | `ml` |
| `engine_version` | loaded `model_version` |
| `signal_type` | `ML_ANOMALY_SIGNAL` |
| `finding` / `explanation` | sanitized inference text (Evidence V1 forbids the word “fraud”) |
| `score` | `ml_anomaly_score` (0–100 distributional rank) or omitted when INCONCLUSIVE |
| `confidence` | feature-availability coverage (0.0–1.0). **Not** the anomaly score |
| `disposition` | `WHY_FLAGGED` / `WHY_NOT_FLAGGED` / `INCONCLUSIVE` |
| `data_mode` | `REAL` / `HYBRID` / `SYNTHETIC` |
| `provenance` | existing envelope plus ML identity in notes and facts |
| `evidence_facts` | OBSERVATION (allocation, category, …) vs DERIVED (model identity, score, limitations) |

---

## 3. ML evidence types

Suggested separate types `ML_ANOMALY_OBSERVATION` / `ML_ANOMALY_FINDING` / `ML_ANOMALY_SCORE` were **not** added as extra signal enums. Evidence Object V1 already distinguishes:

1. observation facts (`fact_kind=OBSERVATION`)
2. derived finding (`finding` + `DERIVED` facts, including `ml_anomaly_finding`)
3. score (`score` + fact `ml_anomaly_score`)

Canonical signal:

- `SignalType.ML_ANOMALY_SIGNAL`

Neutral finding labels:

- `ELEVATED_ANOMALY_SIGNAL`
- `ML_ANOMALY_SIGNAL`
- `INCONCLUSIVE`

Never: FRAUD, FRAUD DETECTED, FRAUD PROBABILITY, GUILTY, CORRUPTION CONFIRMED.

---

## 4. Provenance fields

Every stored ML object preserves:

- project `id` and `internal_project_id`
- `source` = ML model (`source_type=ml_model` on REAL; HYBRID keeps `hybrid_enrichment` because Evidence V1 HYBRID validation requires it; SYNTHETIC stays `synthetic_test_record`)
- `model_name`, `model_version`, `feature_schema_version`, `training_data_hash`, `training_mode`
- `data_mode`
- `created_at`
- inference `explanation` (Evidence-V1-safe wording)
- `limitations`
- `feature_availability`
- `ml_anomaly_score` separately from evidence confidence

Filesystem paths and model artifact files are not exposed to clients.

---

## 5. Project-level integration

`POST /api/v2/projects/{id}/ml-evidence`

1. validate project  
2. validate requested data mode (no silent REAL/SYNTHETIC conversion)  
3. load requested model version (no silent fallback)  
4. call existing `predict_cost` / `predict_time`  
5. convert to Evidence Object  
6. persist with `add_evidence_object` (does not delete sibling ML rows)  
7. return created identity + summary  

Request:

```json
{
  "data_mode": "REAL",
  "model_version": "cost-anomaly-v1-9d0c62e3b384"
}
```

Omitted `model_version` uses the registered `cost-anomaly-v1` artifact.

---

## 6. New-project behavior

A proposal with no stored project id is **not** written as historical evidence.

| Endpoint | `assessment_kind` / `evidence_kind` | Persisted |
| --- | --- | --- |
| `POST /api/v2/ml/predict` | `NEW_PROJECT_ASSESSMENT` | no |
| `POST /api/v2/projects/assess` | `NEW_PROJECT_ASSESSMENT` | no |
| `POST /api/v2/projects/{id}/ml-evidence` | `PROJECT_STORED_EVIDENCE` | yes |

No fake documents, execution evidence, citizen reports, or historical Evidence Objects are created for a not-yet-existing project.

---

## 7. API endpoints

| Method | Path | Role |
| --- | --- | --- |
| POST | `/api/v2/projects/{id}/ml-evidence` | create/store ML evidence |
| GET | `/api/v1/projects/{id}/evidence` | existing retrieval; ML included; optional `engine=ml` / `signal_type=ML_ANOMALY_SIGNAL` |
| POST | `/api/v2/ml/predict` | new-project ML signal only |
| POST | `/api/v2/projects/assess` | new-project engines + ML, not stored |

Existing evidence response schema is unchanged (additional items only).

---

## 8. Passport integration

No redesign. The EVIDENCE section gained a compact **ML Evidence** block:

- ML anomaly signal (explicitly not fraud confirmation)
- model name / version
- anomaly score vs evidence confidence
- data mode
- explanation / limitations
- optional generate action for a stored project

---

## 9. Investigation Workspace integration

No new dashboard cards or navigation. The existing Evidence tab shows:

- generate/store control
- ML anomaly signal, model, version, score, data mode, available features, explanation, limitations
- existing disposition groups still list ML objects (`WHY_FLAGGED` / `WHY_NOT_FLAGGED` / `INCONCLUSIVE`)

Copy states this is an ML anomaly signal, not fraud confirmation.

---

## 10. Copilot integration

Structured retrieval already reads stored Evidence Objects. Added intents:

- `ML_EVIDENCE` — “What ML signal exists?”, “Which model generated this score?”, “Why was the ML anomaly score elevated?”
- `ML_FRAUD_CLARIFICATION` — “Is this a fraud probability?”

Correct answer for the last question: **the ML anomaly score is not a fraud probability.** SARVSAKSHI does not determine legal fraud. Model details come from stored facts, not invention.

Recommended actions remain MONITOR / REVIEW / INSPECT / NEED MORE INFORMATION.

---

## 11. Real / Hybrid / Synthetic handling

| Requested mode | Project | Stored mode |
| --- | --- | --- |
| REAL | real work | REAL |
| HYBRID | real work | HYBRID (labelled; not presented as REAL) |
| SYNTHETIC | real work | rejected (`unsupported_data_mode`) |
| REAL or HYBRID | `is_synthetic` test row | rejected |
| SYNTHETIC | `is_synthetic` test row | SYNTHETIC |

No synthetic-to-real conversion.

---

## 12. Failure modes

| Condition | Result |
| --- | --- |
| missing project | `not_found` 404 |
| missing model artifact | `model_missing` 503 |
| requested version ≠ loaded | `model_version_mismatch` 409 |
| corrupted artifact | `corrupted_model_artifact` 503 |
| malformed inference output | `malformed_ml_inference` 422 |
| unsupported data mode | `unsupported_data_mode` 422 |
| missing allocation / category | stored `INCONCLUSIVE` (no fabricated score) |
| persistence failure | `database_error` 500 |

Failed inference is never converted into a normal score.

---

## 13. Immutability / auditability

ML evidence is append-only. A second prediction, or a later model version, creates a **new** observation. Historical rows are not overwritten or mutated when the model is retrained.

`evidence_id` includes model version plus an observation token so identities remain distinguishable.

---

## 14. Tests

Backend coverage includes:

- valid existing project → stored ML evidence, type, provenance, model version, feature schema, training hash, data mode, anomaly score, explanation, limitations
- missing project / missing model / invalid version / missing required feature / corrupted artifact / unsupported data mode / persistence failure
- second prediction remains a distinct observation; old row unchanged; different model versions distinguishable
- REAL stays REAL; HYBRID stays HYBRID; SYNTHETIC stays test-only
- existing GET evidence includes ML; create endpoint works
- Copilot retrieval of signal, model version, elevated explanation; fraud-probability question clarified; no unsupported causal claims
- Cost / Time / Overlap / Compliance / PCE / Fusion V1.1 / Fusion V2 version strings and V2 weights unchanged; V2 Investigation Priority identical with or without an ML object (`ML_ANOMALY_SIGNAL` is not in `SIGNAL_TYPE_TO_GROUP`)

---

## 15. Regression results

| Suite | Result |
| --- | --- |
| Backend `python -m pytest` | **passed** (full suite, including 12 ML-evidence tests and 2 Copilot ML tests) |
| Frontend `npm test` | **103 passed** |
| Next.js `npm run build` | **passed** |

---

## 16. Limitations

- Isolation Forest remains a global training-distribution detector. It can disagree with Cost V1.1 local peers.
- REAL time ML stays INCONCLUSIVE (no verified execution dates). The HYBRID_TEST time artifact is not used as a silent REAL fallback.
- Evidence Object V1 rejects the token “fraud”. Stored ML explanations and findings use neutral anomaly language only (unusualness versus the training/reference distribution). They do not express probability of wrongdoing, likelihood of wrongdoing, legal findings, legal guilt, corruption, fraud probability, or fraud detected. Copilot still answers “The ML anomaly score is not a fraud probability.” using allowed governance phrasing.
- HYBRID ML objects keep `source_type=hybrid_enrichment` because frozen Evidence V1 HYBRID rules require `enrichment_used=true`; model identity is still in facts and notes.
- ML evidence is **not** fused into Investigation Priority.

---

## 17. Confirmation that Risk Fusion was unchanged

- Risk Fusion V1.1 `ENGINE_VERSION` remains `risk-fusion-v1.1`. Integrated weights remain Cost 0.25 / Schedule 0.15 / Overlap 0.15 / Compliance 0.15.
- Risk Fusion V2 `ENGINE_VERSION` remains `risk-fusion-v2`. `GROUP_WEIGHTS` still sum to 1.00. `ML_ANOMALY_SIGNAL` is **not** in `SIGNAL_TYPE_TO_GROUP`.
- Creating ML evidence does not write `fusion_score` and does not recalculate Investigation Priority.
- A V2 fuse of the same Cost object with and without an ML object yields the same Investigation Priority.

---

## Governance

- ML anomaly score is **not** a fraud probability.
- Stored ML explanations and findings use neutral anomaly language and do not express probability of wrongdoing or legal conclusions.
- No automatic sanction or payment.
- AI recommends. Authorized officers decide.

STOP.
