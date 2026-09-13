"""Intelligence engines.

Cost Intelligence V1.1 lives under ``app.engines.cost`` and is frozen.
Time Intelligence V1 lives under ``app.engines.time`` and is frozen.
Overlap Intelligence V1 lives under ``app.engines.overlap`` and is frozen.
Compliance Engine V1 lives under ``app.engines.compliance`` and is frozen.
The shared Evidence Object layer lives under ``app.evidence``.
Risk Fusion V1.1 lives under ``app.engines.fusion`` and consumes those
objects. It does not reimplement Cost, Time, Overlap, or Compliance.
Risk Fusion V2 lives under ``app.engines.fusion_v2``. It consumes Evidence
Objects from frozen V1/V1.1 engines and does not change their scoring.
Relationship Graph V1 lives under ``app.engines.graph``. It writes
Evidence Objects and is not integrated into Risk Fusion V1.1.
Plan–Claim–Evidence V1 lives under ``app.engines.pce``. It compares recorded
plan, claim, and evidence fields and is not fused into Investigation Priority.
Document & Blueprint Intelligence V1 lives under ``app.engines.document``.
It extracts labelled fields from officer uploads and reuses Evidence Object V1.
Image Evidence & Authenticity V1 lives under ``app.engines.image``.
It stores officer photographs, hashes, and reported EXIF metadata.
It does not run satellite comparison or advanced AI-image detection.
Geospatial Consistency V1 lives under ``app.engines.geo``.
It compares reported image GPS with available project coordinates.
It does not download satellite imagery and does not invent REAL GPS.
Need & Impact V1 lives under ``app.engines.need``.
It produces decision-support priority for proposed/future works.
It does not sanction projects and is not fused into Investigation Priority.
Milestone Advisor V1 lives under ``app.engines.milestone``.
It recommends PROCEED / HOLD / INSPECT / INCONCLUSIVE for milestone readiness.
It does not release funds, integrate with PFMS, or change Risk Fusion V1.1.
Jan-Sakshi / Citizen Evidence V1 lives under ``app.engines.citizen``.
It records supporting citizen field reports with a 500 m prototype geo rule.
It does not produce a legal finding of wrongdoing and is not fused into Investigation Priority.
Advanced Image Forensics V1 lives under ``app.engines.forensics``.
It adds a decision-support layer on Image Evidence V1 photographs.
It does not claim an image is fake or fraudulent and is not fused into Investigation Priority.
Satellite / Remote-Sensing Consistency V1 lives under ``app.engines.satellite``.
It compares a claimed site with available imagery metadata through a provider
abstraction. It does not fabricate imagery and is not fused into Investigation Priority.
End-to-End Lifecycle Orchestration V1 lives under ``app.engines.lifecycle``.
It connects frozen engines into FUTURE / ONGOING / COMPLETED workflows.
It does not rewrite intelligence engines or the Risk Fusion V2 formula.
Real Contextual Data Enrichment V1 lives under ``app.engines.context``.
It adds provenance-first external public context without changing Cost V1.1,
Need & Impact V1, or Risk Fusion scores.
Engines write evidence objects and must not train a supervised fraud classifier.
"""
