"""Safe upload handling for Document & Blueprint V1.

Allowed types only. Files are never executed.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.engines.document.constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    FORBIDDEN_EXTENSIONS,
    MAX_FILE_BYTES,
)
from app.engines.document.errors import DocumentError

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")
_MULTI_DOT = re.compile(r"\.{2,}")

PDF_MAGIC = b"%PDF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sniff_mime(payload: bytes) -> str | None:
    if payload.startswith(PDF_MAGIC):
        return "application/pdf"
    if payload.startswith(PNG_MAGIC):
        return "image/png"
    if payload.startswith(JPEG_MAGIC):
        return "image/jpeg"
    return None


def sanitize_filename(filename: str | None, *, mime_type: str) -> str:
    raw = Path(filename or "upload").name
    raw = raw.replace("\x00", "")
    raw = raw.replace("\\", "_").replace("/", "_")
    raw = _MULTI_DOT.sub(".", raw)
    stem = Path(raw).stem
    ext = Path(raw).suffix.casefold()
    stem = _UNSAFE_CHARS.sub("_", stem).strip("._") or "upload"
    stem = stem[:80]
    if ext not in ALLOWED_EXTENSIONS:
        ext = {
            "application/pdf": ".pdf",
            "image/png": ".png",
            "image/jpeg": ".jpg",
        }.get(mime_type, "")
    if ext not in ALLOWED_EXTENSIONS:
        raise DocumentError(
            "Filename extension is not an allowed document type.",
            code="invalid_file_type",
            status_code=422,
        )
    return f"{stem}{ext}"


def validate_upload(payload: bytes, filename: str | None, declared_mime: str | None) -> tuple[str, str, int, str]:
    if not payload:
        raise DocumentError("Uploaded file is empty.", code="empty_file", status_code=422)
    size = len(payload)
    if size > MAX_FILE_BYTES:
        raise DocumentError(
            f"File exceeds the maximum size of {MAX_FILE_BYTES} bytes.",
            code="file_too_large",
            status_code=422,
        )
    ext = Path(filename or "").suffix.casefold()
    if ext in FORBIDDEN_EXTENSIONS:
        raise DocumentError(
            "Executable or disallowed file types cannot be uploaded.",
            code="invalid_file_type",
            status_code=422,
        )
    sniffed = sniff_mime(payload)
    if sniffed is None:
        raise DocumentError(
            "Only PDF, PNG, and JPEG files are accepted. The file signature was not recognised.",
            code="invalid_file_type",
            status_code=422,
        )
    declared = (declared_mime or "").casefold().split(";")[0].strip()
    if declared in {"image/jpg", "image/pjpeg"}:
        declared = "image/jpeg"
    if declared and declared not in ALLOWED_MIME_TYPES:
        raise DocumentError(
            "Only PDF, PNG, and JPEG MIME types are accepted.",
            code="invalid_file_type",
            status_code=422,
        )
    if declared and declared != sniffed:
        raise DocumentError(
            "Declared file type does not match the file contents.",
            code="invalid_file_type",
            status_code=422,
        )
    if sniffed not in ALLOWED_MIME_TYPES:
        raise DocumentError(
            "Only PDF, PNG, and JPEG files are accepted.",
            code="invalid_file_type",
            status_code=422,
        )
    if ext and ext not in ALLOWED_EXTENSIONS:
        raise DocumentError(
            "Only .pdf, .png, .jpg, and .jpeg uploads are accepted.",
            code="invalid_file_type",
            status_code=422,
        )
    safe_name = sanitize_filename(filename, mime_type=sniffed)
    digest = sha256_bytes(payload)
    return sniffed, safe_name, size, digest
