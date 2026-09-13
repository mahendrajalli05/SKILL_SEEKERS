from __future__ import annotations

from app.engines.image.constants import GPS_UNAVAILABLE_MESSAGE, METADATA_SOURCE_LABEL, METADATA_UNAVAILABLE
from app.engines.image.metadata import extract_metadata
from app.engines.image.security import sha256_bytes
from tests.image_fixtures import (
    TEST_CAMERA_MAKE,
    TEST_LATITUDE,
    TEST_LONGITUDE,
    jpeg_with_exif_gps,
    unique_png,
)


def test_missing_metadata_is_unavailable() -> None:
    result = extract_metadata(unique_png())
    assert result["status"] == METADATA_UNAVAILABLE
    assert result["gps_available"] is False
    assert result["gps_message"] == GPS_UNAVAILABLE_MESSAGE
    assert result["capture_timestamp"] is None
    assert result["latitude"] is None
    names = {item.field: item for item in result["fields"]}
    assert names["latitude"].available is False
    assert names["latitude"].source == METADATA_SOURCE_LABEL
    assert names["latitude"].extraction_method == "unavailable"


def test_exif_gps_and_timestamp_are_extracted_as_reported() -> None:
    payload = jpeg_with_exif_gps()
    result = extract_metadata(payload)
    assert result["status"] == "METADATA_PRESENT"
    assert result["gps_available"] is True
    assert result["latitude"] is not None
    assert result["longitude"] is not None
    assert abs(result["latitude"] - TEST_LATITUDE) < 0.01
    assert abs(result["longitude"] - TEST_LONGITUDE) < 0.01
    assert result["capture_timestamp"]
    assert result["camera_make"] == TEST_CAMERA_MAKE
    for item in result["fields"]:
        if item.available:
            assert item.source == METADATA_SOURCE_LABEL
            assert item.extraction_method == "exif"


def test_metadata_does_not_alter_original_bytes() -> None:
    payload = jpeg_with_exif_gps()
    before = sha256_bytes(payload)
    extract_metadata(payload)
    assert sha256_bytes(payload) == before
