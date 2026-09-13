# ML Training & Inference V1 report

Date: 2026-09-10  
Layer: `ml-training-inference-v1`  
HTTP: `POST /api/v2/ml/predict`, `POST /api/v2/projects/assess`

Frozen and unchanged: real MPLADS project records, Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula, Relationship Graph V1, Search, Passport, Investigation Workspace, PCE, Document/Blueprint, Image Evidence, Image Forensics, Geospatial, Satellite, Need & Impact, Milestone Advisor, Jan-Sakshi, Investigation Copilot, Lifecycle orchestration, Demo cases.

This slice adds a reproducible training and inference layer. It does **not** train a supervised fraud classifier. It does **not** return a fraud probability.

---

## 1. Models actually trained

| Model | Type | Training mode | Version | Train / val / test |
| --- | --- | --- | ---: | --- |
| `cost-anomaly-v1` | IsolationForest | REAL | `cost-anomaly-v1-9d0c62e3b384` | 39,290 / 8,419 / 8,420 |
| `time-anomaly-v1` | IsolationForest | HYBRID_TEST | `time-anomaly-v1-0bbf0968b3ae` | 3,242 / 694 / 696 |

Cost training used observed SQLite `project` rows with positive allocation and a non-blank category (56,129 of 56,138). Synthetic scenario columns were never inputs.

Time training used planned-duration rows from the existing 10,000-record HYBRID enrichment CSV. `TRAINING_DATA_MODE = HYBRID_TEST`.

---

## 2. Models not trained and why

| Candidate | Decision |
| --- | --- |
| Supervised fraud / not-fraud classifier | No authoritative large fraud label set. D003. |
| REAL historical delay / slippage model | Real extract has no verified start or completion dates. Fabricating them would be false history. |
| Duplicate overlap embedding model | Overlap Intelligence V1 already provides semantic similarity. No second overlap model. |
| ML compliance | Compliance remains a deterministic rule engine. |
| Supervised risk / Investigation Priority model | Risk Fusion V2 remains the evidence-fusion layer. ML scores are optional signals and are **not** fused into Investigation Priority in this slice. |

---

## 3. Training dataset

**Cost (REAL):** SQLite `project` table, `is_synthetic = 0`. Observed fields only: allocation, category, state, constituency, work description, recommended date, status, house.

**Time (HYBRID_TEST):** `data/synthetic/sarvsakshi_synthetic_enrichment.csv`. Planned start/completion and physical progress are labelled SYNTHETIC. Real allocation and recommended date are copied identifiers, not fabricated REAL execution dates.

`data/raw/` and the cleaned extract were not modified.

---

## 4. Feature schema

Cost schema `cost-features-v1`:

| Feature | Source | Preprocessing | Missing |
| --- | --- | --- | --- |
| `log_allocation` | `allocation_amount` | log1p | required; INCONCLUSIVE |
| `allocation_peer_percentile` | amount in train (state, category) | empirical percentile; state then global fallback | 0.5 if empty |
| `rec_year` / `rec_month` | `recommended_date` | calendar | train median |
| `recommendation_age_days` | recommended date vs frozen train max date | days | train median |
| `desc_token_count` | work description | token count | 0 |
| `freq_*` | state, constituency, category, status, house | train frequency encoding | 0 if blank/unseen |
| `text_svd_0..7` | work description | train-only TF-IDF + TruncatedSVD | zero vector |

Time schema `time-features-v1` (HYBRID_TEST only): planned duration days, physical progress, log allocation, recommendation year.

Forbidden as features: `scenario_type`, `demo_case_id`, `mixed_signals`, `anomaly_notes`, `overlap_group_id`, `coordinate_source`, and the other held-out enrichment columns already listed in Cost V1.1.

---

## 5. Leakage safeguards

- Temporal split: sort by `recommended_date` then `internal_project_id`. Earlier records train. No random shuffle.
- TF-IDF vocabulary, SVD, frequency maps, peer percentiles, and scaler are fit on **train only**.
- Held-out synthetic labels are attached **after** scoring.
- REAL time inference does not silently load the HYBRID_TEST time artifact.

---

## 6. Algorithms

Isolation Forest, `random_state=26102`, `n_estimators=100`, `n_jobs=1`, `contamination=0.05` as a documented operating point (not a fraud rate).

`ml_anomaly_score` is the empirical rank of `-score_samples` against the frozen train raw scores, mapped to 0–100. Higher means more unusual versus the training distribution. It is not a probability of wrongdoing.

Feature contribution is a cheap perturbation: replace each scaled numeric feature with the train mean and measure the change in raw anomaly score. SHAP is not a dependency.

---

## 7. Model artifacts

Stored under `backend/app/ml/models/` (gitignored binaries):

- `cost-anomaly-v1/model.joblib` + `metadata.json`
- `time-anomaly-v1/model.joblib` + `metadata.json`
- `registry.json`

Identity on every scored prediction: `model_name`, `model_version`, `feature_schema_version`, `training_data_hash`.

Training commands (do not run at API startup):

```
python -m app.ml.training.cost_train
python -m app.ml.training.time_train
python -m app.ml.evaluation.cost_evaluate
```

Clients cannot upload artifacts. Prediction APIs do not accept a model file.

Cost data hash: `9d0c62e3b3843e607024cff72179295c3d258a9dfb909b3ab72aee05ec7f8bca`  
Time data hash: `0bbf0968b3aee7fec81f3bab3117ef5fc841ad8ed2754fa05d22ed9f6452eb3a`

---

## 8. Evaluation method

No accuracy, precision, recall, F1, or AUC. There is no genuine fraud label experiment.

Reported for Isolation Forest:

- score distribution
- anomaly rate at the fitted contamination threshold
- reproducibility (fixed seed + temporal split)
- feature coverage / schema
- synthetic held-out score distributions **after** prediction

---

## 9. Synthetic held-out results

Labels were joined after scoring. This is **not** fraud-detection accuracy. `COST_ANOMALY` in the HYBRID layer is expenditure versus sanctioned amount, not an allocation outlier.

| scenario_type | n | median `ml_anomaly_score` |
| --- | ---: | ---: |
| NORMAL | 6,999 | 64 |
| OVERLAP | 500 | 62.5 |
| TIME_ANOMALY | 799 | 73 |
| COST_ANOMALY | 999 | 78 |
| MIXED | 300 | 74.5 |
| EVIDENCE_GHOST | 399 | 85 |
| DEMO_CLEAN | 1 | 56 |
| DEMO_STUCK | 1 | 84 |
| DEMO_GHOST | 1 | 98 |
| DEMO_OVERBILL | 1 | 99 |

COST_ANOMALY is only modestly above NORMAL on this allocation model, which matches the label definition (spend, not allocation).

REAL unsupervised (all 56,138 scored rows): median score 58; Isolation Forest flag rate 9.3% (train flag rate was 5.0%; later-dated test rows shift upward). That temporal shift is a limitation of a date-ordered split, not a fraud rate.

---

## 10. New-project inference

Generic input: state, constituency, category, work description, allocation amount, recommendation date, optional status/house. Optional planned dates are accepted only by the HYBRID_TEST time model.

Flow: validate → normalize → available features → load requested model version (no silent fallback) → predict → explain → report missing/unseen features.

Missing allocation or category → INCONCLUSIVE. Unseen category still scores with frequency 0 and is listed under `unseen`. Missing artifact → `model_missing`. Wrong `model_version` → `model_version_mismatch`.

---

## 11. API examples

`POST /api/v2/ml/predict`

```json
{
  "state": "Andhra Pradesh",
  "constituency": "KURNOOL",
  "category": "Normal/Others",
  "work_description": "Construction of water tanks",
  "allocation_amount": 250000,
  "recommendation_date": "2023-06-01",
  "data_mode": "REAL"
}
```

Response includes model versions, `ml_anomaly_score`, feature availability, explanation, limitations, `data_mode`, `fraud_probability: null`. No sanction/payment flags.

`POST /api/v2/projects/assess` calls existing Cost V1.1, Time V1 (REAL → no duration score), Overlap V1, and Compliance V1 on the supplied fields. It does not persist Evidence Objects. Risk Fusion V2 is **not available** for a project that does not yet exist.

Five live predictions (2026-09-10), model `cost-anomaly-v1-9d0c62e3b384`, `data_mode=REAL`:

| Case | ML status | ML score | Cost V1.1 (assess) |
| --- | --- | ---: | --- |
| Typical tank ₹2.5 lakh, Kurnool | SCORED / ELEVATED | 95 | WITHIN_PEER_RANGE / 16 |
| High allocation ₹50 lakh, Eluru tanks | SCORED / ELEVATED | 97 | (ML only in this batch) |
| Unseen category, Guntur lights ₹3 lakh | SCORED / ELEVATED | 100 | unseen: category (+ constituency if not in train split) |
| Missing amount, Kadapa hall | INCONCLUSIVE | — | required feature missing |
| Extreme ₹2.5 crore, Srikakulam | SCORED / ELEVATED | 100 | — |

Assess of the typical tank: Investigation Priority unavailable; `automatic_sanction=false`; `fraud_probability=null`. Isolation Forest can flag a work that Cost V1.1 treats as within constituency peers because IF is a **global training-distribution** detector. Cost V1.1 remains the interpretable peer baseline.

Functional UI: `/assess-new-project` (NEW PROJECT ASSESSMENT). Not a redesign.

---

## 12. Limitations

- No fraud labels, no fraud probability, no fraud accuracy claim.
- Isolation Forest is additional to Cost V1.1, not a replacement. Global IF scores can disagree with local peer scores.
- Temporal split: later recommendation dates have a higher IF flag rate than train (test ≈ 27.8% vs train 5.0% on raw `predict()`). That is distribution shift, not a validated alert rate.
- Amount unit is unspecified in the source.
- ~99% of works are `Normal/Others`; category is a weak discriminator; text SVD is a compact title signal only.
- REAL time ML is INCONCLUSIVE. HYBRID_TEST time ML must not be cited as real MPLADS delay statistics.
- New-project Risk Fusion V2 is not computed (no stored Evidence Objects).
- ML scores are not written into Evidence Objects or fused in this slice.

---

## 13. Model versioning

Predictions carry `model_name`, `model_version`, `feature_schema_version`, `training_data_hash`. Requesting a different version does not fall back to another artifact.

---

## 14. Reproducibility

- Seed 26102
- Temporal split recipe in `app/ml/training/split.py`
- Train-only preprocessing
- CLI training, not startup training
- Registry metadata beside the joblib file

Backend tests: **694 passed** (2026-09-10).  
Frontend tests: **101 passed**.  
Next.js production build: **passed** (`/assess-new-project` present).

---

## Governance

- No fraud confirmed wording
- No automatic sanction or payment
- Officer/human decision unchanged (this slice does not add a decision action that mutates scores)
- Existing intelligence engines unchanged (version strings asserted; no sklearn in engine packages)

STOP.
