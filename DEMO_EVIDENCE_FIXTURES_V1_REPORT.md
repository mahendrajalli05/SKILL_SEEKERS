# Demo Evidence Fixtures V1 report

Date: 2026-09-10  
Layer: `demo-evidence-fixtures-v1`  
HTTP: existing Demo Cases routes; fixtures attach through existing Evidence Object V1 APIs

Frozen and unchanged: real MPLADS project records, Cost Intelligence V1.1 formula, Time Intelligence V1 formula, Overlap Intelligence V1, Compliance V1 rules, Evidence Object V1 schema, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph V1, PCE comparison logic, Lifecycle orchestration logic.

This slice fixes the Final Demo Cases V1 integration gap: GHOST, OVER-BILL, and STUCK had **no stored Evidence Objects**, so Risk Fusion V2 correctly returned Investigation Priority 0 / NEED MORE INFORMATION even though labelled HYBRID demonstration context was visible. Fixtures are small, controlled, and explicitly labelled. They are **not** a new dataset and **not** official MPLADS evidence.

Persistent notice:

> Controlled prototype scenario. Some values are synthetic and are not official MPLADS records. DEMO / SYNTHETIC / CONTROLLED PROTOTYPE evidence fixtures are not official MPLADS evidence.

---

## Before / after

| | Before | After |
| --- | --- | --- |
| GHOST / OVER-BILL / STUCK | 0 stored Evidence Objects on live ingest | Controlled HYBRID Evidence Objects stored through Evidence Object V1 |
| CLEAN | 5 engine objects (Cost, Time, Overlap, Compliance, Graph) | Those objects kept, plus labelled supporting plan/claim/image/geo/citizen/milestone/PCE |
| Risk Fusion V2 | Empty storage → IP 0 / EC 0 / INSUFFICIENT_EVIDENCE | Unchanged formula consumes the attached objects |
| Copilot | Grounded retrieval found no IDs on GHOST / OVER-BILL / STUCK | Retrieves the stored Evidence Object IDs. No hard-coded demo scripts |

---

## Architecture

```
Existing DEMO_INTERNAL_IDS (GHOST / OVERBILL / STUCK / CLEAN)
        +
Existing HYBRID / SYNTHETIC enrichment (held-out, not official)
        ↓
Demo Evidence Fixtures V1 (idempotent)
  record_plan / record_claim
  assess_project_cost / time HYBRID_TEST / compliance HYBRID_TEST
  Image Evidence upload + forensics + geospatial + satellite mock (GHOST / CLEAN)
  Milestone Advisor create/assess (OVER-BILL / STUCK / CLEAN)
  Plan → Claim → Evidence verify persist
        ↓
Evidence Object V1 (evidence_id, project_id, finding, confidence, source, provenance, data_mode, engine/version)
        ↓
Risk Fusion V2 (unchanged formula, persist=False on demo assembly)
        ↓
Copilot grounded retrieval
        ↓
Officer decision (scores unchanged; no sanction; no payment)
```

Fixtures run when HYBRID Demo Cases are assembled if they are missing, and can be applied with `python -m app.demo.evidence_fixtures`. They do not rewrite project identity, allocation, status, or work description.

---

## Files created / changed

Created:

- `backend/app/demo/evidence_fixtures.py`
- `backend/app/demo/image_bytes.py`
- `backend/tests/test_demo_evidence_fixtures.py`
- `DEMO_EVIDENCE_FIXTURES_V1_REPORT.md`

Changed:

- `backend/app/demo/constants.py`, `service.py`, `__init__.py`
- `backend/app/domain/schemas/demo.py`
- `backend/tests/demo_fixtures.py`, `backend/tests/test_demo_cases.py`
- `frontend/src/components/DemoCaseNotice.tsx`, `DemoCaseJourney.tsx`
- `frontend/src/lib/display.ts`, `frontend/src/lib/types.ts`
- `frontend/src/components/__tests__/DemoCases.test.tsx`
- `data/demo/README.md`
- `ROADMAP.md` (this correction only)

Engines listed in the freeze list were not modified.

---

## Live ingest results (2026-09-10)

Applied to the existing SQLite extract. Project rows were not rewritten.

### 1. GHOST — SVK-AP-001057 / sqlite `53637` / COMPLETED / HYBRID

**Evidence created (16 IDs):**

- `ev:cost:53637:allocation_cost_anomaly:REAL:17785a7b5232127d`
- `ev:time:53637:time_anomaly:HYBRID:92b8eb0020b35e0d`
- `ev:compliance:53637:mplads_compliance:HYBRID:0c1c3cc3b5b3afa6`
- `ev:image:53637:IMAGE_POTENTIAL_REUSE:HYBRID:56b303c4ec3870a5`
- `ev:image:53637:IMAGE_METADATA:HYBRID:97b9c6fa520c4e56`
- `ev:image:53637:IMAGE_QUALITY:HYBRID:998c80a124c0c7d6`
- `ev:forensics:53637:IMAGE_FORENSIC_MANIPULATION:HYBRID:566683bc8be9f660`
- `ev:forensics:53637:IMAGE_FORENSIC_AI_GENERATION:HYBRID:4ec68ced4df9dd91`
- `ev:forensics:53637:IMAGE_FORENSIC_METADATA:HYBRID:194999a1956cfbf9`
- `ev:geo:53637:GEOSPATIAL_LOCATION_MISMATCH:HYBRID:49faa0057a11656c`
- `ev:geo:53637:GEOSPATIAL_LOCATION_MISMATCH:HYBRID:97ae57dfaf436abc`
- `ev:satellite:53637:SATELLITE_AVAILABILITY:HYBRID:6f1c4976388ce754`
- `ev:satellite:53637:SATELLITE_LOCATION:HYBRID:7ee2a1d607d630a1`
- `ev:satellite:53637:SATELLITE_CHANGE:HYBRID:7c120f8c9b1dea18`
- `ev:satellite:53637:SATELLITE_TEMPORAL:HYBRID:d59a9c1763b4fe50`
- `ev:pce:53637:plan_claim_evidence:HYBRID:315b9db391382712`

Chain exercised: Project → completion claim → SYNTHETIC image with reported EXIF GPS → geospatial LOCATION_MISMATCH vs labelled HYBRID project GPS `10.05, 68.4` → Evidence Objects → Risk Fusion V2.

**Risk Fusion V2 (unchanged formula):** Investigation Priority **25**, Evidence Confidence **26**, recommended action **NEED_MORE_INFORMATION**, explanation WHY_FLAGGED. Top groups: Cost 100, Geospatial LOCATION_MISMATCH, Satellite site-coverage concern, Forensics prototype manipulation signal.

V2 does not recommend INSPECT because Evidence Confidence is below the frozen 28 threshold. That is the actual formula result. Not forced.

**Copilot** (`Why is this project being recommended for inspection?`): grounded retrieval returned all 16 Evidence Object IDs. Recommended action NEED MORE INFORMATION. No “fraud confirmed”. Copilot may still quote stored Risk Fusion V1.1 context; V1.1 was not modified.

**Officer decision:** CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION remain audited. Tests confirm scores are unchanged. No automatic sanction. No payment.

**Data mode:** HYBRID. Labels DEMO / SYNTHETIC / CONTROLLED PROTOTYPE.

---

### 2. OVER-BILL — SVK-AP-003337 / sqlite `22177` / COMPLETED / HYBRID

**Evidence created (5 IDs):**

- `ev:cost:22177:allocation_cost_anomaly:REAL:a9f4511584603d4f`
- `ev:time:22177:time_anomaly:HYBRID:9a4e13c6745fa197`
- `ev:compliance:22177:mplads_compliance:HYBRID:793c36f72169459f`
- `ev:pce:22177:plan_claim_evidence:HYBRID:afb198508ae3ce22`
- `ev:milestone:22177:milestone:HYBRID:9a222ca53e42c84d`

Chain: Project → Plan → Claim (labelled expenditure ₹63.90 lakh vs observed allocation ₹35.50 lakh) → Compliance R004 → PCE MISMATCH → Milestone INSPECT → Risk Fusion V2.

**Risk Fusion V2:** Investigation Priority **9**, Evidence Confidence **21**, **NEED_MORE_INFORMATION**, explanation INCONCLUSIVE. Contributing groups: Compliance R004, PCE MISMATCH, Milestone INSPECT (low confidence). Missing weight is not redistributed.

**Copilot** (`What evidence supports the financial concern?`): retrieved Compliance, Milestone, and PCE Evidence Object IDs, including R004 expenditure vs sanctioned amounts. No hard-coded over-bill script. Recommended action NEED MORE INFORMATION.

**Officer decision:** CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION. Milestone INSPECT is a recommendation only. No PFMS.

**Data mode:** HYBRID.

---

### 3. STUCK — SVK-AP-001446 / sqlite `52862` / ONGOING / HYBRID

**Evidence created (5 IDs):**

- `ev:cost:52862:allocation_cost_anomaly:REAL:22c1313ac0c8999a`
- `ev:time:52862:time_anomaly:HYBRID:830dd5434e8fc827`
- `ev:compliance:52862:mplads_compliance:HYBRID:6d49112c78457b22`
- `ev:pce:52862:plan_claim_evidence:HYBRID:195328b517122d99`
- `ev:milestone:52862:milestone:HYBRID:1e2ca073aa3519f3`

Chain: Project → Plan dates → Claim 12% progress → Time Intelligence (schedule behind plan) → Milestone HOLD → Risk Fusion V2.

**Risk Fusion V2:** Investigation Priority **15**, Evidence Confidence **29**, recommended action **MONITOR**. Time group score 93 (WHY_FLAGGED). Lifecycle / Milestone Advisor recommendation is **HOLD**. V2 MONITOR vs milestone HOLD is not forced into one answer.

**Copilot** (`Why is this milestone being held?`): intent MILESTONE; retrieved `ev:milestone:52862:milestone:HYBRID:1e2ca073aa3519f3`; states HOLD and that this does not release funds.

**Officer decision:** investigation actions plus milestone PROCEED / HOLD / INSPECT / NEED MORE INFORMATION. No payment.

**Data mode:** HYBRID.

---

### 4. CLEAN — SVK-AP-003286 / sqlite `26946` / FUTURE / HYBRID

Existing Cost / Time / Overlap / Compliance / Graph objects were **kept**. Added labelled supporting plan, claim, image, geospatial consistency, citizen reports, satellite mock matching-location metadata, milestone, and PCE.

**Evidence count after fixtures:** 27 IDs, including the original five:

- `ev:cost:26946:allocation_cost_anomaly:REAL:4805ffc568af91e2`
- `ev:time:26946:time_anomaly:REAL:bf7672fbd8129c32`
- `ev:overlap:26946:potential_overlap:HYBRID:feadf0c6b767d54c`
- `ev:compliance:26946:mplads_compliance:HYBRID:4a1f407e96a7f604`
- `ev:graph:26946:relationship_graph:HYBRID:788e1243c78a8531`

plus citizen, image, forensics, geo LOCATION_CONSISTENCY, satellite, milestone, and PCE objects.

**Risk Fusion V2:** Investigation Priority **27**, Evidence Confidence **25**, **NEED_MORE_INFORMATION**, explanation CONFLICTING_EVIDENCE. Score is **not** forced to zero. V2 does not recommend INSPECT. FUTURE workflow remains Need & Impact / NEED MORE INFORMATION.

The previous live V2 on this row was IP 20 / MONITOR. Additional field objects changed the actual fused result. That is expected: V2 recomputes from the current evidence set. CLEAN still does not auto-escalate to INSPECT and does not auto-sanction.

**Copilot** (`Why was this project not escalated?`): retrieved the stored Evidence Object IDs. Recommended action MONITOR from stored V1.1 context. Copilot was not given a special CLEAN script.

**Officer decision:** PRIORITIZE / DEFER / NEED MORE INFORMATION. Not a sanction.

**Data mode:** HYBRID.

---

## Summary table

| Case | Evidence created | Risk Fusion V2 | Recommendation | Copilot | Officer decision | Data mode |
| --- | --- | --- | --- | --- | --- | --- |
| GHOST | 16 objects: image, forensics, geo mismatch, satellite mock, cost/time/compliance, PCE | IP 25 / EC 26 | NEED MORE INFORMATION (not forced to INSPECT) | Grounded; 16 IDs; no fraud wording | CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION | HYBRID |
| OVER-BILL | 5 objects: cost, time, compliance R004, PCE MISMATCH, milestone INSPECT | IP 9 / EC 21 | NEED MORE INFORMATION | Grounded financial IDs including R004 | Same investigation actions; milestone INSPECT is recommend-only | HYBRID |
| STUCK | 5 objects: time 93, cost, compliance, PCE, milestone HOLD | IP 15 / EC 29 MONITOR; lifecycle HOLD | MONITOR (V2) / HOLD (milestone) | Grounded milestone ID | Milestone HOLD/INSPECT available; no payment | HYBRID |
| CLEAN | 27 objects; original five retained | IP 27 / EC 25 | NEED MORE INFORMATION; score not zero; not INSPECT | Grounded IDs; MONITOR from stored V1.1 context | PRIORITIZE / DEFER / NEED MORE INFORMATION | HYBRID |

---

## Journey

PROJECT → PASSPORT → LIFECYCLE → PLAN → CLAIM → EVIDENCE → RISK → COPILOT → DECISION → SUMMARY

Evidence IDs on the EVIDENCE step and FINAL CASE SUMMARY are the stored Evidence Object IDs.

---

## Testing

Backend (`pytest`, 2026-09-10): **674 passed**.

Frontend (`vitest`, 2026-09-10): **100 passed**.

Next.js production build: **passed** (`/demo`, `/demo/[caseId]` present).

Re-run: `tests/test_demo_cases.py` and `tests/test_demo_evidence_fixtures.py` passed.

Covered:

- GHOST / OVER-BILL / STUCK / CLEAN have evidence
- Evidence IDs are `ev:`-prefixed and fused IDs are a subset of stored IDs
- REAL project identity (status, allocation, description, constituency) unchanged
- Extra non-demo project receives no fixtures
- HYBRID / SYNTHETIC / CONTROLLED PROTOTYPE labels visible
- Risk Fusion V2 consumes the objects with frozen weights
- Copilot retrieves evidence IDs; `hardcoded_answers` is false
- Officer CONFIRM CONCERN does not mutate V2 scores
- No “fraud confirmed”, no `automatic_sanction: true`, no payment/PFMS flags

---

## Browser / HTTP smoke (2026-09-10)

Interactive headed browser tools were not available. Closest substitute: live API + UI HTTP against already-bound ports 8000 and 3000.

| Surface | Result |
| --- | --- |
| `GET /api/v1/demo-cases/{GHOST,OVERBILL,STUCK,CLEAN}?data_mode=HYBRID` | 200; evidence counts 16 / 5 / 5 / 27; V2 as table above; `fraud_conclusion=false` |
| `/demo/overbill`, `/demo/stuck`, `/demo/clean` | 200; DEMO notice present; no “fraud confirmed”; no PFMS payment wording |
| `/demo/ghost` on the already-running Next.js process | 500 (`Cannot find module './611.js'` stale `.next` on port 3000). Production `npm run build` succeeded. |

Officer-decision click-through was verified in backend tests, not in a headed browser.

---

## Governance checks

- No legal fraud wording in fixtures, API assembly, or Copilot answers captured
- SYNTHETIC / DEMO / CONTROLLED PROTOTYPE labelled; persistent prototype notice shown
- Officer decision does not modify model calculations
- No automatic sanction
- No payment release / PFMS integration
- Risk Fusion V2 version and weights asserted unchanged
- Real MPLADS extract rows were not rewritten

---

## Limitations

- HYBRID GPS, dates, expenditure, progress, images, and satellite mock metadata are labelled SYNTHETIC prototype values, not official MPLADS records.
- Satellite uses the existing HYBRID TEST mock provider (`wrong_location` for GHOST, `matching_location` for CLEAN). Not live imagery.
- GHOST V2 remains NEED MORE INFORMATION because Evidence Confidence 26 is below the frozen V2 threshold of 28. Expected demonstration direction REVIEW / INSPECT was not forced.
- OVER-BILL V2 remains NEED MORE INFORMATION (IP 9 / EC 21). Compliance R004 and PCE MISMATCH are visible; missing group weights are not redistributed.
- STUCK V2 is MONITOR while Milestone Advisor is HOLD. Both are actual engine outputs.
- CLEAN supporting images can emit Image Evidence `POTENTIAL_IMAGE_REUSE` because two SYNTHETIC fixture JPEGs are stored on the same project. Geospatial is LOCATION_CONSISTENCY. V2 is not forced to zero and is not INSPECT.
- Copilot may quote Risk Fusion V1.1 while Demo Cases display V2. Copilot retrieval/guardrails were not rewritten.
- Idempotent fixture apply on HYBRID demo assembly writes through existing APIs; REAL mode does not attach HYBRID fixtures.

---

## What this slice did not do

- Did not change real MPLADS project records
- Did not change Cost, Time, Overlap, Compliance, PCE, or Lifecycle logic
- Did not change the Evidence Object schema
- Did not change Risk Fusion V1.1 or the Risk Fusion V2 formula/weights
- Did not create a large synthetic dataset
- Did not create fake official government records
- Did not hard-code demo risk scores or Copilot answers
- Did not bypass Evidence Objects

STOP.
