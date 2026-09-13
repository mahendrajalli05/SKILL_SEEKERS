"""Advanced Image Forensics V1 constants.

Decision-support signals only. Does not conclude that an image is fake,
fraudulent, definitely AI-generated, or definitely manipulated.
Does not modify Image Evidence V1 or Risk Fusion V1.1.
"""

from __future__ import annotations

ENGINE_NAME = "forensics"
ENGINE_VERSION = "image-forensics-v1"

POTENTIAL_MANIPULATION = "POTENTIAL_MANIPULATION"
POTENTIAL_AI_GENERATION = "POTENTIAL_AI_GENERATION"
METADATA_ANOMALY = "METADATA_ANOMALY"
INCONCLUSIVE = "INCONCLUSIVE"
NO_STRONG_FORENSIC_SIGNAL = "NO_STRONG_FORENSIC_SIGNAL"
AI_GENERATION_ANALYSIS_UNAVAILABLE = "AI_GENERATION_ANALYSIS_UNAVAILABLE"

REVIEW_REQUIRED = "REVIEW_REQUIRED"

CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"

SIGNAL_MANIPULATION = "manipulation_signal"
SIGNAL_AI = "ai_generation_signal"
SIGNAL_METADATA = "metadata_signal"
SIGNAL_REUSE = "reuse_signal"
SIGNAL_QUALITY = "quality_signal"

INTEGRITY_OK = "INTEGRITY_OK"
INTEGRITY_UNREADABLE = "UNREADABLE"
INTEGRITY_HASH_MISMATCH = "HASH_MISMATCH"
INTEGRITY_MISSING_FILE = "MISSING_FILE"

EXIF_UNAVAILABLE = "EXIF_UNAVAILABLE"
TIMESTAMP_AVAILABLE = "TIMESTAMP_AVAILABLE"
TIMESTAMP_UNAVAILABLE = "TIMESTAMP_UNAVAILABLE"

AI_BACKEND_UNAVAILABLE = "unavailable"
AI_CAPABILITY_UNAVAILABLE = "AI_GENERATION_ANALYSIS_UNAVAILABLE"

PROTOTYPE_ASSESSMENT_LABEL = (
    "Prototype forensic assessment — not a validated authenticity decision."
)

TEST_WATERMARK = (
    "TEST DATA — SYNTHETIC forensic image fixture. "
    "Not an official government photograph and not real field evidence."
)

EDITOR_SOFTWARE_TOKENS = (
    "photoshop",
    "adobe photoshop",
    "lightroom",
    "gimp",
    "paint.net",
    "affinity",
    "snapseed",
    "pixelmator",
    "canva",
    "picsart",
    "facetune",
    "generative fill",
    "content-aware",
)

AI_SOFTWARE_TOKENS = (
    "midjourney",
    "dall-e",
    "dalle",
    "stable diffusion",
    "firefly",
    "generative ai",
    "synthetic-ai-fixture",
)

TIMESTAMP_MISMATCH_SECONDS = 24 * 60 * 60
COPY_MOVE_BLOCK_PX = 16
COPY_MOVE_MIN_PAIRS = 1
COPY_MOVE_MIN_SEPARATION_BLOCKS = 2
RECOMPRESSION_LOW_QUALITY = 70
ELA_UNEVEN_RATIO = 8.0
CONFIDENCE_REAL_CAP = 0.55
CONFIDENCE_HYBRID_CAP = 0.40
CONFIDENCE_SYNTHETIC_CAP = 0.35

FORBIDDEN_CERTAINTY_TOKENS = (
    "fake",
    "fraud",
    "fraudulent",
    "definitely ai-generated",
    "definitely manipulated",
    "definitely ai generated",
)

GOVERNANCE_NOTE = (
    "Image Forensics V1 is a decision-support layer for submitted project images. "
    "Signals may indicate possible manipulation, possible AI-generation, "
    "suspicious metadata, or inconsistent transformations. "
    "They are not a legal finding and not a validated authenticity decision. "
    "Missing EXIF is not proof of manipulation. "
    "AI recommends. Authorized officers decide."
)

CLAIM_PHOTO_COMPLETED = "Photo shows completed work."
PCE_CLAIM_NOT_FALSE_NOTE = (
    "Forensic findings do not mark the claim false. They are supporting evidence for review."
)
PCE_REVIEW_REQUIRED = "Review required."

LIMITATIONS = (
    "No validated AI-generated-image detector is bundled in V1.",
    "Error-level / recompression residue is a prototype indicator, not a validated manipulation test.",
    "Missing EXIF is not proof of manipulation.",
    "Exact duplicate and potential reuse are reused from Image Evidence V1 and are not legal findings.",
    "Project images are not transmitted to external services by default.",
    "Filesystem paths are not exposed.",
    "Image Forensics is not fused into Investigation Priority (Risk Fusion V1.1 unchanged).",
    "Synthetic test images are not real field evidence.",
)

ASSESSMENT_FORMULA = (
    "overall = REVIEW_REQUIRED if manipulation_signal is POTENTIAL_MANIPULATION "
    "or reuse_signal is EXACT_DUPLICATE or POTENTIAL_IMAGE_REUSE "
    "or metadata_signal is METADATA_ANOMALY; "
    "else INCONCLUSIVE if every independent signal is INCONCLUSIVE or UNAVAILABLE; "
    "else NO_STRONG_FORENSIC_SIGNAL. "
    "No combined authenticity probability is produced."
)
