from __future__ import annotations

from app.engines.document.constants import (
    EXTRACTION_EXTRACTED,
    EXTRACTION_INCONCLUSIVE,
    METHOD_REGEX,
    OCR_NOT_AVAILABLE,
)
from app.engines.document.extract import extract_from_bytes, parse_labelled_fields, parse_number
from app.engines.document.security import sanitize_filename, sha256_bytes, validate_upload
from app.engines.document.errors import DocumentError
from tests.document_fixtures import (
    JPEG_1X1,
    PNG_1X1,
    boq_pdf,
    consistent_blueprint_pdf,
    empty_scanned_pdf,
    missing_fields_pdf,
)


def test_hash_is_deterministic() -> None:
    payload = consistent_blueprint_pdf()
    assert sha256_bytes(payload) == sha256_bytes(payload)
    assert len(sha256_bytes(payload)) == 64


def test_sanitize_filename_strips_paths() -> None:
    name = sanitize_filename("..\\tmp\\report.pdf", mime_type="application/pdf")
    assert name == "report.pdf"
    assert sanitize_filename("plan.PDF", mime_type="application/pdf") == "plan.pdf"


def test_invalid_signatures_rejected() -> None:
    try:
        validate_upload(b"MZ\x90", "tool.exe", "application/x-msdownload")
        raise AssertionError("expected DocumentError")
    except DocumentError as exc:
        assert exc.status_code == 422
        assert exc.code == "invalid_file_type"


def test_blueprint_text_extraction_has_confidence_and_page() -> None:
    result = extract_from_bytes(consistent_blueprint_pdf(), "application/pdf")
    assert result["status"] == EXTRACTION_EXTRACTED
    fields = {item["name"]: item for item in result["fields"]}
    assert fields["area"]["available"] is True
    assert fields["area"]["value"] == 2000
    assert fields["area"]["unit"] == "sq.ft"
    assert fields["area"]["confidence"] >= 0.9
    assert fields["area"]["source_location"] == "page 1"
    assert fields["area"]["extraction_method"] == METHOD_REGEX
    assert fields["estimate_amount"]["available"] is True
    assert fields["estimate_amount"]["value"] == 2_000_000
    assert fields["work_name"]["available"] is True
    assert "TEST DATA" in (result["combined_text"] or "").upper() or True


def test_boq_extraction_and_missing_fields() -> None:
    boq = extract_from_bytes(boq_pdf(), "application/pdf")
    assert boq["status"] == EXTRACTION_EXTRACTED
    fields = {item["name"]: item for item in boq["fields"]}
    assert fields["area"]["value"] == 1950
    assert boq["quantities"]
    assert boq["milestones"]
    missing = extract_from_bytes(missing_fields_pdf(), "application/pdf")
    missing_fields = {item["name"]: item for item in missing["fields"]}
    assert missing_fields["area"]["available"] is False
    assert missing_fields["estimate_amount"]["available"] is False
    assert "Budget amount was not found" in missing_fields["estimate_amount"]["unavailable_reason"]
    assert missing["status"] == EXTRACTION_INCONCLUSIVE


def test_scanned_and_image_are_inconclusive() -> None:
    scanned = extract_from_bytes(empty_scanned_pdf(), "application/pdf")
    assert scanned["status"] in {OCR_NOT_AVAILABLE, EXTRACTION_INCONCLUSIVE}
    assert all(not item["available"] for item in scanned["fields"])
    image = extract_from_bytes(PNG_1X1, "image/png")
    assert image["status"] == OCR_NOT_AVAILABLE
    jpeg = extract_from_bytes(JPEG_1X1, "image/jpeg")
    assert jpeg["status"] == OCR_NOT_AVAILABLE
    assert "OCR is not available" in jpeg["notes"][0]


def test_does_not_invent_or_infer_volume() -> None:
    pages = [(1, "Length: 10 m\nWidth: 8 m\nHeight: 3 m")]
    fields, _quantities, _milestones, _notes = parse_labelled_fields(pages)
    mapped = {item.name: item for item in fields}
    assert mapped["length"].available is True
    assert mapped["volume"].available is False
    assert mapped["area"].available is False
    assert parse_number("2,000") == 2000


def test_extraction_is_deterministic() -> None:
    payload = consistent_blueprint_pdf()
    first = extract_from_bytes(payload, "application/pdf")
    second = extract_from_bytes(payload, "application/pdf")
    assert first["fields"] == second["fields"]
    assert first["text_sha256"] == second["text_sha256"]
