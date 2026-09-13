"""Investigation Copilot V1 constants.

Explains stored SARVSAKSHI evidence. Does not recalculate Cost, Time,
Overlap, Compliance, or Risk Fusion scores.
"""

from __future__ import annotations

ENGINE_NAME = "copilot"
ENGINE_VERSION = "investigation-copilot-v1"

UNAVAILABLE_PHRASE = "That information is not available in the current evidence."
INSUFFICIENT_PHRASE = "I don't have enough evidence to answer that confidently."
NOT_ASSESSABLE_PRESERVE = "NOT_ASSESSABLE"

TIME_REAL_LIMITATION = (
    "Time Intelligence cannot determine actual delay because verified "
    "execution dates are unavailable in the current real dataset."
)

HYBRID_NOTICE = (
    "This answer uses the HYBRID prototype enrichment for some fields. "
    "Those values are synthetic and are not official MPLADS records."
)

SYNTHETIC_NOTICE = (
    "This answer uses a SYNTHETIC test record. It is not a government project "
    "and is for controlled testing only."
)

REAL_NOTICE = (
    "This answer uses REAL observed MPLADS extract fields and stored evidence only. "
    "Synthetic enrichment is not used."
)

GOVERNANCE_NOTE = (
    "Investigation Copilot explains stored evidence. It does not determine fraud, "
    "sanction a project, or release funds. AI recommends. Authorized officers decide."
)

CITIZEN_LIMITATION = (
    "Citizen evidence is supporting evidence only. One citizen report does not "
    "establish truth."
)

SATELLITE_UNAVAILABLE = (
    "Satellite verification cannot be completed because imagery is unavailable "
    "or project GPS is not present in the current evidence."
)

GPS_UNAVAILABLE = (
    "Project GPS coordinates are not available in the current real extract "
    "and are not stored on the project record."
)

ML_NOT_FRAUD_PROBABILITY = (
    "The ML anomaly score is not a fraud probability. It is an unsupervised "
    "distributional rank versus the training set. SARVSAKSHI does not determine "
    "legal fraud. The score is not a wrongdoing probability, a legal conclusion, "
    "or confirmed misconduct. The model cannot determine fraud or legal "
    "wrongdoing. Authorized officers decide."
)

ML_UNAVAILABLE = "No stored ML Evidence Object is available for this project."

CONTEXT_NOT_PROJECT_FACT = (
    "External context is external context. A regional statistic is not a "
    "project-specific fact, not a beneficiary count, and not a legal conclusion."
)

MAX_SESSION_TURNS = 8
MAX_QUESTION_CHARS = 2000
MAX_ANSWER_CHARS = 8000
MAX_SEMANTIC_HITS = 6
MAX_CITIZEN_SNIPPETS = 8
MAX_DOCUMENT_SNIPPETS = 6

ALLOWED_RECOMMENDATIONS = (
    "MONITOR",
    "REVIEW",
    "INSPECT",
    "NEED MORE INFORMATION",
)

FORBIDDEN_RECOMMENDATIONS = (
    "automatic sanction",
    "automatic payment",
    "legal action",
    "fraud declaration",
    "release funds",
    "pfms",
)

SUGGESTED_QUESTIONS = (
    "Why is this project flagged?",
    "What evidence is strongest?",
    "Why is Time Intelligence inconclusive?",
    "Show comparable projects.",
    "What should I inspect next?",
    "Summarize Plan → Claim → Evidence.",
    "What ML signal exists for this project?",
)

PATH_LEAK_PATTERN = r"(?:[A-Za-z]:\\|/(?:Users|home|var|etc|opt)/|\\\\)"
SECRET_LEAK_PATTERN = r"(?:api[_-]?key|secret|password|bearer\s+[A-Za-z0-9._\-]+)"
FRAUD_CLAIM_PATTERN = r"\bfraud(ulent)?\b"
LEGAL_CONCLUSION_PATTERN = r"\b(?:guilty|criminal|illegal\s+act|legally\s+established)\b"
SANCTION_PATTERN = r"\b(?:automatically\s+sanction|release\s+funds|pfms\s+payment)\b"
