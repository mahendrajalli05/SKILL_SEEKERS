"""File integrity checks. Original uploaded bytes are not modified."""

from __future__ import annotations

from app.engines.forensics.constants import (
    INTEGRITY_HASH_MISMATCH,
    INTEGRITY_MISSING_FILE,
    INTEGRITY_OK,
    INTEGRITY_UNREADABLE,
)
from app.engines.forensics.types import IntegrityCheck
from app.engines.image.quality import assess_quality
from app.engines.image.security import sha256_bytes


def check_integrity(
    payload: bytes | None,
    *,
    stored_sha256: str | None,
    mime_type: str | None,
    file_size: int | None,
) -> IntegrityCheck:
    if payload is None:
        return IntegrityCheck(
            status=INTEGRITY_MISSING_FILE,
            readable=False,
            content_sha256="",
            stored_sha256=stored_sha256,
            bytes_unmodified=False,
            mime_type=mime_type,
            file_size=file_size,
            notes=["Stored image bytes were not available. Forensics did not invent a file."],
        )
    digest = sha256_bytes(payload)
    quality = assess_quality(payload)
    readable = bool(quality.get("readable"))
    matches = bool(stored_sha256) and digest == stored_sha256
    notes = [
        "Forensic analysis reads stored bytes only. The original uploaded file is not rewritten.",
    ]
    if not stored_sha256:
        notes.append("Stored SHA-256 was unavailable, so integrity could not be fully confirmed.")
        status = INTEGRITY_UNREADABLE if not readable else INTEGRITY_OK
        unmodified = True
    elif not matches:
        notes.append("Computed SHA-256 does not match the stored Image Evidence hash.")
        status = INTEGRITY_HASH_MISMATCH
        unmodified = False
    elif not readable:
        status = INTEGRITY_UNREADABLE
        unmodified = True
        notes.append("File hash matches, but the payload could not be decoded as an image.")
    else:
        status = INTEGRITY_OK
        unmodified = True
        notes.append("SHA-256 matches the stored Image Evidence hash. Original bytes are unchanged.")
    return IntegrityCheck(
        status=status,
        readable=readable,
        content_sha256=digest,
        stored_sha256=stored_sha256,
        bytes_unmodified=unmodified,
        mime_type=mime_type,
        file_size=file_size if file_size is not None else len(payload),
        notes=notes,
    )
