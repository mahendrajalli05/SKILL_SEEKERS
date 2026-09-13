"""Document & Blueprint Intelligence V1.

Deterministic PDF text extraction and plan/evidence integration.
OCR and LLM are not required. Frozen Cost/Time/Overlap/Compliance engines
are unused. Evidence Object V1 is reused.
"""

from app.engines.document.constants import ENGINE_NAME, ENGINE_VERSION
from app.engines.document.service import extract_document, upload_document

__all__ = ["ENGINE_NAME", "ENGINE_VERSION", "extract_document", "upload_document"]
