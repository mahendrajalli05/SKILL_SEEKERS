"""Document & Blueprint Intelligence V1 constants.

Deterministic extraction and storage only. Does not run OCR or an LLM
by default. Does not conclude fraud. Does not change frozen engines.
"""

from __future__ import annotations

ENGINE_NAME = "document"
ENGINE_VERSION = "document-blueprint-v1"
SIGNAL_TYPE = "document"

MAX_FILE_BYTES = 10 * 1024 * 1024
AUTHORITATIVE_CONFIDENCE = 0.50
PLAN_CONFLICT_THRESHOLD = 0.10

ALLOWED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "image/png",
        "image/jpeg",
    }
)
ALLOWED_EXTENSIONS = frozenset({".pdf", ".png", ".jpg", ".jpeg"})
FORBIDDEN_EXTENSIONS = frozenset(
    {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".msi",
        ".dll",
        ".sh",
        ".ps1",
        ".js",
        ".jar",
        ".py",
        ".html",
        ".htm",
        ".svg",
        ".zip",
        ".rar",
        ".7z",
        ".scr",
        ".vbs",
        ".wsf",
    }
)

DOCUMENT_CLASSES = frozenset(
    {
        "BLUEPRINT",
        "BOQ_ESTIMATE",
        "PROJECT_DOCUMENT",
        "PROGRESS_REPORT",
        "COMPLETION_DOCUMENT",
        "OTHER",
    }
)

# Officer-selected class wins. Filename-based hints are only used when
# the caller did not supply a class.
PCE_TYPE_TO_CLASS = {
    "blueprint": "BLUEPRINT",
    "boq": "BOQ_ESTIMATE",
    "pdf": "PROJECT_DOCUMENT",
    "document": "PROJECT_DOCUMENT",
    "supporting_document": "PROJECT_DOCUMENT",
    "progress": "PROGRESS_REPORT",
    "completion": "COMPLETION_DOCUMENT",
    "other": "OTHER",
}

CLASS_TO_PCE_KIND = {
    "BLUEPRINT": "blueprint",
    "BOQ_ESTIMATE": "boq",
    "PROJECT_DOCUMENT": "document",
    "PROGRESS_REPORT": "document",
    "COMPLETION_DOCUMENT": "document",
    "OTHER": "supporting_document",
}

EXTRACT_FIELD_NAMES = (
    "work_name",
    "scope_description",
    "estimate_amount",
    "total_amount",
    "item_amount",
    "area",
    "length",
    "width",
    "height",
    "volume",
    "floors",
    "planned_start",
    "planned_completion",
    "agency_text",
    "reference_number",
)

EXTRACTION_NOT_RUN = "NOT_RUN"
EXTRACTION_EXTRACTED = "EXTRACTED"
EXTRACTION_INCONCLUSIVE = "INCONCLUSIVE"
OCR_NOT_AVAILABLE = "OCR_NOT_AVAILABLE"

INTEGRITY_UNIQUE = "UNIQUE"
INTEGRITY_DUPLICATE_FILE = "DUPLICATE_FILE"
INTEGRITY_SIMILAR_DOCUMENT = "SIMILAR_DOCUMENT"

METHOD_PDF_TEXT = "pdf_text"
METHOD_REGEX = "regex"
METHOD_UNAVAILABLE = "unavailable"
METHOD_OCR_NOT_AVAILABLE = "ocr_not_available"

GOVERNANCE_NOTE = (
    "Document & Blueprint Intelligence extracts labelled fields from officer "
    "uploads. Authenticity is not verified. Results are CONSISTENT, MISMATCH, "
    "INCONCLUSIVE, or PLAN DATA CONFLICT. This is not a legal finding. "
    "AI recommends. Authorized officers decide."
)

TEST_WATERMARK = "TEST DATA — not an official government document"

SCANNED_REASON = (
    "Dimensions could not be reliably extracted from this scanned document."
)
MISSING_BUDGET_REASON = "Budget amount was not found in the uploaded document."
OCR_REASON = (
    "OCR is not available in Document & Blueprint V1. Scanned PDFs and images "
    "cannot be read. Extraction is INCONCLUSIVE."
)
LOW_CONFIDENCE_REASON = (
    "Low-confidence extraction is not treated as authoritative."
)
NO_INFER_REASON = (
    "A value is unavailable. Exact measurements were not inferred from arbitrary text."
)
