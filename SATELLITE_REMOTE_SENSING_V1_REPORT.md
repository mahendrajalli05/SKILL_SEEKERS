# Satellite / Remote-Sensing Consistency V1 report

Date: 2026-09-10  
Engine: `satellite-remote-sensing-v1`  
HTTP:

- `GET  /api/v1/projects/{id}/satellite`
- `POST /api/v1/projects/{id}/satellite/check`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search / AP pilot / Scheme ID, Project Digital Passport, Investigation Workspace (except the new Satellite / Remote Sensing section and PCE satellite framing), Plan → Claim → Evidence V1 comparison logic, Document & Blueprint V1, Image Evidence V1, Advanced Image Forensics V1, Geospatial Consistency V1, Need & Impact V1, Milestone Advisor V1, Jan-Sakshi V1.

This slice adds a **decision-support remote-sensing evidence layer**. It can compare a claimed site and date window with available imagery **when a provider actually returns imagery metadata**. It does **not** prove fraud, project completion, exact construction measurements, or authenticity. It is **not** fused into Investigation Priority.

---

## Architecture

```
Project coordinates (Geospatial Consistency V1 location object)
+ requested date window + area of interest
        ↓
SatelliteProvider (abstraction; not a hard-coded vendor)
        ↓
imagery availability / scene metadata / image reference
        ↓
Remote-sensing analysis V1
  A. site coverage
  B. temporal window vs plan/claim/milestone
  C. basic site-level change where resolution permits
        ↓
SATELLITE_CONSISTENT / SATELLITE_INCONSISTENT /
SATELLITE_INCONCLUSIVE / SATELLITE_UNAVAILABLE
        ↓
Evidence Object V1 (engine=satellite)
        ↓
Plan → Claim → Evidence framing (claim is never marked false)
        ↓
Investigation Workspace → Satellite / Remote Sensing
```

Geospatial Consistency V1 remains a GPS distance check and still reports `SATELLITE_VERIFICATION_NOT_AVAILABLE` on its own payload. This engine is a separate layer.

Risk Fusion V1.1 is not modified. Satellite signal types are not mapped into fusion slots. Future Risk Fusion V2 may consume these objects.

---

## Provider architecture

Callers resolve a provider through `resolve_provider()`. Application routes do not import a vendor client directly.

| Provider | When used | Behaviour |
| --- | --- | --- |
| `UnavailableSatelliteProvider` | Default. `SARVSAKSHI_SATELLITE_PROVIDER=unavailable`. Unconfigured live aliases (`sentinel-2`, `stac`, `planet`, …) | `SATELLITE_UNAVAILABLE`. No scenes. No fabricated imagery. |
| `MockSatelliteProvider` (`test-mock`) | HYBRID / SYNTHETIC only, when `provider=mock`, a `test_scenario` is supplied, or `SARVSAKSHI_SATELLITE_MOCK_ENABLED=true` | Labelled TEST/SYNTHETIC **metadata** responses. `official_imagery=false`. References start with `TEST/`. |
| Disabled mock | REAL mode, even if `provider=mock` is requested | Same as unavailable. Mocked imagery is never presented as official. |

Provider interface fields:

- imagery availability
- acquisition date
- source/provider name
- spatial resolution where available
- cloud/quality where available
- image reference

No provider credentials are accepted or returned by the API. No live satellite API is configured in V1.

---

## Data sources

| Mode | Location | Imagery |
| --- | --- | --- |
| **REAL** | Geospatial V1: current extract has no verified GPS → location unavailable | Default provider unavailable → **SATELLITE_UNAVAILABLE** |
| **HYBRID** | SYNTHETIC enrichment GPS when present, labelled | TEST mock metadata only when explicitly requested. Never shown as official imagery |
| **SYNTHETIC** | Test `project.is_synthetic` rows | Same TEST mock rules. Provenance must state SYNTHETIC |

Project GPS is **not** invented. Unrelated imagery is **not** substituted.

---

## Imagery requirements

A check first asks: is imagery available for the requested coordinates, date window, and a useful spatial resolution?

If not:

**SATELLITE_UNAVAILABLE**

The rest of the platform continues to work.

---

## Analyses performed

Only analyses that can be defended from available metadata/observations.

| Analysis | Question | Not inferred |
| --- | --- | --- |
| Site / location consistency | Does available imagery cover the claimed site? | That the claimed work exists |
| Temporal window | Do acquisition dates match planned / claimed / milestone dates? | Temporal proof of completion when dates do not match |
| Basic change | Is there a labelled site-level change observation on a before/after pair, and is resolution sufficient? | Exact dimensions, floor count, expenditure, or quantity |

Overall results:

| Result | Meaning |
| --- | --- |
| `SATELLITE_CONSISTENT` | Consistent with available imagery |
| `SATELLITE_INCONSISTENT` | Inconsistent with available imagery |
| `SATELLITE_INCONCLUSIVE` | Insufficient imagery evidence |
| `SATELLITE_UNAVAILABLE` | No reliable imagery for the request |

---

## Resolution limits

Prototype useful-GSD ceilings (not official remote-sensing standards):

| Work scale (title-token grouping) | Max useful GSD |
| --- | ---: |
| `SMALL_STRUCTURE` (toilet, borewell, waiting shed, gym, …) | 1.0 m |
| `UNKNOWN` | 2.0 m |
| `LARGE_AREA` (community hall, school, park, …) | 5.0 m |
| `LARGE_LINEAR` (road, drain, canal, …) | 10.0 m |

If available resolution is coarser than the ceiling:

> Imagery resolution is insufficient for reliable physical verification.

A binary physical-verification result is **not** forced.

---

## Date limits

Imagery dates are compared with recorded plan dates, claimed completion (including phrases such as “October 2025”), and milestone/claim dates when present.

Example:

- Claimed completion: 2025-10
- Available imagery: 2024-01

Result: **INCONCLUSIVE** for completion verification. The acquisition window does not match the claim. This is not proof of completion or non-completion.

---

## Examples

**Unavailable (REAL / no provider)**  
No live API. No project GPS in the public extract. Result: `SATELLITE_UNAVAILABLE`. No map.

**HYBRID TEST — matching location**  
Labelled mock scene covers the claimed coordinates at 0.5 m. Result: `SATELLITE_CONSISTENT` for site coverage. Not official imagery.

**HYBRID TEST — wrong location**  
Mock scene does not cover the claimed site. Result: `SATELLITE_INCONSISTENT`.

**HYBRID TEST — before/after change**  
CLAIM: “Site development completed by October 2025.”  
Later labelled observation records site-level change. Result: `SATELLITE_CONSISTENT`. Claim is **not** marked false automatically.

**HYBRID TEST — no visible change**  
Before/after pair with sufficient resolution and no labelled site-level change. Result: `SATELLITE_INCONSISTENT` with available imagery. Not a legal finding.

**HYBRID TEST — insufficient resolution**  
Toilet block + 30 m scene. Result: `SATELLITE_INCONCLUSIVE`.

**HYBRID TEST — wrong date**  
Claimed completion October 2025; imagery 2024-01. Result: `SATELLITE_INCONCLUSIVE`.

---

## Image GPS

Where an uploaded project image has reported EXIF GPS, the engine records **separate** signals:

- project location
- image GPS
- satellite coverage of the project
- satellite coverage of the image GPS when a scene centre exists

These are not combined into a single unsupported conclusion.

---

## Evidence Object V1

Engine `satellite`. Types:

- `SATELLITE_AVAILABILITY`
- `SATELLITE_LOCATION`
- `SATELLITE_CHANGE`
- `SATELLITE_TEMPORAL`
- `SATELLITE_INCONCLUSIVE`

Each object includes evidence_id, project_id, source/provider, imagery reference, acquisition date, spatial resolution where available, finding, confidence, explanation, data_mode, and provenance.

TEST/SYNTHETIC mock metadata is labelled in provenance and must not be cited as official imagery.

---

## Plan → Claim → Evidence

PCE quantity/cost comparison is unchanged. Satellite adds framed findings only:

- CLAIM: recorded completion/progress statement, or a default site claim
- SATELLITE: availability, acquisition, resolution, coverage, change
- Result: `SATELLITE_*`
- `claim_marked_false=false`

A claim is never automatically marked false.

---

## Frontend

Investigation Workspace → **Satellite / Remote Sensing**:

- Provider
- Imagery available / unavailable
- Acquisition date
- Spatial resolution
- Coverage
- Change result
- Assessment
- Confidence
- Limitations
- TEST/SYNTHETIC label when mock metadata is used

No satellite map is rendered when official imagery is unavailable. REAL mode has no TEST provider control.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 589 passed (24 Satellite / Remote-Sensing V1 tests)

cd frontend
npm test
# 55 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions remain: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `relationship-graph-v1`, `plan-claim-evidence-v1`, `document-blueprint-v1`, `image-evidence-v1`, `geospatial-consistency-v1`, `need-impact-v1`, `milestone-advisor-v1`, `jan-sakshi-v1`, `image-forensics-v1`. Satellite engine: `satellite-remote-sensing-v1`.

Controlled tests (mocked provider responses only; no fabricated official imagery): imagery unavailable/available, matching/wrong location, before/after change, no visible change, insufficient resolution, wrong imagery date, REAL no-provider, HYBRID TEST mode, missing project GPS, Evidence Objects, PCE claim-not-false, Risk Fusion unchanged, provenance, no-fraud wording, deterministic IDs.

---

## Limitations

- No live government or commercial satellite API is configured in V1.
- Unavailable imagery stays `SATELLITE_UNAVAILABLE`. Imagery is never fabricated.
- TEST/SYNTHETIC mock responses are metadata only and are not official imagery.
- V1 does not run pixel-level computer vision on real scenes.
- Spatial resolution may be insufficient for small structures.
- Imagery dates that do not match the claim window cannot verify completion.
- Visible site-level change is not quantity, floor-count, or expenditure proof.
- REAL project GPS remains unavailable in the current public extract.
- Satellite evidence is stored, not fused into Investigation Priority.

---

## Future expansion

- Plug in a real STAC / Sentinel / licensed high-resolution provider behind the same interface when credentials and licensing exist.
- Defensible change detection on actual pixels at a stated resolution.
- Cloud-masked composites and documented accuracy limits.
- Risk Fusion V2 consumption of satellite Evidence Objects.

STOP. Copilot, Graph visualization, PFMS, payment release, Risk Fusion V2, and automatic fraud decisions were not built in this slice.
