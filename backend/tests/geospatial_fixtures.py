"""TEST/SYNTHETIC image bytes with chosen reported GPS. Not official photographs."""

from __future__ import annotations

from io import BytesIO

from PIL import Image

from tests.image_fixtures import TEST_CAMERA_MAKE, TEST_TIMESTAMP, _build_exif, _jpeg_bytes, unique_png

VIZIANAGARAM_LAT = 18.116700
VIZIANAGARAM_LON = 83.400000
DEMO_GHOST_LAT = 10.050000
DEMO_GHOST_LON = 68.400000


def jpeg_with_gps(latitude: float, longitude: float, *, tint: int = 70) -> bytes:
    image = Image.new("RGB", (80, 80), (40, 110, tint))
    for x in range(80):
        image.putpixel((x, 40), (220, 220, min(255, 80 + tint)))
    exif = _build_exif(
        make=TEST_CAMERA_MAKE,
        model="GEO-FIXTURE",
        timestamp=TEST_TIMESTAMP,
        latitude=latitude,
        longitude=longitude,
    )
    return _jpeg_bytes(image, quality=90, exif=exif)


def jpeg_without_gps(*, tint: int = 40) -> bytes:
    image = Image.new("RGB", (72, 72), (90, tint, 40))
    buf = BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def png_without_gps() -> bytes:
    return unique_png()
