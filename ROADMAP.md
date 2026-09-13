# SARVSAKSHI Development Roadmap

## Phase 1 — Project Setup
- [x] Repository setup
- [x] Backend skeleton
- [x] Frontend skeleton
- [x] Database skeleton
- [x] Environment configuration

## Phase 2 — Data Foundation
- [ ] Identify Coastal Andhra coverage (not decided; no coastal-region field; work-level file has no District column)
- [x] Collect real MPLADS data (2026-09-09: GitHub work-level snapshot + OpenCity 15th–17th LS MP summaries. Dedicated Completed Works and Expenditure/Vendor bulk files were identified on Dataful as MoSPI-sourced catalogs but were not downloadable without login; no fabricated files were added.)
- [x] Preserve provenance (sidecars with source URL, publisher, SHA256, download date)
- [x] Profile datasets (2026-09-09: still 4 raw extracts; Recommended Works = 60,359 rows, 3,944 AP. Completed Works / vendor files not present in data/raw.)
- [x] Clean data (2026-09-09: primary GitHub work-level extract only; internal surrogate IDs; OpenCity not merged; no invented district/vendor/expenditure)
- [x] Create data dictionary (observed fields only, from profiled extracts)
- [x] Create master schema
- [x] Load SQLite database
- [x] Synthetic enrichment layer (2026-09-10: 10,000 HYBRID records in `data/synthetic/` only; linked by `internal_project_id`; real 56,138-row extract unchanged; seed 26102)

## Phase 3 — Intelligence
- [x] Cost Intelligence V1 (2026-09-10: peer-based allocation anomaly on 56,138 real works; constituency-first with Andhra Pradesh fallback; interpretable median/MAD; HYBRID labels held-out only; no Isolation Forest; no material-price adjustment; no risk fusion)
- [x] Cost Intelligence V1.1 (2026-09-10: geographic constituency validation; deterministic work-title similarity; peer quality; log-robust Allocation Cost Anomaly score; HYBRID labels held-out; see COST_V1_1_REPORT.md)
- [x] Time Intelligence V1 (2026-09-10: dual REAL / HYBRID-TEST modes; REAL uses recommendation date + status only and does not fabricate duration; HYBRID-TEST uses synthetic dates/progress for controlled testing only; constituency-first peers; Time Anomaly + Evidence Confidence; see TIME_V1_REPORT.md)
- [x] Overlap Intelligence V1 (2026-09-10: blocked multi-signal similarity on 56,138 real works; semantic + category + constituency + amount + date + sparse place text; HYBRID GPS held-out only; Potential Overlap / Potential Duplicate + Evidence Confidence; see OVERLAP_V1_REPORT.md)
- [x] Compliance Engine V1 (2026-09-10: deterministic sourced MPLADS Guidelines 2023 rule catalog in `rules/`; REAL missing sanction/expenditure/district/GPS/unit → NOT_ASSESSABLE; HYBRID-TEST for 45-day / one-year / spend-vs-sanction only; not an ML model; see COMPLIANCE_V1_REPORT.md)
- [x] Evidence Object model (2026-09-10: canonical Evidence Object V1; Cost/Time/Overlap/Compliance persist to shared schema; GET /api/v1/projects/{id}/evidence; no Risk Fusion)
- [x] Risk Fusion (2026-09-10: Risk Fusion V1; prototype weights Cost 25 / Schedule 15 / Overlap 15 / Compliance 15 / reserved 30% unavailable; Investigation Priority + Evidence Confidence; no fraud probability; see RISK_FUSION_V1_REPORT.md)
- [x] Risk Fusion V2 (2026-09-10: consumes frozen V1/V1.1 Evidence Objects; correlation-aware Investigation Priority + separate Evidence Confidence; CONFLICTING_EVIDENCE; GET /api/v2/projects/{id}/risk; V1.1 GET /api/v1/.../risk unchanged; see RISK_FUSION_V2_REPORT.md)
- [x] Relationship Graph V1 (2026-09-10: NetworkX ego-neighborhood; PROJECT/MP/CONSTITUENCY/CATEGORY/IDA/STATE; SIMILAR_TO from Overlap V1; Evidence Objects; GET /api/v1/projects/{id}/graph; not fused into Investigation Priority; see RELATIONSHIP_GRAPH_V1_REPORT.md)
- [x] Need & Impact V1 (2026-09-10: Need/Impact/Priority Scores; HIGH/MEDIUM/LOW/INCONCLUSIVE; constituency-first; TEST/SYNTHETIC enrichment labelled; planning-simulation ranking with hypothetical budget; GET /api/v1/projects/{id}/need-impact and POST /api/v1/need-impact/rank; not a sanction; not fused into Investigation Priority; see NEED_IMPACT_V1_REPORT.md)
- [x] ML Training & Inference V1 (2026-09-10: Isolation Forest cost-anomaly-v1 on REAL observed fields; Cost V1.1 remains the peer baseline; no supervised fraud classifier; HYBRID_TEST time model architecture only; POST /api/v2/ml/predict and POST /api/v2/projects/assess; see ML_TRAINING_INFERENCE_V1_REPORT.md)
- [x] ML → Evidence Integration V1 (2026-09-10: ML predictions persist as Evidence Object V1; POST /api/v2/projects/{id}/ml-evidence; GET /api/v1/projects/{id}/evidence includes ML; Passport/Workspace/Copilot retrieval; not fused into Risk Fusion V1.1 or V2; ML anomaly score is not a fraud probability; stored ML explanations use neutral anomaly language; see ML_EVIDENCE_INTEGRATION_V1_REPORT.md)
- [x] Real Contextual Data Enrichment V1 (2026-09-11: provenance-first external public context; MoHFW NCP state population snapshot; official SoR/NFHS/Census district not fabricated; GET /api/v2/projects/{id}/context; Evidence Object V1; Cost V1.1 / Need & Impact formula / Risk Fusion V1.1 and V2 unchanged; see REAL_CONTEXTUAL_DATA_ENRICHMENT_V1_REPORT.md)

## Phase 4 — Intelligence UI
- [x] Search (2026-09-10: officer search over observed fields; 2026-09-10 correction: AP default scope, State → Constituency cascade, Scheme ID, REAL/HYBRID; 2026-09-10 text-search correction: case-insensitive partial match across Scheme ID, internal_project_id, work_description, and MP name; Enter/Search button; URL state; zero-result empty state; see SEARCH_TEXT_V1_REPORT.md)
- [x] Project Digital Passport (2026-09-10: identity, finance, intelligence, evidence, comparables, relationship summary; 2026-09-10 correction: Scheme ID, REAL source vs SYNTHETIC enrichment, honest unavailable fields)
- [ ] Comparable Projects
- [x] Investigation Workspace (2026-09-10: why-flagged, signals, evidence, officer CONFIRM CONCERN / DISMISS / NEED MORE INFORMATION; 2026-09-10 correction: Scheme ID, data mode, disposition groups, scores unchanged; 2026-09-10: Risk Fusion V2 display)
- [x] AP pilot and data-mode UI correction (2026-09-10: current pilot Andhra Pradesh without deleting other states; deterministic SVK-AP-NNNNNN Scheme ID; HYBRID DEMO default; REAL mode never consumes synthetic enrichment; Cost/Time/Overlap/Compliance/Risk/Graph engines unchanged; see AP_PILOT_AND_DATA_MODE_UI_V1_REPORT.md)
- [x] Relationship Graph Visualization V1 (2026-09-10: officer SVG ego-neighborhood from GET /api/v1/projects/{id}/graph; click/hover details; similar-node cap with expand; passport compact summary + Open Relationship Graph; Investigation Workspace section; REAL/HYBRID labelled; not fused into Investigation Priority; see RELATIONSHIP_GRAPH_UI_V1_REPORT.md)
- [x] Need & Impact (2026-09-10: Need & Impact V1 section on passport/workspace plus ranking page; GET /api/v1/projects/{id}/need-impact; POST /api/v1/need-impact/rank; see NEED_IMPACT_V1_REPORT.md)
- [x] Contextual Intelligence (2026-09-11: functional passport/workspace section; PROJECT OBSERVATION vs EXTERNAL CONTEXT vs DERIVED COMPARISON; GET /api/v2/projects/{id}/context; Cost V1.1 / Need & Impact / Risk Fusion unchanged; see REAL_CONTEXTUAL_DATA_ENRICHMENT_V1_REPORT.md; 2026-09-11: observation list keys use indicator+source+geo+period, not indicator alone)

## Phase 5 — Evidence
- [x] Plan–Claim–Evidence V1 (2026-09-10: PLAN/CLAIM/EVIDENCE recording; deterministic CONSISTENT / MISMATCH / INCONCLUSIVE; existing Evidence Object + document/photo tables; no OCR/satellite CV/image-authenticity engine; not fused into Investigation Priority; see PLAN_CLAIM_EVIDENCE_V1_REPORT.md)
- [x] Documents (2026-09-10: Document & Blueprint Intelligence V1; PDF/PNG/JPEG upload; SHA-256; officer-selected type; on-demand labelled extraction; Evidence Object V1; see DOCUMENT_BLUEPRINT_V1_REPORT.md)
- [x] Blueprint/BOQ (2026-09-10: normalized optional scope/quantity/dimension/finance/milestone/date structure; plan attach without silent overwrite; PLAN DATA CONFLICT; PCE comparison reuse; see DOCUMENT_BLUEPRINT_V1_REPORT.md)
- [x] Image reuse (2026-09-10: Image Evidence & Authenticity V1; SHA-256 exact duplicate; aHash/dHash/pHash potential reuse; reported EXIF GPS/timestamp; technical quality; Evidence Object V1; PCE attach; advanced authenticity INCONCLUSIVE/NOT_IMPLEMENTED; see IMAGE_EVIDENCE_V1_REPORT.md)
- [x] Metadata (2026-09-10: reported EXIF fields only; GPS/timestamp not inferred; labelled “reported metadata from uploaded file”; see IMAGE_EVIDENCE_V1_REPORT.md)
- [x] Geospatial consistency (2026-09-10: Geospatial Consistency V1; haversine vs 500 m prototype threshold; REAL project GPS unavailable → INCONCLUSIVE; HYBRID uses labelled SYNTHETIC enrichment coordinates; Image Evidence EXIF GPS reused; Evidence Object V1; PCE framing; satellite unavailable; not fused into Investigation Priority; see GEOSPATIAL_V1_REPORT.md)
- [x] Image Forensics (2026-09-10: Advanced Image Forensics V1; integrity/metadata/transform/manipulation/AI-unavailable pipeline on Image Evidence V1 photos; independent signals; prototype assessment not a validated authenticity decision; Evidence Object V1; PCE framing without marking claims false; not fused into Investigation Priority; see IMAGE_FORENSICS_V1_REPORT.md)
- [x] Satellite / remote sensing (2026-09-10: Satellite / Remote-Sensing Consistency V1; provider abstraction; REAL/no-API → SATELLITE_UNAVAILABLE; HYBRID TEST mock metadata labelled not-official; coverage/temporal/change with resolution-aware INCONCLUSIVE; Evidence Object V1; PCE framing without marking claims false; not fused into Investigation Priority; see SATELLITE_REMOTE_SENSING_V1_REPORT.md)

## Phase 6 — Field workflows
- [x] Jan-Sakshi (2026-09-10: Jan-Sakshi / Citizen Evidence V1; 500 m prototype geo rule; Image Evidence reuse; watermark presentation copy; Evidence Object V1; PCE framing without marking claims false; not fused into Investigation Priority; see JAN_SAKSHI_V1_REPORT.md)
- [x] Milestone Advisor (2026-09-10: Milestone Advisor V1; PROCEED / HOLD / INSPECT / INCONCLUSIVE; officer PROCEED / HOLD / INSPECT / NEED MORE INFORMATION; Plan → Claim → Evidence reused; Risk Fusion V1.1 read-only; no fund release / PFMS; see MILESTONE_ADVISOR_V1_REPORT.md)

## Phase 7 — Copilot
- [x] Evidence retrieval (2026-09-10: structured DB retrieval of stored project/evidence/fusion/PCE/field layers; lexical overlap only for documents, citizen text, and explanations; see INVESTIGATION_COPILOT_V1_REPORT.md)
- [x] RAG (2026-09-10: intent parse → retrieve → context → provider → grounding; deterministic templates default; optional local/external LLM isolated and off by default)
- [x] Guardrails (2026-09-10: no fabricated facts/citations, no legal fraud claims, no unsupported rules, no hidden HYBRID/SYNTHETIC, no payment/sanction recommendations)
- [x] Contextual Q&A (2026-09-10: project-scoped session memory; POST /api/v1/projects/{id}/copilot/chat; GET .../copilot/context; Investigation Workspace panel)
- [x] External contextual retrieval (2026-09-11: Copilot EXTERNAL_CONTEXT intent; source and reference-period facts; regional statistic is not a project-specific fact; no fraud inference; see REAL_CONTEXTUAL_DATA_ENRICHMENT_V1_REPORT.md)

## Phase 8 — Demo
- [x] End-to-End Lifecycle V1 (2026-09-10: FUTURE / ONGOING / COMPLETED orchestration; GET /api/v2/projects/{id}/lifecycle; Passport/Workspace LIFECYCLE section; Copilot lifecycle context; frozen engines and Risk Fusion V2 formula unchanged; see END_TO_END_LIFECYCLE_V1_REPORT.md)
- [x] Ghost case (2026-09-10: existing DEMO_GHOST project; /demo launch; journey PROJECT→SUMMARY; HYBRID GPS labelled SYNTHETIC; live V2 not forced to INSPECT; 2026-09-10 correction: Demo Evidence Fixtures V1 attach labelled HYBRID Evidence Objects through existing APIs so V2 is no longer IP 0 from empty storage; see DEMO_EVIDENCE_FIXTURES_V1_REPORT.md)
- [x] Over-bill case (2026-09-10: existing DEMO_OVERBILL project; labelled SYNTHETIC expenditure vs observed allocation; Cost/Compliance/PCE not mutated; 2026-09-10 correction: Demo Evidence Fixtures V1 persist Cost/Compliance/PCE/Milestone Evidence Objects; V2 formula unchanged)
- [x] Stuck case (2026-09-10: existing DEMO_STUCK ONGOING project; labelled schedule/progress enrichment; milestone actions remain on Milestone Advisor; 2026-09-10 correction: Demo Evidence Fixtures V1 persist Time/Milestone/PCE Evidence Objects; V2 formula unchanged)
- [x] Clean case (2026-09-10: existing DEMO_CLEAN FUTURE project; V2 MONITOR IP 20 not forced to zero; Need & Impact still NEED MORE INFORMATION; 2026-09-10 correction: Demo Evidence Fixtures V1 add supporting HYBRID plan/claim/image/geo/citizen evidence; score still not forced to zero)

## Phase 9 — Validation
- [x] Unit tests (foundation: health, SQLite, observed schema, empty list, profiling, work-level cleaning, SQLite load, synthetic enrichment)
- [x] Integration tests (2026-09-11: Full-System Validation V1; isolated API-chain tests plus live read-only integrity; engines and Risk Fusion V2 formula unchanged; see FULL_SYSTEM_VALIDATION_V1_REPORT.md)
- [x] Model evaluation (2026-09-10: unsupervised Isolation Forest diagnostics; no fraud accuracy/F1/AUC; synthetic labels held-out after scoring; see ML_TRAINING_INFERENCE_V1_REPORT.md)
- [x] Synthetic enrichment validation (HYBRID labels, uniqueness, scenario mix, demo cases, date/amount constraints)
- [x] Data validation (2026-09-11: 56,138 real records, file hashes, REAL/HYBRID/SYNTHETIC separation, evidence orphans, demo identity; see FULL_SYSTEM_VALIDATION_V1_REPORT.md)
- [x] Evidence validation (2026-09-10: schema, provenance, REAL/HYBRID, dispositions, no-fraud-claim, engine adapters)
- [x] Plan–Claim–Evidence V1 tests (2026-09-10: consistent / mismatch / inconclusive, missing fields, quantity and cost caps, REAL vs HYBRID, provenance, evidence linking, deterministic results)
- [x] Document & Blueprint V1 tests (2026-09-10: PDF/image upload, rejection, hash/duplicates, labelled extraction, confidence/page refs, plan attach conflicts, PCE cases, REAL/HYBRID, inconclusive OCR)
- [x] Image Evidence V1 tests (2026-09-10: upload, MIME/size, SHA-256, exact duplicate, perceptual near-duplicate, EXIF GPS/timestamp, missing metadata, quality, Evidence Objects, REAL/HYBRID/SYNTHETIC, provenance, no-fraud wording, authenticity INCONCLUSIVE)
- [x] Geospatial Consistency V1 tests (2026-09-10: haversine, same coordinates, within/boundary/outside 500 m, missing project GPS, missing image GPS, mixed images, DEMO_GHOST-style mismatch, REAL vs HYBRID/SYNTHETIC, Evidence Objects, provenance, satellite unavailable, no-fraud wording)
- [x] Need & Impact V1 tests (2026-09-10: high/low need and impact, missing inputs, INCONCLUSIVE, ranking, budget simulation, ties, deterministic scoring, provenance, REAL/HYBRID, no fabricated values, no automatic sanctioning)
- [x] Milestone Advisor V1 tests (2026-09-10: creation, ordering, amounts, cumulative/missing amount, progress, PCE integration, PROCEED / HOLD / INSPECT / INCONCLUSIVE, NEED MORE INFORMATION, officer audit, score immutability, REAL/HYBRID, provenance, no payment/PFMS, no fraud wording, deterministic assessment)
- [x] Jan-Sakshi V1 tests (2026-09-10: 180 m accept, 1.8 km reject, exact 500 m, missing citizen/project GPS, missing timestamp, missing/invalid image, duplicate image, watermark original preserved, grounded sentiment, insufficient text, aggregation/sample size, privacy GPS omitted, REAL/HYBRID/SYNTHETIC, Evidence Objects, PCE claim-not-false, Risk Fusion unchanged, no-fraud wording, deterministic)
- [x] Image Forensics V1 tests (2026-09-10: metadata analysis, missing EXIF, inconsistent metadata, recompression, resize, duplicate, near duplicate, manipulation signal, inconclusive, AI detector unavailable, Evidence Object, PCE integration without marking claims false, REAL/HYBRID/SYNTHETIC, provenance, original bytes unchanged, deterministic, no-fraud wording, no false certainty)
- [x] Satellite / Remote-Sensing V1 tests (2026-09-10: provider abstraction, imagery unavailable/available, matching/wrong location, before/after change, no visible change, insufficient resolution, wrong imagery date, REAL/no-provider, HYBRID TEST mock, missing project GPS, Evidence Object, PCE claim-not-false, Risk Fusion unchanged, provenance, no-fraud wording, deterministic)
- [x] Investigation Copilot V1 tests (2026-09-10: why flagged / why not, supporting and missing evidence, time inconclusive, comparables, PCE, inspect-next, REAL/HYBRID, unavailable satellite/GPS, citizen/milestone/graph, hallucination prevention, source references, no-fraud wording, no unsupported rules, deterministic retrieval, LLM unavailable fallback, Risk Fusion unchanged)
- [x] Risk Fusion V2 tests (2026-09-10: all groups, one group, missing/unavailable/not-assessable, correlated overlap+graph, independent corroboration, conflicting evidence, high priority + low confidence, REAL/HYBRID/SYNTHETIC, duplicates, bounds, deterministic, monotonicity, history, officer scores unchanged, no-fraud wording)
- [x] End-to-End Lifecycle V1 tests (2026-09-10: future/ongoing/completed/unknown, planning transition, missing evidence, REAL/HYBRID/SYNTHETIC, milestone/PCE/risk/citizen/geo/satellite/document/image/officer, timeline, data mode, no sanction/payment/fraud, deterministic state, Copilot lifecycle context)
- [x] ML Training & Inference V1 tests (2026-09-10: deterministic Isolation Forest training, leakage exclusion, missing/unseen features, model missing/version mismatch, synthetic labels after scoring, frozen engines unchanged, POST /api/v2/ml/predict and /api/v2/projects/assess)
- [x] ML → Evidence Integration V1 tests (2026-09-10: stored ML Evidence Objects, provenance, model versioning, immutability, REAL/HYBRID/SYNTHETIC, failure modes, existing evidence API, Copilot retrieval, fraud-probability clarification, stored explanation neutrality, Risk Fusion formula unchanged)
- [x] Real Contextual Data Enrichment V1 tests (2026-09-11: source registry provenance, MoHFW population snapshot, malformed/timeout/stale/missing geography/incompatible units, Evidence Objects, REAL/HYBRID/SYNTHETIC, NEW_PROJECT_ASSESSMENT, Copilot retrieval, Cost V1.1 / Need & Impact / Risk Fusion unchanged)

## Phase 10 — Finalization
- [x] UI polish (2026-09-10: UI Polish V1; cohesive government decision-support chrome; AP pilot + REAL/HYBRID identity; dashboard from available search totals only; Passport/Workspace visual structure; lazy tabs; no engine changes; see UI_POLISH_V1_REPORT.md)
- [x] FINAL UI/UX REDESIGN V1 (2026-09-11: investigation-console visual system; sidebar shell; command-center dashboard from existing search totals only; Passport/Workspace/Search/Demo/Assessment restyle; REAL/HYBRID/SYNTHETIC distinction; no engine or API contract changes; see FINAL_UI_UX_REDESIGN_V1_REPORT.md)
- [x] FINAL UI/UX REBUILD V2 (2026-09-11: light premium information-architecture rebuild; unified Projects & Search; discoverable Evidence/Geospatial/ML/Copilot/Milestones/Prioritization/Assess/Demo journeys; no engine or API contract changes; see FINAL_UI_UX_REBUILD_V2_REPORT.md)
- [x] FINAL VISUAL PRODUCT TRANSFORMATION V3 (2026-09-11: hub navigation, compact environment chip, command-center dashboard, Passport/Investigation/ML/Geo/Jan-Sakshi/Prioritization/Assess/Demo visual system; frontend only; see FINAL_UI_UX_VISUAL_TRANSFORMATION_V3_REPORT.md)
- [x] FINAL UI/UX PRODUCT REFINEMENT V4 (2026-09-11: task-based information architecture; Evidence, Verification, Analytics, Planning, Lifecycle, AI & Models, and Context as separate primary sections; frontend only; see FINAL_UI_UX_PRODUCT_REFINEMENT_V4_REPORT.md)
- [ ] Deployment
- [ ] Demo rehearsal
- [ ] Presentation
- [ ] Viva preparation
