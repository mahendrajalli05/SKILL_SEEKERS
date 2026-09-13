# Intelligence UI V1 report

Date: 2026-09-10  
Slice: officer Search + Project Digital Passport + Investigation Workspace  
Frozen engines: Cost V1.1, Time V1, Overlap V1, Compliance V1, Evidence Object V1, Risk Fusion V1.1, Relationship Graph V1

This slice turns the existing intelligence APIs into an officer-facing workflow. It does **not** recalculate Cost, Time, Overlap, Compliance, Evidence, Risk Fusion, or Relationship Graph scores in the frontend. It does **not** output a fraud probability or a legal finding.

---

## What was built

### 1. Project Search

Officer search over **observed real fields only**:

- text: `internal_project_id`, work description, MP name
- filters: constituency, category, status, state
- pagination

Results show project, constituency, category, status, allocation, and recommendation date. Blank observed values render as **Unavailable**. Allocation is labelled **unit unspecified**.

Not offered as filters (fields are not in the real extract):

- district
- vendor
- expenditure
- GPS
- sanction date
- completion date

HTTP:

- `GET /api/v1/projects` — paginated search
- `GET /api/v1/projects/options` — distinct observed filter values
- `GET /api/v1/projects/{id}` — identity plus availability metadata

### 2. Project Digital Passport

Reusable project page with:

A. Project identity (internal ID, kind, scheme, work, category, state, constituency, MP, IDA, status, house)  
B. Recommendation / finance (recommendation date, allocation, provenance, unspecified amount unit)  
C. Intelligence summary (Investigation Priority, Evidence Confidence, Cost / Time / Overlap / Compliance from existing APIs)  
D. Evidence objects (finding, score, confidence, source, data mode, explanation)  
E. Comparable projects from Cost and Overlap APIs  
F. Relationship summary (connected project count, MP, constituency, category, IDA, state, graph findings — **no visualization**)  
G. Availability / limitations (district, vendor, expenditure, GPS, sanction date, completion date listed as UNAVAILABLE)

### 3. Investigation Workspace

Officer layout:

- Top: identity, Investigation Priority, Evidence Confidence, recommended action (Monitor / Review / Inspect)
- Middle: why flagged, contributing and unavailable signals, evidence cards, comparables, relationship findings, compliance findings
- Bottom: evidence timeline/summary, data limitations, officer actions

Officer actions (stored as human decisions, never a legal fraud button):

- Confirm concern
- Dismiss
- Need more information

These write `officer_decision` and `audit_event`. They do **not** change Investigation Priority or Evidence Confidence.

HTTP:

- `GET /api/v1/projects/{id}/decisions`
- `POST /api/v1/projects/{id}/decisions`

---

## Data modes

The UI distinguishes **REAL**, **HYBRID**, and **SYNTHETIC**.

A work with a HYBRID enrichment row shows a visible notice that missing government fields are **SYNTHETIC prototype enrichment**, not official MPLADS data. REAL view hides HYBRID evidence. HYBRID/TEST view is opt-in via `?mode=hybrid`.

---

## Risk display

- Investigation Priority: 0–100 when assessed
- Evidence Confidence: 0–100 when assessed, shown separately
- Available / unavailable signals and explanations from Risk Fusion V1.1

`INSUFFICIENT_EVIDENCE`, `NOT_ASSESSABLE`, and `INCONCLUSIVE` are shown as unassessed labels. They are **not** displayed as an assessed score of 0.

Time Intelligence in REAL mode states:

> Time Intelligence unavailable because verified execution dates are not present in the current real dataset.

Fraud probability is not a response field and is not rendered.

---

## API consumption

The UI calls existing endpoints only:

| Need | Endpoint |
| --- | --- |
| Project | `GET /api/v1/projects/{id}` |
| Evidence | `GET /api/v1/projects/{id}/evidence` |
| Risk | `GET /api/v1/projects/{id}/risk` |
| Graph | `GET /api/v1/projects/{id}/graph` |
| Cost | `GET /api/v1/projects/{id}/cost-intelligence` |
| Time | `GET /api/v1/projects/{id}/time-intelligence` |
| Overlap | `GET /api/v1/projects/{id}/overlap-intelligence` |
| Compliance | `GET /api/v1/projects/{id}/compliance` |

New endpoints were added only for search listing, filter options, project availability metadata, and officer decisions.

---

## Frontend components

Reusable officer components:

- `RiskScoreCard`
- `EvidenceCard`
- `SignalCard`
- `ProjectHeader`
- `ComparableProjects`
- `RelationshipSummary`
- `OfficerDecisionPanel`
- `DataAvailabilityPanel`

Professional, responsive, no decorative animation.

---

## Tests and verification

Backend: all existing frozen-engine tests plus search, project-detail, and officer-decision tests.

Frontend: Vitest component tests for risk display, evidence cards, REAL vs HYBRID labelling, missing-field rendering, officer actions, and no “fraud confirmed” button.

`next build` succeeded.

Live API checks on the 56,138-row database:

| Check | Result |
| --- | --- |
| Search total | 56,138 works, paginated |
| Real project `31` | Unavailable fields listed; Time NOT_ASSESSABLE; Cost/Overlap/Compliance/Graph returned from existing engines; Risk has no `fraud_probability` |
| Hybrid demo `26946` (CLEAN) | `has_hybrid_enrichment=true`; HYBRID notice present; Time/Compliance/Overlap/Graph `HYBRID_TEST`; evidence modes REAL+HYBRID |
| Officer decision | `need_more_info` stored; Investigation Priority and Evidence Confidence unchanged; `fraud_confirmed` rejected 422 |

Frontend routes `/search`, `/projects/31`, and `/projects/26946/investigate` returned HTTP 200. Interactive click-through in a browser was not available in this environment; API and page-load checks were used instead.

---

## Not in this slice

- Graph visualization
- Plan / Claim / Evidence upload UI
- Documents, images, satellite
- Jan-Sakshi
- Milestone advisor
- Copilot
- Need & Impact
- Final four-case demo packaging

Cost, Time, Overlap, Compliance, Evidence Object, Risk Fusion V1.1, and Relationship Graph V1 remain frozen.
