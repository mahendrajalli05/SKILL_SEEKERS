# Document & Blueprint Intelligence V1 report

Date: 2026-09-10  
Engine: `document-blueprint-v1`  
HTTP:

- `POST /api/v1/projects/{id}/documents`
- `GET  /api/v1/projects/{id}/documents`
- `GET  /api/v1/documents/{document_id}`
- `POST /api/v1/documents/{document_id}/extract`
- `POST /api/v1/documents/{document_id}/attach-plan`
- `POST /api/v1/documents/{document_id}/attach-evidence`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search, Project Digital Passport. Plan–Claim–Evidence V1 comparison logic is reused, not rewritten. Investigation Workspace gained a Documents / Blueprint panel only.

This slice makes uploaded PDFs and images usable in the existing Plan → Claim → Evidence workflow. It extracts labelled fields when machine-readable text exists. It does **not** verify authenticity, does not run OCR or an LLM, does not invent values, and does not determine fraud.

---

## Architecture

```
Officer upload (PDF / PNG / JPEG)
        ↓
Safe storage + SHA-256 (existing document table)
        ↓
On-demand extract (pypdf text + labelled regex)
        ↓
Normalized blueprint/BOQ structure (optional fields)
        ↓
Officer attach → PLAN overlay (no silent overwrite)
             → EVIDENCE (observed quantity/expenditure)
        ↓
Existing Plan–Claim–Evidence comparison
        ↓
Evidence Object V1 (engine=document, signal=document)
```

Existing `document` and `plan_artifact` tables are reused. No second document table and no second evidence system. Extraction is **not** run on upload. OCR and LLM are structured as later backends; V1 returns `OCR_NOT_AVAILABLE` / `INCONCLUSIVE` for scanned PDFs and images.

Cost, Time, Overlap, Compliance, Fusion, and Graph scoring files were not modified. Fusion still treats document as `NOT_YET_INTEGRATED`.

---

## Schema (additive)

`document` (existing table): `mime_type`, `file_size`, `extraction_status`, `integrity_status`, `duplicate_of_id`, plus the PCE V1 metadata already present (`filename`, `document_type`, `content_sha256`, `data_mode`, `provenance_json`, timestamps).

`plan_artifact` (existing table): stores extraction JSON, method, text hash, and attach flags. Not a duplicate document store.

Document class is officer-selected:

- `BLUEPRINT`
- `BOQ_ESTIMATE`
- `PROJECT_DOCUMENT`
- `PROGRESS_REPORT`
- `COMPLETION_DOCUMENT`
- `OTHER`

Filename is not used to override an explicit type.

---

## Extraction

For PDFs with machine-readable text, labelled fields only:

- work/project name
- estimate / total / item amount
- area, length, width, height, floors, volume
- quantities (item / quantity / unit)
- milestones (name / amount / target date)
- planned start / planned completion
- agency / contractor text
- document/reference numbers

Missing values return **unavailable**. Conflicting values in one document are not auto-chosen. Length × width is not computed as area. Volume is not inferred. Unit rates are not invented.

Every extracted field has `value`, `confidence`, `extraction_method`, and `source_location` (page) when present. Confidence below 0.50 is not treated as authoritative for plan/evidence attach.

Scanned PDFs and PNG/JPEG:

> Dimensions could not be reliably extracted from this scanned document.

or

> OCR is not available in Document & Blueprint V1.

Budget-not-found example:

> Budget amount was not found in the uploaded document.

---

## Plan integration

Officer **Attach to Plan** fills empty overlay fields only.

Trusted extract allocation and an already-recorded overlay are not overwritten. When sources differ beyond the 10% relative threshold, the result is **PLAN DATA CONFLICT**. No source is chosen as truth.

---

## Plan vs Claim vs Evidence

Attach to Evidence writes `observed_quantity` / `observed_expenditure` on the existing `document` row. The frozen PCE comparison then uses those values.

Controlled TEST fixtures (not official documents):

**CASE 1 — CONSISTENT** — Plan 2,000 sq.ft; claim 2,000 sq.ft; extracted blueprint 2,000 sq.ft.

**CASE 2 — MISMATCH** — Plan/claim 2,000 sq.ft; extracted document 800 sq.ft.

**CASE 3 — INCONCLUSIVE** — TEST progress note with no labelled dimensions.

Wording never includes a legal fraud conclusion.

---

## Integrity and security

SHA-256 detects exact **DUPLICATE FILE**. Matching extracted text with a different file hash is **SIMILAR DOCUMENT**. Similar content is not treated as fraud.

Uploads: PDF/PNG/JPEG only (magic-byte sniff), 10 MiB maximum, sanitized filenames, storage under `data/uploads/documents/`, no executable types, files are not executed.

---

## REAL vs HYBRID

REAL uploads are officer-supplied evidence. Authenticity is not verified. HYBRID/SYNTHETIC uploads remain labelled. Synthetic fixtures are marked `TEST DATA — not an official government document`. Fake official government documents are not generated.

---

## Frontend

Investigation Workspace → **Documents / Blueprint**:

1. Upload
2. Select document type
3. Upload status
4. Extracted fields
5. Extraction confidence
6. Page/source references
7. Attach to Plan / Evidence
8. PLAN DATA CONFLICT
9. REAL or SYNTHETIC

The rest of the workspace was not redesigned.

---

## Tests and build

```powershell
cd backend
python -m pytest
# 431 passed (19 Document/Blueprint V1 tests)

cd frontend
npm test
# 40 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions asserted in tests: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `plan-claim-evidence-v1`. Document engine: `document-blueprint-v1`.

Interactive browser click-through was not available in this environment. Upload, extraction, attach, PCE comparison, and REAL/HYBRID labelling were verified through the backend TestClient and frontend component tests.

---

## Limitations

- No OCR, no LLM, no image-authenticity scoring.
- No satellite or geospatial verification.
- Authenticity of uploaded files is not assessed.
- Duplicate/similar reports are integrity notices, not legal findings.
- Document evidence is stored, not fused into Investigation Priority.

STOP. Copilot, Jan-Sakshi, Milestone Advisor, Need & Impact, image authenticity, and graph visualization were not built in this slice.
