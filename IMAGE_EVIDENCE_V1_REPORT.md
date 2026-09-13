# Image Evidence & Authenticity V1 report

Date: 2026-09-10  
Engine: `image-evidence-v1`  
HTTP:

- `POST /api/v1/projects/{id}/images`
- `GET  /api/v1/projects/{id}/images`
- `GET  /api/v1/images/{image_id}`
- `POST /api/v1/images/{image_id}/analyze`
- `POST /api/v1/images/{image_id}/attach-evidence`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, Project Digital Passport, Plan–Claim–Evidence V1 comparison logic, Document & Blueprint Intelligence V1.

This slice adds a reliable **image-evidence layer** to the existing Plan → Claim → Evidence workflow. It stores officer photographs, detects exact duplicates and potential visual reuse, extracts reported EXIF metadata when present, and records technical quality checks. It does **not** determine fraud, does not compare satellite imagery, does not accept citizen uploads, and does not run advanced AI-generated-image detection.

---

## Architecture

```
Officer upload (JPEG / PNG / WebP)
        ↓
Safe storage + SHA-256 (existing photo table)
        ↓
On-upload analysis
  - exact duplicate (SHA-256) → EXACT_DUPLICATE
  - perceptual aHash/dHash/pHash → POTENTIAL_IMAGE_REUSE
  - reported EXIF (timestamp / GPS / camera)
  - technical quality
  - authenticity capability stub → NOT_IMPLEMENTED / INCONCLUSIVE
        ↓
Evidence Object V1 (engine=image)
  IMAGE_EXACT_DUPLICATE / IMAGE_POTENTIAL_REUSE
  IMAGE_METADATA
  IMAGE_QUALITY
        ↓
Officer attach → existing photo row is PCE evidence
        ↓
Existing Plan–Claim–Evidence comparison (unchanged)
```

Existing `photo` / `photo_details` tables are reused. Additive columns only. No second evidence store. Fusion still treats image as `NOT_YET_INTEGRATED`. Filesystem paths are not returned by the API.

---

## Schema (additive)

`photo` (existing table): `mime_type`, `file_size`, `content_sha256`, `ahash`, `dhash`, `duplicate_of_id`, `integrity_status`, `attached_to_evidence`, `analysis_json`, `analysis_status`, plus PCE V1 metadata already present (`filename`, `source`, `data_mode`, `provenance_json`, `exif_lat`, `exif_lon`, `exif_time`, `phash`).

`image_id` is the SQLite `photo.id`. It is not an official MPLADS image or work ID. Every image belongs to `project.id` / `internal_project_id`.

---

## Duplicate and reuse

| Result | Meaning |
| --- | --- |
| **EXACT_DUPLICATE** | Same SHA-256 as a previously stored image in the same data mode |
| **POTENTIAL_IMAGE_REUSE** | Perceptual hash Hamming distance ≤ 10 of 64 bits (dHash / pHash / aHash) |
| **UNIQUE** | No exact or near match |

High visual similarity is not proof of wrongdoing. Wording never includes a legal fraud conclusion.

Each match returns `image_id`, `matched_image_id`, hash name, distance, similarity, explanation, and confidence.

---

## Metadata

Where EXIF is present, V1 extracts:

- capture timestamp
- latitude / longitude
- camera make / model

Each field stores value, source, extraction method, and confidence. Source is always:

> reported metadata from uploaded file

EXIF is not treated as verified location. GPS is not compared to satellite imagery. Missing values return **METADATA_UNAVAILABLE** and, for GPS:

> GPS metadata unavailable.

The original image bytes are not modified. Values are never inferred from pixels.

---

## Quality

Technical checks only:

- file readability
- width / height / pixel count
- low-resolution warning
- Laplacian-variance blur/flat-colour warning

Poor image quality is not treated as wrongdoing.

---

## Advanced authenticity

V1 capability state is explicit:

- capability: `NOT_IMPLEMENTED`
- result: `INCONCLUSIVE`
- score: none

`app.engines.image.forensics` is the hook for a later model. No manipulation score is fabricated.

---

## Data modes

| Mode | Meaning |
| --- | --- |
| REAL | Officer-supplied photograph on a real work. Not an official government photograph merely because it was uploaded. |
| HYBRID | Real work plus labelled SYNTHETIC/TEST image context. |
| SYNTHETIC | Test-only `project.is_synthetic` rows. Provenance must state SYNTHETIC. |

Synthetic fixtures are marked `TEST DATA — SYNTHETIC image fixture. Not an official government photograph.` REAL listings hide HYBRID/SYNTHETIC uploads.

---

## Plan → Claim → Evidence

Images are stored on the existing `photo` table, so Plan–Claim–Evidence already lists them as supporting image evidence. Officer **Attach to Evidence** records Evidence Objects and sets `attached_to_evidence`.

Example: claim “Work completed” plus a submitted progress photograph. The system records that the image exists, whether metadata/GPS is available, and whether exact duplicate or potential reuse was detected. It does **not** claim the photograph proves physical completion.

---

## Frontend

Investigation Workspace → **Image Evidence**:

1. Upload JPEG/PNG/WebP
2. Thumbnail
3. Reported metadata
4. SHA-256 and perceptual hashes
5. Duplicate / reuse result
6. Attach to Evidence
7. Evidence confidence
8. REAL / HYBRID / SYNTHETIC
9. Limitations (supporting evidence only; EXIF untrusted; authenticity INCONCLUSIVE; no satellite comparison)

Project summary:

Images submitted, exact duplicates, potential reuse, GPS available/unavailable, metadata availability, quality warnings, evidence confidence, advanced authenticity = INCONCLUSIVE.

The rest of the workspace was not redesigned.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 456 passed (25 Image Evidence V1 tests)

cd frontend
npm test
# 41 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions remain: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `plan-claim-evidence-v1`, `document-blueprint-v1`. Image engine: `image-evidence-v1`.

Controlled TEST fixtures only (not a large image dataset): unique, exact duplicate, near duplicate, different image, no metadata, EXIF GPS, unreadable JPEG, HYBRID image.

---

## Limitations

- No satellite or geospatial comparison.
- No citizen / Jan-Sakshi uploads.
- No advanced AI-generated or manipulation detector; result is INCONCLUSIVE.
- EXIF GPS/timestamps are reported metadata and may be missing or edited.
- An image does not prove physical completion.
- Image evidence is stored, not fused into Investigation Priority.

STOP. Copilot, Jan-Sakshi, Milestone Advisor, Need & Impact, satellite CV, and graph visualization were not built in this slice.
