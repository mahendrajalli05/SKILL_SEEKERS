# Plan–Claim–Evidence V1 report

Date: 2026-09-10  
Engine: `plan-claim-evidence-v1`  
HTTP:

- `POST /api/v1/projects/{id}/plan`
- `GET  /api/v1/projects/{id}/plan`
- `POST /api/v1/projects/{id}/claims`
- `GET  /api/v1/projects/{id}/claims`
- `POST /api/v1/projects/{id}/evidence` (attachment recording; existing GET evidence list is unchanged)
- `GET  /api/v1/projects/{id}/verification`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema, Risk Fusion V1.1, Relationship Graph V1, Search, Project Digital Passport, Investigation Workspace (except the new PCE section).

This slice compares **PLAN → CLAIM → EVIDENCE**. It produces **CONSISTENT**, **MISMATCH**, or **INCONCLUSIVE**. It does **not** determine fraud, does not invent unit rates, and does not fuse Investigation Priority.

---

## Architecture

```
Observed project fields (+ optional officer plan overlay)
        ↓
PLAN (what the work is supposed to be)
        ↓
CLAIM (what the agency/contractor states)     EVIDENCE attachments
        ↓                                              ↓
        └──────── deterministic comparison engine ─────┘
                          ↓
              CONSISTENT / MISMATCH / INCONCLUSIVE
                          ↓
         Evidence Object (engine=pce, signal=plan_claim_evidence)
```

Attachments reuse the existing `document` / `photo` tables and the shared Evidence Object envelope (`document` / `image` engines). Verification results use `engine=pce`. `persist_evidence_object` still replaces one engine’s rows; attachments use additive `add_evidence_object` so multiple documents are not deleted.

Cost, Time, Overlap, Compliance, Fusion, and Graph scoring files were not modified. Fusion still maps only the four integrated signal types; PCE/document/image objects are stored and listed, not fused.

---

## Schema

New table `plan` (one overlay row per project):

| Field | Meaning |
| --- | --- |
| `project_id` | FK to `project` |
| `sanctioned_scope` | Officer-recorded scope when supplied |
| `budget_estimate` | Officer-recorded estimate when supplied |
| `blueprint_document_id` | Optional FK to `document` |
| `dimensions_value` / `dimensions_unit` | When supplied; otherwise unavailable |
| `milestone_label` / `milestone_amount` | When supplied |
| `planned_start_date` / `planned_completion_date` | When supplied |
| `source` | Provenance of the overlay |
| `data_mode` | `REAL` / `HYBRID` / `SYNTHETIC` |
| `provenance_json` | Required source trail |

Existing tables extended (additive `ALTER`, rows kept):

- `claim`: progress %, quantity, claim date, claimant, supporting document ids, `data_mode`, provenance
- `document`: filename, document type, source, hash, observed quantity/expenditure, `data_mode`, provenance
- `photo`: filename, source, observed quantity, `data_mode`, provenance (lat/lon/time/hash already existed)

REAL extract fields remain on `project`. District, vendor, GPS, expenditure, and dimensions are still not invented on `project`.

---

## Workflow

1. Officer opens Investigation Workspace → **Plan → Claim → Evidence**.
2. **PLAN** shows observed extract fields plus any recorded overlay. Unavailable government fields stay unavailable in REAL mode.
3. Officer may **record a claim** (a statement under evaluation, not a fact).
4. Officer may **attach** PDF, image, blueprint, BOQ, inspection, or citizen evidence with structured metadata. No OCR / satellite CV / image-authenticity engine.
5. **Run verification** (`GET .../verification`) compares available fields only.
6. Result, reasons, mismatches, and missing information are shown. SYNTHETIC overlay/enrichment fields are labelled.

---

## Comparison logic

Deterministic. Relative mismatch threshold: **10%**.

Quantity (two-sided): plan dimensions ↔ claimed quantity ↔ evidence quantity. Units must match; conversion is not performed.

Cost caps (one-sided overrun): claimed or evidence expenditure vs plan allocation/estimate and vs milestone amount. Underspend is not a mismatch (₹19 lakh vs ₹20 lakh is CONSISTENT; ₹14 lakh vs ₹15 lakh milestone is CONSISTENT).

Claim vs evidence expenditure remains two-sided (the two recorded amounts should agree).

Quantity-to-cost conversion is always **INCONCLUSIVE**: unit rates and material prices are not used.

Photo-only evidence without a recorded quantity cannot verify dimensions. Claimed 100% completion with insufficient evidence is INCONCLUSIVE, not a mismatch.

### Overall result

| Overall | Rule |
| --- | --- |
| **MISMATCH** | Any assessable comparison (except unit-rate conversion) is MISMATCH |
| **CONSISTENT** | No mismatch, at least one CONSISTENT comparison, and supporting evidence is attached |
| **INCONCLUSIVE** | Otherwise, including missing claim, missing evidence, or no comparable values |

---

## Result states

Allowed `overall_result` values: `CONSISTENT`, `MISMATCH`, `INCONCLUSIVE`.

Payload includes `plan_findings`, `claim_findings`, `evidence_findings`, `mismatches`, `missing_information`, local `evidence_confidence` (capped REAL 0.90 / HYBRID 0.72 / SYNTHETIC 0.55), `provenance`, and `explanation`.

Wording never includes a legal fraud conclusion.

---

## Data modes

| Mode | Plan / claim / evidence |
| --- | --- |
| REAL | Observed extract + REAL overlays/attachments only. HYBRID overlay is hidden. Enrichment is not consumed. |
| HYBRID | Real extract fields plus labelled SYNTHETIC enrichment (dates/milestones when present) and HYBRID overlays. |
| SYNTHETIC | Test rows (`project.is_synthetic`). Provenance must state SYNTHETIC. |

---

## Limitations

- No OCR, BOQ parsing, satellite CV, or image-authenticity scoring.
- Allocation unit in the extract remains unspecified; officer-recorded amounts are displayed in ₹ lakh only as a formatting convenience, not as an official unit.
- No unit-rate or SoR prices.
- One current plan overlay per project.
- Verification is not fused into Investigation Priority.
- Citizen/inspection attachments are recording-only; one citizen report is not treated as truth.

---

## REAL example

Live Andhra Pradesh work `id=234`, Scheme ID `SVK-AP-002021` (`GET /api/v1/projects/234/plan?data_mode=REAL`):

- Sanctioned scope from `project.work_description`: construction of buildings for multi-gym
- Budget/estimate from observed allocation: `500000` (unit unspecified in source)
- Dimensions: **unavailable** (not in the public extract; no overlay)
- REAL verification without a recorded claim or attachment: **INCONCLUSIVE**

---

## HYBRID example

Andhra Pradesh work `id=25533`, Scheme ID `SVK-AP-000005` (`GET .../plan?data_mode=HYBRID`), using existing enrichment only:

- Budget `194840` from the real extract (`synthetic=false`)
- Dimensions still unavailable
- SYNTHETIC: milestone `M4` / `56783`, planned start `2023-12-13`, planned completion `2024-03-28`
- Same project in REAL mode: planned start **unavailable**, no SYNTHETIC flags

---

## CONSISTENT / MISMATCH / INCONCLUSIVE (controlled)

From the V1 test fixtures (not additional synthetic bulk data):

**CONSISTENT** — Plan 2,000 sq.ft / ₹20 lakh; claim 1,950 sq.ft / ₹19 lakh; evidence 1,940 sq.ft / ₹19 lakh.

**MISMATCH** — Plan/claim 2,000 sq.ft completed; evidence quantity 800 sq.ft.

**INCONCLUSIVE** — Dimensions unavailable on plan and claim; photo only; or missing claim / missing evidence / missing expenditure.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 412 passed

cd frontend
npm test
# 39 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions asserted in tests: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `relationship-graph-v1`.

STOP. Copilot, Jan-Sakshi, Milestone Advisor, and Need & Impact were not built in this slice.
