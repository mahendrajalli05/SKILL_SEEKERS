# Advanced Image Forensics V1 report

Date: 2026-09-10  
Engine: `image-forensics-v1`  
HTTP:

- `POST /api/v1/images/{image_id}/forensics`
- `GET  /api/v1/images/{image_id}/forensics`

Frozen and unchanged in this slice: Cost Intelligence V1.1, Time Intelligence V1, Overlap Intelligence V1, Compliance V1, Evidence Object V1 schema/validation, Risk Fusion V1.1, Relationship Graph V1, Search / AP pilot / Scheme ID, Project Digital Passport, Investigation Workspace (except the new Image Forensics section and PCE forensic framing), Plan → Claim → Evidence V1 comparison logic, Document & Blueprint V1, Image Evidence & Authenticity V1, Geospatial Consistency V1, Need & Impact V1, Milestone Advisor V1, Jan-Sakshi V1.

This slice adds a **forensic-assistance layer** for submitted project images. It helps officers review possible manipulation, possible AI-generation, suspicious metadata, and transformations that are inconsistent with the stored source. It does **not** determine that an image is fake, fraudulent, definitely AI-generated, or definitely manipulated. It is **not** fused into Investigation Priority.

---

## Architecture

```
Input image (existing Image Evidence V1 photo row)
        ↓
File integrity checks (SHA-256 vs stored hash; original bytes not rewritten)
        ↓
Metadata analysis (reported EXIF + software / timestamp / camera combinations)
        ↓
Image transformation analysis (JPEG recompression residue, dimensions, repeated regions)
        ↓
Potential manipulation signals
        ↓
Potential AI-generation signals (plugin; default unavailable)
        ↓
Forensic explanation
        ↓
Evidence Object V1 (engine=forensics)
```

Image Evidence V1 remains the image store: SHA-256, aHash/dHash/pHash, reported EXIF, quality, linking, and existing Image Evidence Objects. Advanced authenticity on Image Evidence V1 stays `NOT_IMPLEMENTED` / `INCONCLUSIVE`. This engine is a separate layer.

Risk Fusion V1.1 is not modified. The image slot remains `NOT_YET_INTEGRATED`. A future Risk Fusion V2 may consume these objects.

Project images are processed locally. They are **not** transmitted to external services by default (`SARVSAKSHI_FORENSICS_AI_EXTERNAL_ENABLED` defaults false; V1 still does not send bytes even if requested). Filesystem paths are not returned.

---

## Techniques used

Independent signals only. No single “fake image probability”.

| Signal | Source | Possible results |
| --- | --- | --- |
| `integrity` | SHA-256 vs stored Image Evidence hash; decode check | `INTEGRITY_OK` / `UNREADABLE` / `HASH_MISMATCH` / `MISSING_FILE` |
| `metadata_signal` | Image Evidence EXIF plus Software / DateTimeOriginal / DateTimeDigitized / camera make-model | `METADATA_ANOMALY` / `NO_STRONG_FORENSIC_SIGNAL` / `INCONCLUSIVE` |
| `reuse_signal` | Image Evidence V1 SHA-256 and perceptual hashes | `EXACT_DUPLICATE` / `POTENTIAL_IMAGE_REUSE` / `UNIQUE` / `INCONCLUSIVE` |
| `quality_signal` | Image Evidence V1 technical quality | `QUALITY_WARNING` / `NO_STRONG_FORENSIC_SIGNAL` / `INCONCLUSIVE` |
| `manipulation_signal` | Repeated 16px blocks; EXIF-vs-pixel size plus editor/camera combination | `POTENTIAL_MANIPULATION` / `NO_STRONG_FORENSIC_SIGNAL` / `INCONCLUSIVE` |
| `ai_generation_signal` | `AiGenerationDetector` plugin | `AI_GENERATION_ANALYSIS_UNAVAILABLE` / `INCONCLUSIVE` / `POTENTIAL_AI_GENERATION` only if a future testable detector returns a score |

JPEG recompression residue is recorded as **context**. Uneven residue or low estimated JPEG quality alone is **INCONCLUSIVE**, not `POTENTIAL_MANIPULATION`.

Missing EXIF is **not** `METADATA_ANOMALY` and is **not** treated as manipulation.

Allowed findings:

- `POTENTIAL_MANIPULATION`
- `POTENTIAL_AI_GENERATION`
- `METADATA_ANOMALY`
- `INCONCLUSIVE`
- `NO_STRONG_FORENSIC_SIGNAL`
- `AI_GENERATION_ANALYSIS_UNAVAILABLE`

---

## Techniques unavailable

| Technique | V1 state |
| --- | --- |
| Validated AI-generated-image detector | No suitable local open-source model is bundled. Arbitrary pixel heuristics are not used. Result: `AI_GENERATION_ANALYSIS_UNAVAILABLE`. Abstraction: `set_ai_detector()`. |
| External forensic APIs | Not used. Images are not transmitted. |
| Error-level analysis as a validated manipulation test | Prototype JPEG recompression residue only. Not treated as a validated authenticity test. |
| Satellite / geospatial CV | Not in this slice (Geospatial Consistency V1 is separate and frozen). |
| Benchmark accuracy on a public manipulation dataset | No independent validated dataset is used. No accuracy percentage is claimed. |

---

## Confidence rules

Evidence Confidence is **separate** from the signal result.

Display labels: `HIGH` / `MEDIUM` / `LOW` / `INCONCLUSIVE`.

Numeric confidence is capped: REAL 0.55 / HYBRID 0.40 / SYNTHETIC 0.35.

| Situation | Confidence label |
| --- | --- |
| Repeated-region copy-move indicator | MEDIUM (capped) |
| Metadata anomaly (inconsistent timestamps and/or editor+camera) | LOW–MEDIUM |
| Missing EXIF | INCONCLUSIVE |
| AI detector unavailable | INCONCLUSIVE |
| File unreadable | INCONCLUSIVE |

A forensic signal can have HIGH / MEDIUM / LOW confidence where justified. Otherwise: INCONCLUSIVE.

---

## Combined assessment formula

Labelled:

> Prototype forensic assessment — not a validated authenticity decision.

Exact formula:

```
overall = REVIEW_REQUIRED
  if manipulation_signal is POTENTIAL_MANIPULATION
  or reuse_signal is EXACT_DUPLICATE or POTENTIAL_IMAGE_REUSE
  or metadata_signal is METADATA_ANOMALY
else INCONCLUSIVE
  if every independent signal among manipulation/metadata/reuse is INCONCLUSIVE or UNAVAILABLE
else NO_STRONG_FORENSIC_SIGNAL
```

No combined authenticity probability is produced. AI-generation unavailable does **not** by itself force `REVIEW_REQUIRED`.

---

## Evidence Object V1

Engine `forensics`. Types:

- `IMAGE_FORENSIC_MANIPULATION`
- `IMAGE_FORENSIC_AI_GENERATION`
- `IMAGE_FORENSIC_METADATA`
- `IMAGE_FORENSIC_INCONCLUSIVE` (when overall is INCONCLUSIVE)

Each object includes project_id, image_id, finding, confidence, source, provenance, data_mode, engine version `image-forensics-v1`, and explanation.

---

## Plan → Claim → Evidence

Plan–Claim–Evidence V1 comparison is not rewritten. Forensics adds framing only.

Example:

- CLAIM: “Photo shows completed work.”
- FORENSIC: Potential image reuse detected.
- Result: Review required.

The claim is **not** marked false.

---

## REAL / HYBRID / SYNTHETIC

| Mode | Meaning |
| --- | --- |
| REAL | Real uploaded image/evidence on a real work. Not an official government photograph merely because it was uploaded. |
| HYBRID | Real project plus labelled SYNTHETIC prototype image context. |
| SYNTHETIC | Test-only `project.is_synthetic` rows. Provenance must state SYNTHETIC. |

Synthetic fixtures are marked TEST. They are not presented as real field evidence. Fake government photographs are not generated.

---

## Frontend

Investigation Workspace → **Image Forensics**:

- Image
- Integrity
- Metadata
- Reuse
- Manipulation signal
- AI-generation signal
- Confidence
- Overall forensic assessment
- Limitations

Example wording:

- Manipulation: Potential signal
- AI generation: Inconclusive
- Metadata: Timestamp available
- Reuse: No match
- Overall: REVIEW REQUIRED

Plan → Claim → Evidence Evidence/Result tabs show the same forensic framing. Claims are not marked false.

---

## Examples (controlled TEST fixtures)

Small fixtures only. Not a large dataset. Not real manipulated government images.

| Fixture | Expected assistance result |
| --- | --- |
| Original camera-tagged JPEG | Integrity OK; timestamp available; AI unavailable; no strong manipulation signal |
| Recompressed JPEG | Low-quality JPEG context; manipulation not claimed with certainty |
| Resized JPEG | Dimensions recorded; no definite manipulation claim |
| Exact duplicate | `reuse_signal=EXACT_DUPLICATE`; overall REVIEW REQUIRED |
| Near duplicate | Image Evidence perceptual reuse reused when it fires |
| Metadata-stripped JPEG | EXIF unavailable; missing EXIF is not manipulation |
| Metadata-inconsistent JPEG (editor tag + timestamp mismatch) | `METADATA_ANOMALY`; overall REVIEW REQUIRED |
| Copy-move PNG (duplicated 16px block) | `POTENTIAL_MANIPULATION` (review signal) |
| Synthetic AI-like TEST JPEG | AI analysis unavailable; not called definitely AI-generated |

---

## Validation methodology

- Unit tests for metadata, integrity, transformation, AI plugin, and overall wording.
- API tests for POST/GET, original-byte SHA-256 unchanged, Evidence Objects, PCE framing, REAL/HYBRID/SYNTHETIC, Risk Fusion V1.1 unchanged.
- Frontend component test for the Image Forensics panel.
- No independent public manipulation/AI benchmark was scored. **No accuracy figure is claimed.**

```powershell
cd backend
python -m pytest
# 565 passed (17 Image Forensics V1 tests)

cd frontend
npm test
# 51 passed

npm run build
# Next.js compiled successfully
```

Frozen engine versions asserted: `cost-peer-v1.1`, `time-peer-v1`, `overlap-multi-v1`, `compliance-rules-v1`, `risk-fusion-v1.1`, `relationship-graph-v1`, `plan-claim-evidence-v1`, `document-blueprint-v1`, `image-evidence-v1`, `geospatial-consistency-v1`, `need-impact-v1`, `milestone-advisor-v1`, `jan-sakshi-v1`. Forensics engine: `image-forensics-v1`.

Interactive browser click-through was not available in this environment. Integrity, metadata, manipulation, AI-unavailable handling, Evidence Objects, PCE claim-not-false framing, REAL/HYBRID/SYNTHETIC labelling, and unchanged Risk Fusion were verified through backend TestClient tests and frontend component tests.

---

## Limitations

- No validated AI-generated-image detector is bundled.
- Repeated-region and recompression checks are prototype indicators.
- Missing EXIF is common (especially PNG) and is not proof of manipulation.
- EXIF can be missing, edited, or incorrect.
- An image does not prove physical completion.
- Image Forensics is stored, not fused into Investigation Priority.

---

## Files

Engine: `backend/app/engines/forensics/`  
Evidence adapter: `backend/app/evidence/adapters/forensics.py`  
HTTP: `backend/app/api/routes/forensics.py`  
Schema: `backend/app/domain/schemas/forensics.py`  
Storage: additive `forensics_json` / `forensics_status` on existing `photo`  
UI: Investigation Workspace **Image Forensics** plus PCE forensic framing

STOP. Satellite, Copilot, graph visualization, Risk Fusion V2, payment, and PFMS were not built in this slice.
