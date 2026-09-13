# Milestone Advisor V1 report

Date: 2026-09-10  
Engine: `milestone-advisor-v1`  
HTTP:

- `GET  /api/v1/projects/{id}/milestones`
- `POST /api/v1/projects/{id}/milestones`
- `GET  /api/v1/milestones/{milestone_id}`
- `POST /api/v1/milestones/{milestone_id}/assess`
- `POST /api/v1/milestones/{milestone_id}/decision`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, Project Digital Passport structure, Investigation Workspace (except the new Milestones section), Plan → Claim → Evidence V1 comparison logic, Document & Blueprint Intelligence V1, Image Evidence & Authenticity V1, Geospatial Consistency V1, Need & Impact V1.

This slice adds a **milestone-based decision-support workflow**. It recommends whether a work appears ready to proceed to the next milestone from available Plan, Claim, and Evidence. It does **not** release funds, approve or sanction payments, integrate with PFMS, or change Risk Fusion scores.

---

## Architecture

```
Officer-recorded milestone (workflow only; not an official MPLADS status)
        ↓
PLAN (existing overlay / extract) + CLAIM + EVIDENCE attachments
        ↓
Existing Plan → Claim → Evidence comparison (reused, not rewritten)
        +
Stored Evidence Objects (Cost / Time / Overlap / Compliance / Image / Geo)
        +
Stored FusionScore snapshot (display only; not a driver)
        ↓
Deterministic recommendation: PROCEED / HOLD / INSPECT / INCONCLUSIVE
        ↓
Evidence Object V1 (engine=milestone, signal=milestone)
        ↓
Officer action: PROCEED / HOLD / INSPECT / NEED MORE INFORMATION
        ↓
Audit trail. Investigation Priority and Evidence Confidence unchanged.
```

Milestone Advisor is its **own decision-support layer**. It does not add milestone weighting to Risk Fusion V1.1. Fusion still treats milestone as `NOT_YET_INTEGRATED`.

There is **no** payment, PFMS, or automatic-sanction endpoint.

---

## Milestone schema

New tables `milestone` and `milestone_decision`. Additive only. Existing rows are kept.

### `milestone`

| Field | Meaning |
| --- | --- |
| `id` (`milestone_id`) | SQLite surrogate. Not an official MPLADS milestone ID |
| `project_id` | FK to `project` |
| `milestone_number` | Optional order (1, 2, 3, …) |
| `milestone_name` | Optional label (default M1–M4) |
| `description` | Optional |
| `planned_amount` | Optional planned/sanctioned amount for this milestone |
| `cumulative_amount` | Sum of planned amounts for this and earlier numbered milestones |
| `target_date` | Optional planned date |
| `completion_claimed` | Optional claimed completion flag |
| `claimed_progress` | Optional claimed progress percent |
| `claimed_expenditure` | Optional claimed expenditure. REAL missing values stay unavailable |
| `status` | SARVSAKSHI workflow state |
| `data_mode` | `REAL` / `HYBRID` / `SYNTHETIC` |
| `provenance_json` | Required source trail |
| `claim_id` / `document_ids` / `photo_ids` | Optional links into existing PCE tables |
| `recommendation` | Last assessment: PROCEED / HOLD / INSPECT / INCONCLUSIVE |
| `assessment_json` | Last explanation payload |
| `synthetic` | True when values are labelled SYNTHETIC |
| `officer_action` / `officer_reason` / `officer_acted_at` | Last recorded officer action |

Workflow states (not official MPLADS status values):

`PLANNED` · `CLAIMED` · `UNDER_REVIEW` · `PROCEED` · `HOLD` · `INSPECT` · `COMPLETED`

### `milestone_decision`

Stores the officer action, reason, actor, data mode, and Investigation Priority / Evidence Confidence snapshots. `scores_unchanged` is always intended to be true. The write path refuses to complete if fusion scores changed.

---

## Recommendation logic

Evidence-first. Investigation Priority alone never produces INSPECT or HOLD.

Inputs:

- Plan → Claim → Evidence overall result (`CONSISTENT` / `MISMATCH` / `INCONCLUSIVE`)
- required attachments (document or progress image)
- geospatial location mismatch (stored Geo Evidence Object)
- image exact duplicate / potential reuse (stored Image Evidence Object)
- expenditure inconsistency vs planned amount or evidence amount (10% relative threshold reused from PCE)
- claimed vs evidence-supported progress, when both exist and PCE is not already a mismatch
- Time Intelligence schedule mismatch (stored Time Evidence Object; Time V1 is not recalculated)
- Cost / Compliance / Overlap flags as supporting intelligence only

| Recommendation | Rule |
| --- | --- |
| **INSPECT** | Location mismatch, potential reused/duplicate image, two or more independent milestone concerns, or a milestone concern plus a flagged intelligence signal |
| **HOLD** | Plan–Claim–Evidence MISMATCH; claim without required evidence; expenditure/progress inconsistency; schedule mismatch |
| **PROCEED** | Claim recorded, required evidence present, PCE CONSISTENT, no unresolved critical mismatch |
| **INCONCLUSIVE** | Otherwise, including missing claim and missing evidence, or REAL missing execution/financial information |

Quantity mismatch is counted once via PCE. It is not also counted as a separate progress inconsistency.

Outputs never include FRAUD, FRAUD DETECTED, or FRAUD PROBABILITY.

Every response states:

> Milestone recommendation only. Authorized officials make the final administrative decision. SARVSAKSHI does not release funds.

And:

> No payment was executed. This prototype does not integrate with PFMS and does not release or sanction funds.

`funds_released`, `payment_executed`, `automatic_sanction`, and `pfms_integrated` are always `false`.

---

## Evidence inputs

Reuses existing systems. No second evidence store.

| Input | Source |
| --- | --- |
| Plan / Claim / Evidence | Existing PCE tables and `compare_plan_claim_evidence` |
| Documents / blueprint / BOQ | Existing `document` rows |
| Progress images / metadata / reuse | Existing `photo` rows and Image Evidence Objects |
| Geospatial consistency | Stored Geo Evidence Objects |
| Time / Cost / Compliance / Overlap | Stored Evidence Objects. Engines are not modified |
| Risk Fusion | Read-only `fusion_score` snapshot for display |
| Officer observations | Recorded on `milestone_decision` |

---

## Officer workflow

Buttons on the Investigation Workspace:

- PROCEED
- HOLD
- INSPECT
- NEED MORE INFORMATION

These are SARVSAKSHI workflow decisions. They do **not**:

- release money
- approve a PFMS payment
- alter Investigation Priority or Evidence Confidence
- alter Cost / Time / Overlap / Compliance / Fusion outputs

NEED MORE INFORMATION sets status `UNDER_REVIEW` and leaves the system recommendation unchanged.

---

## Amounts and progress

- Milestone planned amount
- Cumulative planned amount (this milestone and earlier numbers)
- Remaining planned amount (`total planned − cumulative`) when both are available
- Claimed expenditure when recorded

REAL: missing expenditure remains unavailable. Synthetic enrichment is not consumed.

HYBRID: synthetic expenditure / milestone amounts remain labelled SYNTHETIC.

Progress:

- claimed progress
- evidence-supported progress when plan quantity and evidence quantity exist
- planned progress from milestone number / last number
- schedule mismatch from stored Time Intelligence

Time Intelligence V1 is not rebuilt.

---

## REAL vs HYBRID

| Mode | Behaviour |
| --- | --- |
| REAL | Observed extract + REAL recorded milestones/claims/evidence only. Missing execution and financial fields stay unavailable. HYBRID milestones are hidden. |
| HYBRID | Real work plus labelled SYNTHETIC milestone/execution values. Persistent notice shown. |
| SYNTHETIC | Test `project.is_synthetic` rows. Provenance must state SYNTHETIC. |

HYBRID persistent notice:

> Prototype simulation: some execution, financial, location, or milestone fields are synthetic and are not official MPLADS records.

---

## Frontend

Investigation Workspace → **Milestones**:

- Project, current milestone, planned amount, claimed progress, evidence status, risk/evidence summary, recommendation
- Timeline: M1 → M2 → M3 → M4 → COMPLETION (planned date, claim, evidence, result, officer action)
- WHY? supporting / conflicting / missing evidence and intelligence signals
- Officer buttons
- Governance and no-payment notes

Project Digital Passport shows a compact milestone status section. Unrelated pages were not redesigned.

---

## Controlled cases

Small fixtures only. No new bulk synthetic dataset.

**CASE 1 — PROCEED** — Plan 2,000 sq.ft / ₹20 lakh; claim 1,950 sq.ft / ₹19 lakh; evidence 1,940 sq.ft / ₹19 lakh. Claim supported. Recommendation **PROCEED**.

**CASE 2 — HOLD** — Plan/claim 2,000 sq.ft completed; evidence quantity 800 sq.ft. PCE mismatch. Recommendation **HOLD**.

**CASE 3 — INSPECT** — PCE mismatch plus stored geospatial location mismatch and potential image reuse. Recommendation **INSPECT**.

**CASE 4 — INCONCLUSIVE** — Milestone recorded with no claim and no attachments. Recommendation **INCONCLUSIVE**.

**CASE 5 — REAL MODE** — No claimed expenditure, no execution dates. Expenditure remains unavailable. Recommendation **INCONCLUSIVE**.

**CASE 6 — HYBRID MODE** — Synthetic planned amount and claimed expenditure labelled SYNTHETIC. REAL listing hides the HYBRID milestone. Hybrid notice is present.

Officer NEED MORE INFORMATION after PROCEED: status `UNDER_REVIEW`, recommendation unchanged, fusion scores unchanged.

---

## Limitations

- Milestone states are SARVSAKSHI workflow states, not official MPLADS status values.
- REAL public extract still has no verified expenditure, sanction date, or execution dates.
- Recommendations are decision-support only.
- SARVSAKSHI does not release funds and does not integrate with PFMS.
- Risk Fusion V1.1 is not reweighted with a milestone slot.
- Time / Cost / Compliance / Overlap are reused as stored inputs.
- No citizen portal, Copilot, satellite comparison, or graph visualization in this slice.

---

## Governance safeguards

- No FRAUD / FRAUD DETECTED / FRAUD PROBABILITY wording.
- No payment-release, PFMS, or automatic-sanction APIs.
- Officer actions snapshot fusion scores and refuse score mutation.
- SYNTHETIC values stay labelled.
- AI recommends. Authorized officers decide.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 532 passed (16 Milestone Advisor V1 tests)

cd frontend
npm test
# 47 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions asserted in tests: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `relationship-graph-v1`, `plan-claim-evidence-v1`, `document-blueprint-v1`, `image-evidence-v1`, `geospatial-consistency-v1`, `need-impact-v1`. Milestone engine: `milestone-advisor-v1`.

Interactive browser click-through was not available in this environment. PROCEED / HOLD / INSPECT / INCONCLUSIVE, REAL / HYBRID labelling, officer-action score immutability, and the absence of payment endpoints were verified through backend TestClient tests and frontend component tests.

---

## Files

Engine: `backend/app/engines/milestone/`  
Evidence adapter: `backend/app/evidence/adapters/milestone.py`  
HTTP: `backend/app/api/routes/milestone.py`  
UI: Milestones section on Investigation Workspace and compact status on the Project Digital Passport.

STOP. PFMS integration, actual payment release, citizen portal, Copilot, satellite comparison, and graph visualization were not built in this slice.
