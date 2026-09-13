# Final End-to-End Demo Cases V1 report

Date: 2026-09-10  
Layer: `final-demo-cases-v1`  
HTTP:

- `GET /api/v1/demo-cases`
- `GET /api/v1/demo-cases/{case_id}` (`GHOST`, `OVERBILL` / `over-bill`, `STUCK`, `CLEAN`)

UI:

- `/demo` — Demo Cases launch panel
- `/demo/{caseId}` — guided journey for one case
- Existing Passport / Investigation Workspace opened with `?mode=hybrid&demo={case}`

Frozen and unchanged: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Risk Fusion V2 formula and weights, Relationship Graph V1, Need & Impact V1 scoring, Milestone Advisor V1, Jan-Sakshi V1, Investigation Copilot V1 retrieval/guardrails, Satellite V1, Geospatial V1, Image Evidence V1, Image Forensics V1, Documents/Blueprint V1, Plan → Claim → Evidence V1, End-to-End Lifecycle V1.

This slice is **application orchestration only**. It connects four existing controlled projects into an officer demonstration journey. It does **not** add an intelligence engine, does not rewrite formulas, does not generate a new dataset, does not sanction a project, and does not release funds.

Persistent notice on every demo surface:

> Controlled prototype scenario. Some values are synthetic and are not official MPLADS records.

---

## Architecture

```
Existing DEMO_INTERNAL_IDS (GHOST / OVERBILL / STUCK / CLEAN)
        +
Observed project identity (real MPLADS extract)
        +
Labelled HYBRID / SYNTHETIC enrichment (held-out, not official)
        +
Stored Evidence Objects, Lifecycle V1, Risk Fusion V2 (persist=False)
        ↓
GET /api/v1/demo-cases[/{id}]
        ↓
/demo launch panel → /demo/{case} journey
        ↓
PROJECT → PASSPORT → LIFECYCLE → INVESTIGATION → EVIDENCE
→ RISK → COPILOT → DECISION → SUMMARY
```

Risk Fusion V1.1 remains at `GET /api/v1/projects/{id}/risk`.  
Risk Fusion V2 remains at `GET /api/v2/projects/{id}/risk`.  
Demo Cases read V2 with `persist=False` and assert frozen version/weights.

Copilot suggested questions are prompts only. Answers use existing grounded retrieval. No hard-coded case scripts.

---

## Files created / changed

Created:

- `backend/app/demo/` (`constants.py`, `catalog.py`, `service.py`, `summary.py`, `errors.py`)
- `backend/app/domain/schemas/demo.py`
- `backend/app/api/routes/demo.py`
- `backend/tests/demo_fixtures.py`
- `backend/tests/test_demo_cases.py`
- `frontend/src/app/demo/page.tsx`
- `frontend/src/app/demo/[caseId]/page.tsx`
- `frontend/src/components/DemoCaseNotice.tsx`
- `frontend/src/components/DemoCaseLaunch.tsx`
- `frontend/src/components/DemoCaseJourney.tsx`
- `frontend/src/components/DemoCaseSummary.tsx`
- `frontend/src/components/DemoWorkflowBanner.tsx`
- `frontend/src/components/__tests__/DemoCases.test.tsx`
- `FINAL_DEMO_CASES_V1_REPORT.md`

Changed (wiring / chrome only):

- `backend/app/api/routes/__init__.py`
- `frontend/src/components/AppHeader.tsx`
- `frontend/src/components/OfficerDashboard.tsx`
- `frontend/src/lib/api.ts`, `frontend/src/lib/types.ts`, `frontend/src/lib/display.ts`
- `frontend/src/components/ui/statusBadge.ts`
- project layout banner when `?demo=` is present
- `ROADMAP.md` (Final Demo Cases V1 only)

Engines listed in the freeze list were not modified.

---

## Demo mode and labelling

Every case is a **controlled prototype scenario**.

| Label | Meaning |
| --- | --- |
| REAL | Observed MPLADS extract fields (identity, constituency, STATUS, allocation) |
| HYBRID | Real identity plus labelled SYNTHETIC enrichment |
| SYNTHETIC | Prototype enrichment or test fixture values; never official MPLADS records |
| DEMO | UI badge for the four demonstration cases |

HYBRID GPS, dates, expenditure, and progress are shown in a saffron-bordered SYNTHETIC panel. They are not presented as government records.

`fraud_conclusion`, `automatic_sanction`, `automatic_payment`, and `pfms_integrated` are always `false`. Officer actions are audited and do not change Investigation Priority or Evidence Confidence.

---

## Journey

Each case is executable from the main application:

1. Header **Demo Cases** or dashboard **Open Demo Cases**
2. Select GHOST / OVER-BILL / STUCK / CLEAN
3. Move through:

PROJECT → PASSPORT → LIFECYCLE → INVESTIGATION → EVIDENCE → RISK → COPILOT → DECISION → SUMMARY

Passport and Investigation Workspace are the existing pages, opened with `?mode=hybrid&demo={case}` so the persistent DEMO / HYBRID notice remains visible.

---

## Officer decision

| Lifecycle | Available actions | Effect |
| --- | --- | --- |
| COMPLETED (GHOST, OVER-BILL) | CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION | Audited investigation disposition. Scores unchanged. |
| ONGOING (STUCK) | Those investigation actions, plus milestone PROCEED / HOLD / INSPECT / NEED MORE INFORMATION on the existing Milestone panel | Does not release funds. No PFMS. |
| FUTURE (CLEAN) | PRIORITIZE / DEFER / NEED MORE INFORMATION | Planning simulation only. Not a sanction. |

No automatic sanction. No payment release.

---

## Live ingest database (2026-09-10 smoke)

The running SQLite extract contains the four controlled internal IDs. Demo Cases do **not** re-run Cost, Time, Overlap, Compliance, image, geo, satellite, citizen, or milestone engines. They assemble whatever is already stored plus labelled HYBRID enrichment display.

| Case | SQLite `id` | Scheme ID | Lifecycle | Stored Evidence Objects | Risk Fusion V2 | Lifecycle recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| GHOST | 53637 | SVK-AP-001057 | COMPLETED | 0 | IP 0 / EC 0 / NEED_MORE_INFORMATION / INSUFFICIENT_EVIDENCE | INCONCLUSIVE |
| OVER-BILL | 22177 | SVK-AP-003337 | COMPLETED | 0 | IP 0 / EC 0 / NEED_MORE_INFORMATION / INSUFFICIENT_EVIDENCE | INCONCLUSIVE |
| STUCK | 52862 | SVK-AP-001446 | ONGOING | 0 | IP 0 / EC 0 / NEED_MORE_INFORMATION / INSUFFICIENT_EVIDENCE | NEED MORE INFORMATION |
| CLEAN | 26946 | SVK-AP-003286 | FUTURE | 5 | IP 20 / EC 29 / MONITOR / INCONCLUSIVE | NEED MORE INFORMATION |

This is intentional honesty. Expected demonstration directions (REVIEW / INSPECT, HOLD, MONITOR / PROCEED) are **not forced**. Where stored Evidence Objects are missing, SARVSAKSHI says NEED MORE INFORMATION / INCONCLUSIVE.

Backend tests seed labelled HYBRID plan / claim / evidence through **existing** PCE, milestone, and Evidence Object APIs so the four journeys can be verified with Evidence Object IDs. That fixture is not a new government dataset.

---

## 1. GHOST

**Purpose:** Demonstrate a location / evidence-integrity concern.

**Project (live extract):**

- Scheme ID: `SVK-AP-001057`
- Internal Project ID: `internal:464569d6e0e8fa677cd826b350df9c2c0bd680a7665587cadd63e93e2b357d29`
- SQLite id: `53637`
- Constituency: VIZIANAGARAM
- Source status: Completed
- Lifecycle: COMPLETED / FINAL_INVESTIGATION
- Allocation: ₹73,78,000
- Work: Purchase of prosthetics, wheel chairs, tricycles, hearing aids (observed description)
- Data reliability: **HYBRID**

**Initial claim:** Work is reported completed in the observed STATUS field.

**Available plan / enrichment (labelled SYNTHETIC, not official):**

- Planned start 2023-08-02, planned completion 2024-01-14, actual completion 2024-01-20
- Expenditure 72,42,167
- Progress 100%
- GPS `10.05, 68.4` (held-out DEMO_GHOST coordinates; far from Vizianagaram context)

**Evidence (live ingest):** no stored Evidence Objects. Geospatial status NOT AVAILABLE. Satellite SATELLITE_UNAVAILABLE. Images / documents / citizen / milestone not recorded. PCE INCONCLUSIVE (plan/claim/evidence not recorded on this project).

**Risk Fusion V2 (unchanged formula, persist=False):** Investigation Priority 0, Evidence Confidence 0, NEED_MORE_INFORMATION, INSUFFICIENT_EVIDENCE.

**Copilot (grounded, not hard-coded):** Suggested question *“Why is this project being recommended for inspection?”* Answered from stored facts: COMPLETED / FINAL_INVESTIGATION, Investigation Priority 0 because no assessable intelligence signals were available to fuse. Recommended action NEED MORE INFORMATION. No evidence IDs (none stored). No “fraud confirmed”.

**Recommendation (actual):** INCONCLUSIVE / NEED MORE INFORMATION.

**Officer decision (live):** not recorded. COMPLETED actions CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION remain available and auditable.

**Expected demonstration outcome:** REVIEW / INSPECT **if** image, GPS, and geospatial Evidence Objects are present.

**Actual demonstration outcome on live ingest:** NEED MORE INFORMATION, because those engines have not been persisted for this project. The labelled SYNTHETIC GPS is shown so an officer can see why a location check would be the next inspection step. Not a legal finding.

**REAL / HYBRID:** HYBRID. Base identity is real. GPS/dates/expenditure are SYNTHETIC enrichment.

**Limitations:** Live database has no image/forensics/geo Evidence Objects for this ID. Demo Cases do not invent them. Tests seed labelled geo/image evidence for the same internal ID.

---

## 2. OVER-BILL

**Purpose:** Demonstrate a financial / expenditure inconsistency.

**Project (live extract):**

- Scheme ID: `SVK-AP-003337`
- Internal Project ID: `internal:eab396eafd121f6c8426cb285be2078aa7cfc6fe718050d6eb7340208318e762`
- SQLite id: `22177`
- Constituency: ELURU
- Source status: Completed
- Lifecycle: COMPLETED / FINAL_INVESTIGATION
- Allocation (observed): ₹35,50,000
- Work: Establishing public lift irrigation projects
- Data reliability: **HYBRID**

**Initial claim:** Work is reported completed; HYBRID enrichment supplies expenditure for prototype testing.

**Available plan / enrichment (labelled SYNTHETIC, not official):**

- Expenditure 63,90,000 (above observed allocation)
- Progress 100%
- GPS 16.766328, 81.154918
- Planned 2023-12-24 to 2024-08-29; labelled actual completion 2024-06-30

**Evidence (live ingest):** 0 stored Evidence Objects. PCE INCONCLUSIVE (plan not recorded on the project row). Milestone not recorded. Cost / Compliance engines exist but were not persisted for this ID in the current ingest.

**Risk Fusion V2:** IP 0 / EC 0 / NEED_MORE_INFORMATION / INSUFFICIENT_EVIDENCE.

**Copilot:** Suggested question *“What financial evidence supports the concern?”* Grounded answer: that information is not available in the current evidence; no stored Evidence Objects. Recommended action NEED MORE INFORMATION. No hard-coded over-bill script.

**Recommendation (actual):** INCONCLUSIVE / NEED MORE INFORMATION.

**Officer decision (live):** not recorded. CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION available.

**Expected demonstration outcome:** REVIEW / HOLD / INSPECT where Cost, Compliance, PCE, and Milestone actually support it.

**Actual demonstration outcome on live ingest:** NEED MORE INFORMATION. The labelled SYNTHETIC expenditure vs observed allocation is displayed and flagged as not official. Engine results were not mutated to force a high score.

**REAL / HYBRID:** HYBRID.

**Limitations:** Expenditure is SYNTHETIC enrichment, not an official PFMS figure. Without persisted Cost/Compliance/PCE objects, V2 cannot fuse a financial concern.

---

## 3. STUCK

**Purpose:** Demonstrate schedule / progress / milestone risk.

**Project (live extract):**

- Scheme ID: `SVK-AP-001446`
- Internal Project ID: `internal:639b82094c0b023fa8fd1047f88e87a608a92f59442a74bf086ab25d4a2274c5`
- SQLite id: `52862`
- Constituency: ANANTAPUR
- Source status: Ongoing
- Lifecycle: ONGOING
- Allocation: ₹10,00,000
- Work: Construction of additional rooms and halls in an existing public/community building
- Data reliability: **HYBRID**

**Initial claim:** Work is ongoing with low claimed progress in labelled HYBRID enrichment.

**Available plan / enrichment (labelled SYNTHETIC, not official):**

- Planned start 2023-09-02, planned completion 2024-04-11
- Actual completion: none
- Progress 12%
- Expenditure 1,08,000
- GPS 14.727152, 77.603815

Dates are not fabricated as official MPLADS records.

**Evidence (live ingest):** 0 stored Evidence Objects. Time / milestone / PCE not persisted. PCE INCONCLUSIVE. Satellite unavailable. Citizen NOT AVAILABLE.

**Risk Fusion V2:** IP 0 / EC 0 / NEED_MORE_INFORMATION.

**Copilot:** Suggested question *“Why is this milestone being held?”* Intent MILESTONE. Answer: milestone recommendation is not available in the current evidence; this does not release funds. Recommended action NEED MORE INFORMATION.

**Recommendation (actual):** NEED MORE INFORMATION.

**Officer decision (live):** not recorded. Investigation CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION, plus milestone PROCEED / HOLD / INSPECT on the existing Milestone Advisor panel.

**Expected demonstration outcome:** INSPECT / HOLD where Time Intelligence, PCE, and Milestone Advisor actually support it.

**Actual demonstration outcome on live ingest:** NEED MORE INFORMATION. Labelled overdue/low-progress enrichment is shown so the officer can see what would be inspected next.

**REAL / HYBRID:** HYBRID.

**Limitations:** No stored Time or Milestone Evidence Objects on this ID in the live ingest. Tests seed a labelled milestone for the same internal ID.

---

## 4. CLEAN

**Purpose:** Demonstrate that SARVSAKSHI does **not** flag every project.

**Project (live extract):**

- Scheme ID: `SVK-AP-003286`
- Internal Project ID: `internal:e714d635eb46ac65589489b3972d8cf896f9c2b7baaaeb753bf3e312929fc3b9`
- SQLite id: `26946`
- Constituency: KADAPA
- Source status: Sanctioned
- Lifecycle: FUTURE / PRIORITIZATION
- Allocation: ₹35,00,000
- Work: Construction of culverts and bridges
- Data reliability: **HYBRID**

**Initial claim:** Ordinary sanctioned work with supporting plan, claim, and evidence when recorded.

**Available plan / enrichment (labelled SYNTHETIC):** GPS 14.451364, 78.831066; expenditure 0; progress 0; planned 2024-06-23 to 2024-12-24.

**Evidence (live ingest) — stored Evidence Object IDs:**

- `ev:compliance:26946:mplads_compliance:HYBRID:4a1f407e96a7f604`
- `ev:cost:26946:allocation_cost_anomaly:REAL:4805ffc568af91e2`
- `ev:graph:26946:relationship_graph:HYBRID:788e1243c78a8531`
- `ev:overlap:26946:potential_overlap:HYBRID:feadf0c6b767d54c`
- `ev:time:26946:time_anomaly:REAL:bf7672fbd8129c32`

PCE INCONCLUSIVE (plan/claim not recorded). Image / geo / citizen / milestone not recorded. Satellite SATELLITE_UNAVAILABLE. Need & Impact INCONCLUSIVE (population/infrastructure inputs unavailable; not invented).

**Risk Fusion V2:** Investigation Priority **20**, Evidence Confidence **29**, recommended action **MONITOR**, explanation type INCONCLUSIVE. Score is **not** forced to zero.

**Risk Fusion V1.1 (unchanged, separate endpoint):** IP 58 / EC 60 / INSPECT on this same project. Demo Cases display V2. Copilot currently cites stored V1 context when answering a general “why not escalated” question (Copilot retrieval was not modified in this slice).

**Copilot:** Suggested question *“Why was this project not escalated?”* Grounded answer referenced stored Cost, Compliance, Overlap, and Graph Evidence Object IDs. No legal fraud wording. Recommended action from Copilot reflected stored V1 context (MONITOR vs INSPECT difference documented as V1/V2 dual display, not a Demo Cases mutation).

**Recommendation (actual):** V2 MONITOR; lifecycle NEED MORE INFORMATION because Need & Impact cannot both be assessed.

**Officer decision (live):** `need_more_info` already recorded. FUTURE actions PRIORITIZE / DEFER / NEED MORE INFORMATION remain available. Not a sanction.

**Expected demonstration outcome:** MONITOR / PROCEED where supported.

**Actual demonstration outcome:** V2 MONITOR with a non-zero score. FUTURE workflow still NEED MORE INFORMATION on Need & Impact. This shows the system does not auto-escalate every work and does not auto-prioritize when inputs are missing.

**REAL / HYBRID:** HYBRID (Cost and Time objects include REAL-mode rows; Compliance/Overlap/Graph objects are HYBRID).

**Limitations:** Image, geospatial, and citizen evidence are not stored on this live row. Need & Impact remains INCONCLUSIVE. Copilot may quote V1 scores while the Demo Cases summary quotes V2; both engines are frozen and were not rewritten.

---

## Summary table

| Case | Main Signal | Evidence | Recommendation | Officer Decision |
| --- | --- | --- | --- | --- |
| GHOST | Location-integrity scenario; labelled SYNTHETIC GPS `10.05, 68.4`; no fused assessable groups in live ingest | 0 stored objects (live). Tests seed labelled geo/image IDs. | INCONCLUSIVE / NEED MORE INFORMATION (expected direction REVIEW / INSPECT not forced) | Not recorded; CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION |
| OVER-BILL | Labelled SYNTHETIC expenditure ₹63.90 lakh vs observed allocation ₹35.50 lakh | 0 stored objects (live). Tests seed Cost / Compliance / PCE. | INCONCLUSIVE / NEED MORE INFORMATION (expected REVIEW / HOLD / INSPECT not forced) | Not recorded; CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION |
| STUCK | Labelled SYNTHETIC 12% progress and planned end 2024-04-11; no stored Time/Milestone objects | 0 stored objects (live). Tests seed Time / Milestone. | NEED MORE INFORMATION (expected INSPECT / HOLD not forced) | Not recorded; milestone PROCEED / HOLD / INSPECT available |
| CLEAN | Cost, Compliance, Overlap, Graph assessable; V2 does not escalate | 5 Evidence Object IDs listed above | V2 MONITOR (IP 20 / EC 29); lifecycle NEED MORE INFORMATION | NEED MORE INFORMATION (existing); PRIORITIZE / DEFER remain available |

---

## Evidence traceability

Important conclusions on the Demo Cases journey list supporting Evidence Object IDs in the EVIDENCE section and FINAL CASE SUMMARY. Where the live ingest has none, the UI states that explicitly instead of inventing IDs.

Why SARVSAKSHI recommended an action can be read from:

- Risk Fusion V2 contributing groups and `evidence_ids`
- Stored Evidence Object IDs
- Labelled SYNTHETIC enrichment panel (GPS, expenditure, progress)
- Missing-information list
- Copilot citations (same retrieval as Investigation Copilot V1)

Judges should not rely on Copilot alone.

---

## Copilot

Suggested questions (prompts only):

| Case | Examples |
| --- | --- |
| GHOST | Why is this project being recommended for inspection? What location evidence supports the concern? |
| OVER-BILL | What financial evidence supports the concern? What did Compliance report? |
| STUCK | Why is this milestone being held? Why is Time Intelligence concerned? |
| CLEAN | Why was this project not escalated? Why is this project not flagged? |

`hardcoded_answers` is false. `grounded_retrieval` is true. Investigation Copilot V1 was not given special demo scripts.

---

## Testing

Backend (`pytest`, 2026-09-10): **667 passed**.

Frontend (`vitest`, 2026-09-10): **100 passed**.

Next.js production build: **passed** (`/demo`, `/demo/[caseId]` present).

Covered for all four cases (fixture database):

- catalog IDs match existing `DEMO_INTERNAL_IDS`
- search by internal project ID
- project loading / passport / lifecycle / V2 risk / evidence / PCE
- GHOST geo/image/satellite presence in fixture
- OVER-BILL cost, compliance, PCE, milestone
- STUCK time/milestone and HOLD/INSPECT actions
- CLEAN score not forced to zero; matches `assess_project_risk_v2(..., persist=False)`
- Copilot grounded answers with Evidence IDs on fixture GHOST
- officer CONFIRM CONCERN does not mutate V2 scores
- no “fraud confirmed”, no `automatic_sanction: true`, no payment/PFMS flags
- Risk Fusion V2 version and weights still equal the frozen constants

---

## Browser / HTTP smoke (2026-09-10)

Interactive Cursor browser tools were not available in this session. Port 3000 already served the Next.js app. HTTP smoke against the running UI and API:

| URL | HTTP | fraud confirmed | PFMS payment | DEMO notice / demo chrome |
| --- | --- | --- | --- | --- |
| `/demo?mode=hybrid` | 200 | no | no | yes |
| `/demo/ghost?mode=hybrid` | 200 | no | no | yes |
| `/demo/overbill?mode=hybrid` | 200 | no | no | yes |
| `/demo/stuck?mode=hybrid` | 200 | no | no | yes |
| `/demo/clean?mode=hybrid` | 200 | no | no | yes |
| `/projects/53637?mode=hybrid&demo=ghost` | 200 | no | no | yes |
| `/projects/22177/investigate?mode=hybrid&demo=overbill` | 200 | no | no | yes |
| `/projects/52862/investigate?mode=hybrid&demo=stuck` | 200 | no | no | yes |
| `/projects/26946?mode=hybrid&demo=clean` | 200 | no | no | yes |

API `GET /api/v1/demo-cases` listed all four cases as available. Copilot chat on GHOST/OVER-BILL/STUCK/CLEAN returned grounded NEED MORE INFORMATION or MONITOR language with no legal fraud conclusion.

**Not verified interactively:** click-through of every button inside a headed browser. Closest substitute: HTTP page load + live API payloads for all four cases.

**Recorded issues:**

1. Live ingest has **no stored Evidence Objects** for GHOST, OVER-BILL, and STUCK, so V2 is INSUFFICIENT_EVIDENCE. Expected REVIEW/INSPECT/HOLD directions are shown as “not forced”.
2. CLEAN Copilot may quote Risk Fusion **V1.1** (IP 58) while Demo Cases / `GET /api/v2/.../risk` show **V2** (IP 20). Copilot was not modified. Both formulas remain frozen.
3. CLEAN already has an officer `need_more_info` row in the live database.

No runtime 5xx on the smoked pages. No score mutation from Demo Cases assembly.

---

## Governance checks

- No legal fraud wording in catalog, API, UI copy, or Copilot answers smoked
- SYNTHETIC values labelled; persistent prototype notice shown
- Officer decision does not modify model calculations
- No automatic sanction
- No payment release / PFMS integration
- Module links use existing Passport, Investigation Workspace, Relationship Graph, and Copilot panels
- Risk Fusion V2 version/weights asserted unchanged at request time

---

## Limitations

- Demo Cases do not generate or persist new intelligence. Sparse live evidence produces INCONCLUSIVE / NEED MORE INFORMATION, which is the correct prototype behaviour.
- HYBRID GPS, dates, expenditure, and progress are held-out SYNTHETIC enrichment from the existing synthetic layer, not a new dataset and not official MPLADS.
- CLEAN is FUTURE (Sanctioned → FUTURE via existing STATUS mapping). Need & Impact remains the primary FUTURE workflow.
- Image, forensics, geospatial, satellite, Jan-Sakshi, and documents appear when those modules have actually stored outputs.
- No headed click-through browser automation in this session.

---

## What this slice did not do

- Did not redesign architecture
- Did not change any intelligence-engine formula
- Did not create a new intelligence engine
- Did not generate a large new dataset
- Did not force GHOST/OVER-BILL/STUCK into INSPECT or CLEAN into score zero
