# Need & Impact V1 report

Date: 2026-09-10  
Engine: `need-impact-v1`  
HTTP:

- `GET  /api/v1/projects/{id}/need-impact`
- `POST /api/v1/need-impact/rank`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, Project Digital Passport structure, Plan–Claim–Evidence V1, Document & Blueprint Intelligence V1, Image Evidence & Authenticity V1, Geospatial Consistency V1.

This slice adds **decision-support prioritization for proposed/future MPLADS works** when available budget is limited. It produces **Need Score**, **Impact Score**, **Priority Score**, **Evidence Confidence**, and a recommended priority class.

It does **not** sanction a project, approve funds, release payments, or determine fraud.

---

## Architecture

```
Observed MPLADS fields (state, constituency, category, work, amount, status, date, MP, IDA)
        +
Optional TEST/SYNTHETIC need/impact enrichment (HYBRID/SYNTHETIC only)
        ↓
Need Score (modular; unavailable components marked)
Impact Score (modular; unavailable components marked)
Urgency (waiting time / observed disaster text / labelled TEST/SYNTHETIC)
        ↓
Priority Score = documented prototype weights of available Need + Impact (+ Urgency)
        ↓
HIGH PRIORITY / MEDIUM PRIORITY / LOW PRIORITY / INCONCLUSIVE
        ↓
Evidence Object V1 (engine=need)
  NEED_ASSESSMENT
  IMPACT_ASSESSMENT
  PRIORITY_ASSESSMENT
        ↓
GET /need-impact  and  POST /need-impact/rank (planning simulation)
```

Need & Impact is **not** fused into Investigation Priority. Fusion still treats this engine as not integrated.

There is **no** sanction or payment endpoint.

---

## Governance safeguards

Every response states:

> Priority recommendation only. Authorized officials make final administrative decisions.

And:

> Prototype weighting — not an official MPLADS sanction formula.

Outputs never include:

- sanction approved
- sanction denied
- fraud
- fraud probability

`automatic_sanction` is always `false`. `sanction_decision` is always `null`. Hypothetical budget ranking is labelled **PLANNING SIMULATION only**.

---

## Score formula

All weights below are **prototype weights only. They are not an official MPLADS sanction formula.**

### Need Score

Need components and prototype weights (sum 1.00):

| Component | Weight | REAL | HYBRID / SYNTHETIC |
| --- | ---: | --- | --- |
| Population need index | 0.30 | unavailable | TEST/SYNTHETIC index 0–100 when supplied |
| Infrastructure gap | 0.25 | unavailable | TEST/SYNTHETIC index 0–100 when supplied |
| Underserved-area indicator | 0.20 | unavailable | TEST/SYNTHETIC index 0–100 when supplied |
| Disaster / essential-service statistics | 0.25 | unavailable | TEST/SYNTHETIC flag mapped to 90 / 10 |

Unavailable components are omitted. Remaining **Need** weights are renormalized among available Need components.

If no Need component is available: Need Score is **INCONCLUSIVE** (`score = null`). Values are not invented.

**Not used as Need Score (by design):**

- historical MPLADS work count
- historical funding
- MP name as geography
- fabricated district / census / SC-ST composition

Constituency work counts may appear as **contextual evidence** with `used_as_need_score=false`. A constituency is not ranked lower because it has fewer recorded works.

### Impact Score

Impact components and prototype weights (sum 1.00):

| Component | Weight | REAL | HYBRID / SYNTHETIC |
| --- | ---: | --- | --- |
| Beneficiary count | 0.30 | unavailable | TEST/SYNTHETIC count → documented bands |
| Essential-service relevance | 0.30 | observed category + work description mapping | same mapping |
| Expected community coverage | 0.20 | unavailable | TEST/SYNTHETIC index 0–100 when supplied |
| Infrastructure gap | 0.20 | unavailable | TEST/SYNTHETIC index 0–100 when supplied |

Allocation amount is **not** an impact proxy.

Prototype beneficiary bands (not official):

| Count | Score |
| ---: | ---: |
| 0 | 0 |
| ≥ 1 | 20 |
| ≥ 100 | 40 |
| ≥ 500 | 55 |
| ≥ 1,000 | 70 |
| ≥ 5,000 | 85 |
| ≥ 10,000 | 95 |

Essential-service relevance is a documented prototype mapping from observed text (water / health / education / sanitation = 85; general public facility = 60; beautification / statue = 25). Unmatched category and description → component unavailable, not a default invented score.

### Urgency

Used only when actually supported:

- FUTURE/UNKNOWN lifecycle + `recommended_date` → prototype waiting-time bands to as-of 2026-09-10
- disaster-related words in observed work/category text
- TEST/SYNTHETIC `urgency_index` in HYBRID/SYNTHETIC when supplied

Urgency is **optional** in the combined Priority Score.

### Priority Score

```
Need weight    = 0.45
Impact weight  = 0.40
Urgency weight = 0.15
```

Need **and** Impact must both be assessable. Otherwise the recommended class is **INCONCLUSIVE** and no numeric Priority Score is forced.

If both Need and Impact are available:

```
Priority = Σ (w_i × score_i) / Σ w_i   for available dimensions among {Need, Impact, Urgency}
```

Recommended class:

| Priority Score | Class |
| --- | --- |
| ≥ 70 | HIGH PRIORITY |
| ≥ 40 and < 70 | MEDIUM PRIORITY |
| < 40 | LOW PRIORITY |
| Need or Impact unavailable | INCONCLUSIVE |

This is a decision-support priority, not an administrative sanction.

---

## Available vs unavailable inputs

### Available in REAL (observed extract)

- State, constituency (geographic only; chamber labels excluded)
- Category, work description
- Allocation amount (requested amount; unit unspecified)
- Status, recommendation date, lifecycle_stage derived from STATUS
- MP name (contextual / identity only)
- IDA
- Place text (city / ward / block / village) when present

### Unavailable in REAL (never invented)

- population
- infrastructure availability / gap statistics
- underserved-area indicators
- beneficiary counts
- expected community coverage
- disaster statistics / official declarations
- census or SC/ST composition
- district as a verified geographic field

### HYBRID / SYNTHETIC

Small controlled TEST/SYNTHETIC fixtures in `data/synthetic/need_impact_test_enrichment.json` (not a new large dataset; not merged into the real extract).

REAL mode never consumes those values.

---

## Ranking logic

`POST /api/v1/need-impact/rank` accepts candidate `project_ids` and an optional hypothetical budget.

1. Assess each candidate in the requested data mode.
2. INCONCLUSIVE works are **not forced** into the ranked list (`unranked`).
3. Rank assessable works by:
   1. Priority Score descending
   2. Evidence Confidence descending
   3. stable `project_id` ascending
4. Explain why a work is ranked above/below its neighbour.

---

## Budget simulation

Optional `available_budget` (same unspecified unit as allocation) or `available_budget_crore` (1 crore treated as 10,000,000 of that same unit, labelled as an assumption).

Greedy walk down the ranked list:

- if requested allocation ≤ remaining hypothetical budget → `within_hypothetical_budget=true`
- else → excluded from the simulated remainder, with note **“This is not a sanction denial.”**

No payment is executed. No sanction is written.

---

## Evidence objects

Engine `need`, version `need-impact-v1`.

| Type | Meaning |
| --- | --- |
| `NEED_ASSESSMENT` | Need Score, components, unavailable inputs |
| `IMPACT_ASSESSMENT` | Impact Score, components, unavailable inputs |
| `PRIORITY_ASSESSMENT` | Combined priority class and rationale |

Each object includes `project_id`, finding, score (nullable), confidence, source, provenance, `data_mode`, and explanation.

---

## Examples

### REAL missing census inputs

A proposed drinking-water work in Vizianagaram:

- Need Score: INCONCLUSIVE (population / infra / underserved unavailable)
- Impact Score: 85 (work-type essential-service relevance from observed category)
- Priority class: **INCONCLUSIVE**
- No fabricated population or beneficiary count

### HYBRID high-need / high-impact fixture

TEST/SYNTHETIC indexes around 88–92 plus 12,000 labelled beneficiaries:

- Need Score ≈ 90
- Impact Score high
- Priority class: **HIGH PRIORITY**
- Enrichment labelled TEST/SYNTHETIC

### Budget-constrained ranking

Hypothetical ₹50 crore, candidates P1 priority 91 (₹3,000,000) then P2 priority 40 (₹3,000,000) with remaining 4,000,000 after unit conversion of a small test budget:

- P1 inside hypothetical budget
- P2 exceeds remaining hypothetical budget
- Neither is sanctioned

---

## Limitations

- The current real MPLADS extract has no verified population, infrastructure-gap, or beneficiary dataset for every locality.
- Work-type essential-service relevance is not a census community-need measure.
- Prototype weights are not official MPLADS weights.
- Constituency coverage counts are contextual only.
- SYNTHETIC enrichment is for controlled testing only.
- Need & Impact is not Investigation Priority and is not a funding approval.

---

## Dual mode

| Mode | Inputs | Output label |
| --- | --- | --- |
| REAL | Observed extract fields only | INCONCLUSIVE Need unless a later verified need dataset exists; no synthetic values |
| HYBRID | Observed fields + labelled TEST/SYNTHETIC enrichment when a fixture exists | HYBRID / TEST/SYNTHETIC |
| SYNTHETIC | Synthetic test `project` rows | SYNTHETIC |

---

## Files

Engine: `backend/app/engines/need/`  
Evidence adapter: `backend/app/evidence/adapters/need.py`  
HTTP: `backend/app/api/routes/need.py`  
UI: Need & Impact section on the Project Digital Passport / Investigation Workspace, plus `/need-impact` ranking page.
