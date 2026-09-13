"""Advanced Image Forensics V1.

Decision-support forensic assistance for submitted project images.
Reuses Image Evidence V1 storage, hashes, EXIF, and quality checks.
Does not determine fraud and is not fused into Investigation Priority.
"""

from app.engines.forensics.constants import ENGINE_NAME, ENGINE_VERSION

__all__ = ["ENGINE_NAME", "ENGINE_VERSION"]
