from __future__ import annotations

from pathlib import Path

from app.engines.image.constants import MAX_FILE_BYTES
from app.engines.image.errors import ImageError
from app.engines.image.forensics import assess_authenticity
from app.engines.image.security import sanitize_filename, sha256_bytes, sniff_mime, validate_upload
from tests.image_fixtures import unique_png, webp_bytes


def test_sha256_matches_hashlib() -> None:
    payload = unique_png()
    assert sha256_bytes(payload) == __import__("hashlib").sha256(payload).hexdigest()


def test_sniff_rejects_non_image() -> None:
    assert sniff_mime(b"MZ executable") is None
    assert sniff_mime(b"<html>nope</html>") is None
    assert sniff_mime(unique_png()) == "image/png"


def test_invalid_mime_and_extension_rejected() -> None:
    try:
        validate_upload(b"MZ executable", "payload.exe", "application/octet-stream")
    except ImageError as exc:
        assert exc.status_code == 422
        assert exc.code == "invalid_file_type"
    else:
        raise AssertionError("exe must be rejected")
    try:
        validate_upload(b"<svg></svg>", "site.svg", "image/svg+xml")
    except ImageError as exc:
        assert exc.status_code == 422
    else:
        raise AssertionError("svg must be rejected")


def test_oversized_image_rejected() -> None:
    payload = b"\xff\xd8\xff" + b"a" * (MAX_FILE_BYTES + 10)
    try:
        validate_upload(payload, "big.jpg", "image/jpeg")
    except ImageError as exc:
        assert exc.status_code == 422
        assert exc.code == "file_too_large"
    else:
        raise AssertionError("oversized jpeg must be rejected")


def test_safe_filename_strips_paths() -> None:
    name = sanitize_filename("..\\windows\\system32\\site.PNG", mime_type="image/png")
    assert ".." not in name
    assert "\\" not in name
    assert "/" not in name
    assert name.endswith(".png")
    assert Path(name).name == name


def test_webp_accepted_when_signature_present() -> None:
    payload = webp_bytes()
    if payload is None:
        return
    mime, name, size, digest = validate_upload(payload, "shot.webp", "image/webp")
    assert mime == "image/webp"
    assert name.endswith(".webp")
    assert size == len(payload)
    assert digest == sha256_bytes(payload)


def test_advanced_authenticity_is_inconclusive() -> None:
    result = assess_authenticity(unique_png())
    assert result.capability == "NOT_IMPLEMENTED"
    assert result.result == "INCONCLUSIVE"
    assert result.score is None
    assert "inconclusive" in result.explanation.casefold()
    assert "fraud" not in result.explanation.casefold()
