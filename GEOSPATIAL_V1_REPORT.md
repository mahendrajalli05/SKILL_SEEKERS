# Geospatial Consistency V1 report

Date: 2026-09-10  
Engine: `geospatial-consistency-v1`  
HTTP:

- `GET  /api/v1/projects/{id}/geospatial`
- `POST /api/v1/projects/{id}/geospatial/check`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, Project Digital Passport, Plan–Claim–Evidence V1 comparison logic, Document & Blueprint Intelligence V1, Image Evidence & Authenticity V1.

This slice adds a **location consistency check** between reported image GPS and a project location **when project coordinates are actually available**. It does **not** prove authenticity, physical completion, or that a photograph depicts the claimed work. It does **not** download or process satellite imagery.

---

## Architecture

```
Project location (REAL: unavailable; HYBRID: SYNTHETIC enrichment GPS)
        ↓
Reported image GPS from Image Evidence V1 (EXIF; not inferred from pixels)
        ↓
Haversine distance vs configurable prototype threshold (default 500 m)
        ↓
LOCATION_CONSISTENT / LOCATION_MISMATCH / INCONCLUSIVE
        ↓
Evidence Object V1 (engine=geo)
  GEOSPATIAL_LOCATION_CONSISTENCY
  GEOSPATIAL_LOCATION_MISMATCH
  GEOSPATIAL_INCONCLUSIVE
        ↓
Plan → Claim → Evidence framing (claim vs image GPS distance)
        ↓
Investigation Workspace → Geospatial Evidence panel
```

Existing `photo` rows and Evidence Object tables are reused. Project GPS is **not** written onto the real `project` record. Fusion still treats geospatial as `NOT_YET_INTEGRATED`. No map library was added.

---

## Available data

| Mode | Project coordinates | Meaning |
| --- | --- | --- |
| **REAL** | Unavailable | Current work-level extract has no verified latitude/longitude. Result is **INCONCLUSIVE / LOCATION UNAVAILABLE**. Coordinates are not invented. |
| **HYBRID** | SYNTHETIC enrichment GPS when present | Controlled prototype testing only. Labelled **SYNTHETIC**. Not official MPLADS GPS. |
| **SYNTHETIC** | Test `project.is_synthetic` rows | Provenance must state SYNTHETIC. |

Image GPS is always:

> Reported GPS metadata from uploaded file

If image GPS is absent: **GPS_METADATA_UNAVAILABLE**. Location is not inferred from image content. Missing GPS is **not** converted into a mismatch.

---

## Distance and threshold

Deterministic haversine great-circle distance (`EARTH_RADIUS_M = 6,371,000`). Returns `distance_meters` and `distance_km`.

Default prototype threshold: **500 metres** (`SARVSAKSHI_GEOSPATIAL_THRESHOLD_METERS`, overridable on `POST .../geospatial/check`).

This is a prototype/business-rule setting. It is **not** a claim that MPLADS officially uses a 500 m verification radius.

| Inputs | Result |
| --- | --- |
| Project GPS + image GPS + distance ≤ 500 m | `LOCATION_CONSISTENT` |
| Project GPS + image GPS + distance > 500 m | `LOCATION_MISMATCH` |
| Project GPS missing **or** image GPS missing | `INCONCLUSIVE` |

Boundary: 500.0 m is consistent; any greater distance is a mismatch.

---

## Multiple images

Per project the engine returns:

- image count
- GPS available / unavailable counts
- distances
- consistent / mismatch / inconclusive counts
- `mixed_results`

Overall:

- any mismatch → `LOCATION_MISMATCH`
- all assessable images consistent and none missing GPS → `LOCATION_CONSISTENT`
- one matching image plus missing GPS on others → **INCONCLUSIVE**

One matching image does **not** make every other image trustworthy.

---

## Evidence Object V1

Engine `geo`. Types:

- `GEOSPATIAL_LOCATION_CONSISTENCY`
- `GEOSPATIAL_LOCATION_MISMATCH`
- `GEOSPATIAL_INCONCLUSIVE`

Each object includes evidence_id, project_id, image_id where applicable, finding, optional score, confidence, distance, threshold, source, data_mode, provenance, and explanation.

Example:

> Uploaded image GPS is 148 meters from the supplied project location, within the configured 500 meter prototype threshold.

Location Consistency is **separate** from Evidence Confidence. Matching GPS does not raise overall project confidence. Local confidence reflects GPS availability, reported-metadata quality, project-location source, and provenance, with mode caps REAL 0.50 / HYBRID 0.40 / SYNTHETIC 0.35.

---

## Plan → Claim → Evidence

PCE quantity/cost comparison is unchanged. Geospatial adds a framed finding:

- CLAIM: “Progress photograph was taken at the project site.”
- EVIDENCE: image GPS = N meters from project location
- Result: `LOCATION_CONSISTENT` / `LOCATION_MISMATCH` / `INCONCLUSIVE`

This does **not** prove the photograph depicts the claimed work.

---

## Satellite preparation

`SatelliteProvider` is an interface for a later imagery backend.

V1 implementation: `UnavailableSatelliteProvider`.

Returns:

**SATELLITE_VERIFICATION_NOT_AVAILABLE**

No imagery is downloaded, processed, or fabricated.

---

## Frontend

Investigation Workspace → **Geospatial Evidence**:

1. Project location: Available / Unavailable
2. Image GPS: Available / Unavailable
3. Distance in metres
4. 500 m prototype threshold
5. Result: LOCATION CONSISTENT / LOCATION MISMATCH / INCONCLUSIVE
6. HYBRID / SYNTHETIC labels when applicable
7. Plan → Claim → Evidence location framing
8. Satellite = not available
9. Limitations

A map was not added. Numeric/location consistency is the V1 surface.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 481 passed (25 Geospatial Consistency V1 tests)

cd frontend
npm test
# 43 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions remain: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `plan-claim-evidence-v1`, `document-blueprint-v1`, `image-evidence-v1`. Geospatial engine: `geospatial-consistency-v1`.

Controlled tests only (existing synthetic enrichment; no additional bulk data): same coordinates, within 500 m, just outside 500 m, far away, missing project GPS, missing image GPS, mixed images, DEMO_GHOST-style offshore SYNTHETIC coordinates, REAL/HYBRID/SYNTHETIC separation, Evidence Objects, provenance, 500 m configuration, deterministic IDs, no-fraud wording, satellite unavailable.

---

## Limitations

- No satellite imagery comparison or computer vision.
- No citizen / Jan-Sakshi geofencing.
- REAL project GPS is unavailable in the current public extract.
- SYNTHETIC hybrid coordinates are not official MPLADS GPS.
- Image GPS is reported EXIF and may be missing or edited.
- GPS consistency does not prove completion or authenticity.
- Geospatial evidence is stored, not fused into Investigation Priority.

STOP. Copilot, Jan-Sakshi, Milestone Advisor, Need & Impact, and satellite comparison were not built in this slice.
