"""SYNTHETIC JPEG bytes for Demo Evidence Fixtures V1.

Not official government photographs. Reported EXIF GPS/timestamp are labelled
fixture metadata from the generated file.
"""

from __future__ import annotations

import struct
from io import BytesIO

from PIL import Image

FIXTURE_CAMERA_MAKE = "DEMO-FIXTURE"
FIXTURE_CAMERA_MODEL = "SYNTHETIC-CONTROLLED"
FIXTURE_TIMESTAMP = "2024:03:20 08:15:00"

# Labelled SYNTHETIC reported EXIF for GHOST: Vizianagaram-area point.
# Contrasts with existing HYBRID enrichment GPS 10.05, 68.4. Not official GPS.
GHOST_REPORTED_IMAGE_LAT = 18.112000
GHOST_REPORTED_IMAGE_LON = 83.395000


def _jpeg_bytes(image: Image.Image, *, quality: int = 90, exif: bytes | None = None) -> bytes:
    buf = BytesIO()
    converted = image.convert("RGB")
    if exif:
        converted.save(buf, format="JPEG", quality=quality, exif=exif)
    else:
        converted.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def _ascii_field(text: str) -> bytes:
    return text.encode("ascii", errors="replace") + b"\x00"


def _dms(value: float) -> tuple[tuple[tuple[int, int], tuple[int, int], tuple[int, int]], int]:
    sign = 1 if value >= 0 else -1
    value = abs(value)
    degrees = int(value)
    minutes_full = (value - degrees) * 60
    minutes = int(minutes_full)
    seconds = (minutes_full - minutes) * 60
    return ((degrees, 1), (minutes, 1), (int(round(seconds * 10000)), 10000)), sign


def _ifd(entries: list[bytes], next_ifd: int = 0) -> bytes:
    return struct.pack("<H", len(entries)) + b"".join(entries) + struct.pack("<I", next_ifd)


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


def jpeg_with_exif_gps(
    *,
    latitude: float,
    longitude: float,
    color: tuple[int, int, int],
    pattern: str,
) -> bytes:
    """Build a distinct SYNTHETIC JPEG so cases do not share a reuse hash."""
    image = Image.new("RGB", (96, 96), color)
    accent = ((color[0] + 80) % 256, (color[1] + 40) % 256, (color[2] + 120) % 256)
    if pattern == "ghost":
        for x in range(96):
            image.putpixel((x, 24), accent)
            image.putpixel((16, x), (240, 200, 40))
    elif pattern == "clean":
        for y in range(0, 96, 8):
            for x in range(96):
                image.putpixel((x, y), accent)
    elif pattern == "citizen":
        for x in range(96):
            image.putpixel((x, x), accent)
            image.putpixel((95 - x, x), (40, 40, 200))
    else:
        for x in range(0, 96, 6):
            image.putpixel((x, 48), accent)
    exif = _build_exif(
        make=FIXTURE_CAMERA_MAKE,
        model=FIXTURE_CAMERA_MODEL,
        timestamp=FIXTURE_TIMESTAMP,
        latitude=latitude,
        longitude=longitude,
    )
    return _jpeg_bytes(image, quality=90, exif=exif)
