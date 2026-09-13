"""TEST/SYNTHETIC image bytes. Not official government photographs."""

from __future__ import annotations

import struct
from io import BytesIO

from PIL import Image

from app.engines.image.constants import TEST_WATERMARK

TEST_LATITUDE = 17.416667
TEST_LONGITUDE = 78.483333
TEST_TIMESTAMP = "2024:03:20 08:15:00"
TEST_CAMERA_MAKE = "TEST-CAMERA"
TEST_CAMERA_MODEL = "SYNTHETIC-FIXTURE"


def _png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _jpeg_bytes(image: Image.Image, *, quality: int = 95, exif: bytes | None = None) -> bytes:
    buf = BytesIO()
    converted = image.convert("RGB")
    if exif:
        converted.save(buf, format="JPEG", quality=quality, exif=exif)
    else:
        converted.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def unique_png() -> bytes:
    image = Image.new("RGB", (96, 96), (180, 32, 32))
    for x in range(96):
        image.putpixel((x, 20), (240, 200, 40))
        image.putpixel((40, x), (40, 40, 200))
    return _png_bytes(image)


def near_duplicate_jpeg() -> bytes:
    image = Image.new("RGB", (96, 96), (176, 36, 30))
    for x in range(96):
        image.putpixel((x, 20), (235, 198, 36))
        image.putpixel((40, x), (44, 42, 190))
    image.putpixel((90, 90), (255, 255, 255))
    return _jpeg_bytes(image, quality=55)


def different_png() -> bytes:
    image = Image.new("RGB", (96, 96), (20, 90, 160))
    for y in range(96):
        for x in range(96):
            if (x // 12 + y // 12) % 2 == 0:
                image.putpixel((x, y), (20, 140, 60))
    return _png_bytes(image)


def tiny_png() -> bytes:
    return _png_bytes(Image.new("RGB", (16, 16), (90, 90, 90)))


def no_metadata_png() -> bytes:
    return unique_png()


def _ascii_field(text: str) -> bytes:
    encoded = text.encode("ascii", errors="replace") + b"\x00"
    return encoded


def _dms(value: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    sign = 1 if value >= 0 else -1
    value = abs(value)
    degrees = int(value)
    minutes_full = (value - degrees) * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    return ((degrees, 1), (minutes, 1), (int(round(seconds * 10000)), 10000)), sign


def jpeg_with_exif_gps() -> bytes:
    """JPEG with reported EXIF GPS/timestamp. TEST fixture, not a government photo."""
    image = Image.new("RGB", (80, 80), (40, 110, 70))
    for x in range(80):
        image.putpixel((x, 40), (220, 220, 80))
    exif = _build_exif(
        make=TEST_CAMERA_MAKE,
        model=TEST_CAMERA_MODEL,
        timestamp=TEST_TIMESTAMP,
        latitude=TEST_LATITUDE,
        longitude=TEST_LONGITUDE,
    )
    return _jpeg_bytes(image, quality=90, exif=exif)


def corrupt_jpeg() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF" + b"\x00" * 8 + b"\xff\x00not-an-image"


def hybrid_png() -> bytes:
    image = Image.new("RGB", (64, 64), (120, 60, 160))
    image.putpixel((8, 8), (255, 255, 0))
    return _png_bytes(image)


def webp_bytes() -> bytes | None:
    image = Image.new("RGB", (32, 32), (10, 20, 30))
    buf = BytesIO()
    try:
        image.save(buf, format="WEBP")
    except OSError:
        return None
    return buf.getvalue()


def _ifd(entries: list[bytes], next_ifd: int = 0) -> bytes:
    body = struct.pack("<H", len(entries)) + b"".join(entries) + struct.pack("<I", next_ifd)
    return body


def _entry(tag: int, typ: int, count: int, value: int | bytes) -> bytes:
    if isinstance(value, bytes):
        packed = value.ljust(4, b"\x00")[:4]
        return struct.pack("<HHI", tag, typ, count) + packed
    return struct.pack("<HHII", tag, typ, count, value)


def _build_exif(*, make: str, model: str, timestamp: str, latitude: float, longitude: float) -> bytes:
    make_b = _ascii_field(make)
    model_b = _ascii_field(model)
    dt = (timestamp + "\x00").encode("ascii")[:20].ljust(20, b"\x00")
    lat_dms, lat_sign = _dms(latitude)
    lon_dms, lon_sign = _dms(longitude)
    lat_ref = b"N\x00" if lat_sign >= 0 else b"S\x00"
    lon_ref = b"E\x00" if lon_sign >= 0 else b"W\x00"

    # Layout after TIFF header (offset 0):
    # 0: endian + magic + ifd0_offset
    # 8: IFD0
    header = b"II" + struct.pack("<H", 42)
    ifd0_offset = 8
    ifd0_count = 5
    ifd0_size = 2 + ifd0_count * 12 + 4
    data_cursor = ifd0_offset + ifd0_size

    make_off = data_cursor
    data_cursor += len(make_b)
    model_off = data_cursor
    data_cursor += len(model_b)
    dt_off = data_cursor
    data_cursor += 20
    exif_ifd_off = data_cursor
    exif_count = 1
    exif_ifd_size = 2 + exif_count * 12 + 4
    data_cursor += exif_ifd_size
    dto_off = data_cursor
    data_cursor += 20
    gps_ifd_off = data_cursor
    gps_count = 4
    gps_ifd_size = 2 + gps_count * 12 + 4
    data_cursor += gps_ifd_size
    lat_off = data_cursor
    data_cursor += 24
    lon_off = data_cursor
    data_cursor += 24

    type_ascii = 2
    type_long = 4
    type_rational = 5
    ifd0 = _ifd(
        [
            _entry(0x010F, type_ascii, len(make_b), make_off),
            _entry(0x0110, type_ascii, len(model_b), model_off),
            _entry(0x0132, type_ascii, 20, dt_off),
            _entry(0x8769, type_long, 1, exif_ifd_off),
            _entry(0x8825, type_long, 1, gps_ifd_off),
        ]
    )
    exif_ifd = _ifd([_entry(0x9003, type_ascii, 20, dto_off)])
    gps_ifd = _ifd(
        [
            _entry(1, type_ascii, 2, lat_ref),
            _entry(2, type_rational, 3, lat_off),
            _entry(3, type_ascii, 2, lon_ref),
            _entry(4, type_rational, 3, lon_off),
        ]
    )

    def rationals(parts: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]) -> bytes:
        return b"".join(struct.pack("<II", num, den) for num, den in parts)

    payload = (
        header
        + struct.pack("<I", ifd0_offset)
        + ifd0
        + make_b
        + model_b
        + dt
        + exif_ifd
        + dt
        + gps_ifd
        + rationals(lat_dms)
        + rationals(lon_dms)
    )
    return b"Exif\x00\x00" + payload


__all__ = [
    "TEST_CAMERA_MAKE",
    "TEST_CAMERA_MODEL",
    "TEST_LATITUDE",
    "TEST_LONGITUDE",
    "TEST_TIMESTAMP",
    "TEST_WATERMARK",
    "corrupt_jpeg",
    "different_png",
    "hybrid_png",
    "jpeg_with_exif_gps",
    "near_duplicate_jpeg",
    "no_metadata_png",
    "tiny_png",
    "unique_png",
    "webp_bytes",
]
