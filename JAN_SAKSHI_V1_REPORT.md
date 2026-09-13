# Jan-Sakshi / Citizen Evidence V1 report

Date: 2026-09-10  
Engine: `jan-sakshi-v1`  
HTTP:

- `POST /api/v1/projects/{id}/citizen-reports`
- `GET  /api/v1/projects/{id}/citizen-reports`
- `GET  /api/v1/citizen-reports/{id}`
- `POST /api/v1/citizen-reports/{id}/verify`
- `GET  /api/v1/projects/{id}/citizen-summary`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, AP pilot/data mode, Scheme ID, Project Digital Passport structure, Investigation Workspace (except the new JAN-SAKSHI section), Plan → Claim → Evidence V1 comparison logic, Document & Blueprint Intelligence V1, Image Evidence & Authenticity V1, Geospatial Consistency V1, Need & Impact V1, Milestone Advisor V1.

This slice adds **citizen-generated field evidence**. People near a work can submit structured satisfaction, an observation, and an optional photo. Submissions become supporting Evidence Objects. They do **not** prove poor quality, project failure, or a legal finding of wrongdoing. They are **not** fused into Investigation Priority.

---

## Architecture

```
Citizen identifies a project
        ↓
Optional photo (Image Evidence V1 upload; no second image store)
+ capture GPS + capture timestamp
+ satisfaction 1–5 + observation + optional issue category
        ↓
Validation (project exists, safe upload, GPS/timestamp where required)
        ↓
Location check vs known project GPS
  haversine reused from Geospatial Consistency V1
  500 m prototype radius (not an official MPLADS rule)
        ↓
ACCEPTED / REJECTED / INCONCLUSIVE
        ↓
Presentation watermark copy (original bytes unchanged)
+ grounded text analysis (not a chatbot)
+ duplicate-image flag via Image Evidence hashes
        ↓
Evidence Object V1:
  CITIZEN_LOCATION / CITIZEN_FEEDBACK / CITIZEN_IMAGE / CITIZEN_AGGREGATE
        ↓
PCE framing in the citizen engine only
  claim is never marked false
        ↓
Officer summary + Passport Citizen Evidence section
Investigation Priority unchanged.
```

Citizen Evidence is its **own evidence source**. Risk Fusion V1.1 still treats `citizen_evidence` as `NOT_YET_INTEGRATED`. Fusion scoring, weights, and Investigation Priority display are not modified.

There is **no** payment, PFMS, Copilot, satellite, advanced image-forensics, graph visualization, automatic-sanction, or automatic-fraud endpoint.

---

## Citizen report schema

Additive columns on the existing `citizen_report` table. No passwords and no unnecessary personally identifying information.

| Field | Meaning |
| --- | --- |
| `id` (`citizen_report_id`) | SQLite surrogate |
| `project_id` | FK to `project` |
| `satisfaction_rating` | 1–5 |
| `observation_text` | Free-text observation / complaint |
| `issue_category` | Optional: work quality, incomplete work, delayed work, location concern, safety, other |
| `submitted_at` | Server receipt time |
| `latitude` / `longitude` | Verification GPS. Not returned by default |
| `image_id` | FK to existing `photo` (Image Evidence V1) |
| `submission_status` | `ACCEPTED` / `REJECTED` / `INCONCLUSIVE` |
| `verification_result` | `LOCATION_VERIFIED` / `LOCATION_REJECTED` / `INCONCLUSIVE` (`LOCATION_UNAVAILABLE` as alias) |
| `capture_timestamp` | Citizen-supplied capture time when provided |
| `timestamp_status` | `TIMESTAMP_RECORDED` / `TIMESTAMP_UNAVAILABLE` |
| `data_mode` | `REAL` / `HYBRID` / `SYNTHETIC` |
| `provenance_json` | Required source trail |
| `analysis_json` | Grounded sentiment / issue / severity |
| `duplicate_flag` | `POTENTIAL_DUPLICATE_CITIZEN_EVIDENCE` when the same image hash is reused |
| `watermark_path` | Presentation copy only |
| `evidence_ids_json` | Canonical Evidence Object IDs |
| `synthetic` | True when the report is labelled TEST/SYNTHETIC |

Legacy rating / notes columns from the earlier skeleton remain unused by V1 write paths.

Configurable prototype settings (`backend/app/config.py`):

| Setting | Default |
| --- | --- |
| `citizen_radius_meters` | 500 |
| `citizen_insufficient_sample_max` | 3 |
| `citizen_community_signal_min` | 10 |
| `citizen_min_reports_for_concern` | 3 |
| `citizen_rate_limit_count` | 20 per hour per project |

---

## 500-metre prototype geo rule

500 m is a SARVSAKSHI prototype verification rule. It is **not** an official MPLADS rule.

Distance uses `app.engines.geo.distance.haversine_m`. Project GPS uses `project_location_for`. Coordinates are never invented.

| Condition | Result |
| --- | --- |
| Project GPS + citizen GPS + distance ≤ 500 m | `LOCATION_VERIFIED` |
| Project GPS + citizen GPS + distance > 500 m | `LOCATION_REJECTED` |
| Missing project GPS or missing citizen GPS | `INCONCLUSIVE` / `LOCATION_UNAVAILABLE` |

Exact 500.0 m is verified. REAL public extract has no real project GPS; REAL mode does not force a location decision.

A verified-location submission still requires a capture timestamp for `ACCEPTED`. Missing timestamp → `INCONCLUSIVE` with a clear reason. Invalid submissions are not silently accepted.

---

## Photo, EXIF, watermark

Photos reuse Image Evidence V1 (`source=citizen_upload`). SHA-256, reported EXIF GPS/timestamp, MIME/size checks, and exact-duplicate detection are reused. EXIF is labelled **reported metadata from uploaded file**.

Watermark:

- Overlay includes SARVSAKSHI, Scheme ID, submission timestamp, and lat/lon when available.
- Written to `data/uploads/citizen_watermarks/`.
- Original uploaded bytes are unchanged.
- The watermark is a presentation aid, not proof of authenticity.

---

## Structured feedback analysis

Not a chatbot. Outputs are grounded in the submitted text:

- sentiment: positive / negative / mixed / neutral / `INCONCLUSIVE`
- issue category (word-boundary matching so `"complete"` does not match `"incomplete"`)
- complaint severity
- evidence confidence

Insufficient text (short of 12 characters or 3 words) returns `INCONCLUSIVE`. Sentiment is not treated as proof of project quality. Complaints are not fabricated.

---

## Duplicate / spam

Exact duplicate image → `POTENTIAL_DUPLICATE_CITIZEN_EVIDENCE` for review. Duplicate is not treated as proof of wrongdoing.

Simple rate limit: 20 submissions per project per hour.

V1 does not require citizen accounts.

---

## Multi-citizen aggregation

For a project:

- total submissions
- verified-location submissions
- rejected submissions
- average satisfaction and 1–5 distribution
- recurring issue categories / complaint themes
- citizen evidence confidence (capped by data mode; a single report cannot dominate)

Sample-size status (configurable):

| Count | Status |
| --- | --- |
| ≤ 3 | Insufficient citizen sample |
| 4–9 | Limited citizen sample |
| ≥ 10 | Community feedback signal available |

`POTENTIAL_COMMUNITY_CONCERN` requires at least 3 verified reports sharing a recurring issue category. This is a prototype threshold, not a universal official cutoff.

---

## Evidence Object V1

Adapter: `backend/app/evidence/adapters/citizen.py`.

Uses `add_evidence_object` so sibling citizen rows are not deleted. Does not change Evidence Object validation.

| Signal | Role |
| --- | --- |
| `CITIZEN_LOCATION` | Location verification result |
| `CITIZEN_FEEDBACK` | Satisfaction / observation / analysis |
| `CITIZEN_IMAGE` | Linked Image Evidence photo |
| `CITIZEN_AGGREGATE` | Project-level community signal |

Each object retains project_id, citizen_report_id, image_id where applicable, finding, confidence, source, provenance, data_mode, and timestamp.

---

## Plan → Claim → Evidence

Citizen framing lives in `app.engines.citizen.pce_frame`. Plan–Claim–Evidence V1 comparison is not rewritten.

Example: claim “Road work is complete” plus citizen “Road remains incomplete in section X.” → `CITIZEN_CONTRADICTION` / evidence of concern. The claim is **not** marked false.

---

## Risk Fusion

Not modified. Investigation Priority and Evidence Confidence stay as Risk Fusion V1.1. Citizen evidence is an independent source for a later fusion version.

---

## REAL / HYBRID / SYNTHETIC

| Mode | Behaviour |
| --- | --- |
| REAL | Actual user-provided citizen evidence. Missing project GPS stays unavailable. Synthetic reports are hidden. |
| HYBRID | Real work plus labelled SYNTHETIC prototype citizen evidence. Persistent notice shown. |
| SYNTHETIC | Test-only rows. Provenance and badge state TEST/SYNTHETIC. |

Synthetic citizen submissions are never presented as genuine public reports.

---

## Privacy

- No passwords or unnecessary identity data.
- Default GET responses omit raw latitude/longitude.
- Officer may pass `include_location=true` for verification.
- Public-facing aggregate results do not include citizen GPS.
- Frontend officer and passport views do not display raw coordinates.

---

## Frontend

Citizen view `/jan-sakshi`:

1. Identify / select a project
2. Capture or upload a photo
3. Obtain location (verification only; not published)
4. Submit satisfaction 1–5
5. Enter observation and optional issue category
6. Validate and submit
7. See ACCEPTED / REJECTED / INCONCLUSIVE with reasons

Officer view: Investigation Workspace → **JAN-SAKSHI** — verified/rejected counts, satisfaction distribution, recurring issues, citizen images, location verification status (without raw GPS), PCE framing, evidence confidence.

Project Digital Passport → **Citizen Evidence** summary: reports, verified, rejected, average satisfaction, top recurring issues, citizen evidence confidence. Investigation Priority is not changed.

Nav: Jan-Sakshi.

---

## Controlled cases

Small fixtures only. No new bulk synthetic dataset. All marked TEST/SYNTHETIC.

**CASE 1** — Citizen at 180 m, photo + GPS + timestamp, positive feedback. **ACCEPTED** / **LOCATION_VERIFIED**.

**CASE 2** — Citizen at 1.8 km. **REJECTED** / **LOCATION_REJECTED**.

**CASE 3** — GPS unavailable. **INCONCLUSIVE**.

**CASE 4** — Multiple citizens report incomplete work. **CITIZEN_AGGREGATE** = potential community concern; three reports still show **Insufficient citizen sample**.

**CASE 5** — Repeated identical image. **POTENTIAL_DUPLICATE_CITIZEN_EVIDENCE**.

Also covered: exact 500.0 m unit classification; REAL missing project GPS; missing timestamp; missing/invalid image; privacy omission of lat/lon; HYBRID labelling; PCE claim-not-false; Risk Fusion version `risk-fusion-v1.1` unchanged.

HTTP 500 m tests use a 499.5 m offset so JSON lat/lon rounding cannot push haversine slightly over the threshold. Exact 500.0 classification is asserted in `test_citizen_location.py`.

---

## Limitations

- 500 m is a prototype verification rule, not an official MPLADS rule.
- REAL public extract still has no verified project GPS.
- One citizen report does not establish truth.
- Sentiment is not proof of project quality.
- Watermark is not proof of authenticity.
- EXIF is reported metadata from the uploaded file.
- Citizen evidence is not fused into Investigation Priority in V1.
- No citizen accounts, Copilot, satellite, PFMS, or automatic sanction.

---

## Governance safeguards

- No FRAUD / FRAUD DETECTED / FRAUD PROBABILITY wording.
- No payment-release, PFMS, or automatic-sanction APIs.
- Claim is never marked false from citizen text.
- SYNTHETIC values stay labelled.
- Raw citizen GPS omitted from default responses.
- AI recommends. Authorized officers decide.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 548 passed (16 Jan-Sakshi / Citizen Evidence V1 tests)

cd frontend
npm test
# 50 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions asserted in tests: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `relationship-graph-v1`, `plan-claim-evidence-v1`, `document-blueprint-v1`, `image-evidence-v1`, `geospatial-consistency-v1`, `need-impact-v1`, `milestone-advisor-v1`. Citizen engine: `jan-sakshi-v1`.

Interactive browser click-through was not available in this environment. Location boundary, accepted/rejected/inconclusive submissions, duplicate image, aggregation, REAL/HYBRID labelling, Evidence Object generation, PCE framing, privacy omission of GPS, and unchanged Risk Fusion were verified through backend TestClient tests and frontend component tests.

---

## Files

Engine: `backend/app/engines/citizen/`  
Evidence adapter: `backend/app/evidence/adapters/citizen.py`  
HTTP: `backend/app/api/routes/citizen.py`  
Schema: `backend/app/domain/schemas/citizen.py`  
Storage: additive columns on `citizen_report`  
Citizen UI: `frontend/src/app/jan-sakshi/page.tsx`  
Officer UI: `frontend/src/components/JanSakshiPanel.tsx`  
Passport: `frontend/src/components/CitizenEvidenceSummary.tsx`

Supporting wiring only: `backend/app/config.py`, `backend/app/db.py`, `backend/app/domain/enums.py`, `backend/app/evidence/constants.py`, route/schema/model `__init__` files, frontend `api.ts` / `types.ts` / `AppShell.tsx`, passport and investigation pages.

STOP. Payment release, PFMS, satellite, advanced image forensics, Copilot, graph visualization, automatic fraud finding, automatic sanction, and Risk Fusion reweighting were not built in this slice.
