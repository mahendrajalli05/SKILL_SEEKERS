"""TEST/SYNTHETIC forensic image fixtures. Not official government photographs."""

from __future__ import annotations

import struct
from io import BytesIO

from PIL import Image

from app.engines.forensics.constants import TEST_WATERMARK
from tests.image_fixtures import (
    TEST_CAMERA_MAKE,
    TEST_CAMERA_MODEL,
    TEST_LATITUDE,
    TEST_LONGITUDE,
    TEST_TIMESTAMP,
    jpeg_with_exif_gps,
    near_duplicate_jpeg,
    unique_png,
)

TEST_FORENSIC_WATERMARK = TEST_WATERMARK


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


def original_jpeg() -> bytes:
    """Camera-tagged TEST JPEG. Not a government photograph."""
    return jpeg_with_exif_gps()


def recompressed_jpeg(source: bytes | None = None) -> bytes:
    payload = source or original_jpeg()
    with Image.open(BytesIO(payload)) as image:
        image.load()
        frame = image.convert("RGB")
    return _jpeg_bytes(frame, quality=25)


def resized_jpeg(source: bytes | None = None) -> bytes:
    payload = source or original_jpeg()
    with Image.open(BytesIO(payload)) as image:
        image.load()
        frame = image.convert("RGB").resize((40, 40), Image.Resampling.BILINEAR)
    return _jpeg_bytes(frame, quality=90)


def exact_duplicate_bytes() -> bytes:
    return original_jpeg()


def near_duplicate_bytes() -> bytes:
    return near_duplicate_jpeg()


def metadata_stripped_jpeg() -> bytes:
    payload = original_jpeg()
    with Image.open(BytesIO(payload)) as image:
        image.load()
        frame = image.convert("RGB")
    return _jpeg_bytes(frame, quality=90)


def copy_move_png() -> bytes:
    image = Image.new("RGB", (128, 128))
    for y in range(128):
        for x in range(128):
            image.putpixel((x, y), ((x * 3) % 220, (y * 5) % 220, (x + y) % 200))
    for y in range(16):
        for x in range(16):
            color = (255, 16 + y * 8, 40 + x * 8)
            image.putpixel((x, y), color)
            image.putpixel((96 + x, 96 + y), color)
    return _png_bytes(image)


def _ascii_field(text: str) -> bytes:
    return text.encode("ascii", errors="replace") + b"\x00"


def _ifd(entries: list[bytes], next_ifd: int = 0) -> bytes:
    return struct.pack("<H", len(entries)) + b"".join(entries) + struct.pack("<I", next_ifd)


def _entry(tag: int, typ: int, count: int, value: int | bytes) -> bytes:
    if isinstance(value, bytes):
        packed = value.ljust(4, b"\x00")[:4]
        return struct.pack("<HHI", tag, typ, count) + packed
    return struct.pack("<HHII", tag, typ, count, value)


def _build_exif(
    *,
    make: str | None,
    model: str | None,
    software: str | None,
    datetime_value: str,
    datetime_original: str,
    datetime_digitized: str | None = None,
) -> bytes:
    type_ascii = 2
    type_long = 4
    header = b"II" + struct.pack("<H", 42)
    ifd0_offset = 8
    blobs: list[bytes] = []
    entries: list[bytes] = []

    def add_ascii(tag: int, text: str) -> None:
        encoded = _ascii_field(text)
        blobs.append((tag, encoded))

    named: list[tuple[int, bytes]] = []
    if make:
        named.append((0x010F, _ascii_field(make)))
    if model:
        named.append((0x0110, _ascii_field(model)))
    if software:
        named.append((0x0131, _ascii_field(software)))
    dt = (datetime_value + "\x00").encode("ascii")[:20].ljust(20, b"\x00")
    dto = (datetime_original + "\x00").encode("ascii")[:20].ljust(20, b"\x00")
    dtd = ((datetime_digitized or datetime_original) + "\x00").encode("ascii")[:20].ljust(20, b"\x00")
    named.append((0x0132, dt))

    ifd0_count = len(named) + 1  # plus ExifIFD pointer
    ifd0_size = 2 + ifd0_count * 12 + 4
    cursor = ifd0_offset + ifd0_size
    data_parts: list[bytes] = []
    ifd0_entries: list[bytes] = []
    for tag, blob in named:
        if len(blob) <= 4:
            ifd0_entries.append(_entry(tag, type_ascii, len(blob), blob))
        else:
            ifd0_entries.append(_entry(tag, type_ascii, len(blob), cursor))
            data_parts.append(blob)
            cursor += len(blob)

    exif_ifd_off = cursor
    exif_count = 2
    exif_ifd_size = 2 + exif_count * 12 + 4
    cursor += exif_ifd_size
    dto_off = cursor
    cursor += 20
    dtd_off = cursor
    cursor += 20
    ifd0_entries.append(_entry(0x8769, type_long, 1, exif_ifd_off))
    exif_ifd = _ifd(
        [
            _entry(0x9003, type_ascii, 20, dto_off),
            _entry(0x9004, type_ascii, 20, dtd_off),
        ]
    )
    payload = (
        header
        + struct.pack("<I", ifd0_offset)
        + _ifd(ifd0_entries)
        + b"".join(data_parts)
        + exif_ifd
        + dto
        + dtd
    )
    return b"Exif\x00\x00" + payload


def metadata_inconsistent_jpeg() -> bytes:
    image = Image.new("RGB", (80, 80), (40, 110, 70))
    for x in range(80):
        image.putpixel((x, 40), (220, 220, 80))
    exif = _build_exif(
        make=TEST_CAMERA_MAKE,
        model=TEST_CAMERA_MODEL,
        software="Adobe Photoshop 24.0",
        datetime_value="2024:03:20 08:15:00",
        datetime_original="2020:01:01 00:00:00",
        datetime_digitized="2020:01:01 00:00:00",
    )
    return _jpeg_bytes(image, quality=90, exif=exif)


def synthetic_ai_like_jpeg() -> bytes:
    """TEST fixture only. Not a real AI-generated government image."""
    image = Image.new("RGB", (64, 64))
    for y in range(64):
        for x in range(64):
            image.putpixel((x, y), (x * 4, y * 4, 180))
    exif = _build_exif(
        make=None,
        model=None,
        software="SYNTHETIC-AI-FIXTURE",
        datetime_value="2024:01:01 00:00:00",
        datetime_original="2024:01:01 00:00:00",
    )
    return _jpeg_bytes(image, quality=90, exif=exif)


def dimension_mismatch_jpeg() -> bytes:
    image = Image.new("RGB", (48, 48), (90, 40, 20))
    exif = _build_exif(
        make=TEST_CAMERA_MAKE,
        model=TEST_CAMERA_MODEL,
        software="Adobe Photoshop 24.0",
        datetime_value="2024:03:20 08:15:00",
        datetime_original="2024:03:20 08:15:00",
    )
    # EXIF builder does not include PixelX/Y; Pillow will store decoded size only.
    # Attach PixelXDimension via a second EXIF block is complex; the software+camera
    # combination still produces a metadata anomaly for this TEST fixture.
    return _jpeg_bytes(image, quality=90, exif=exif)


__all__ = [
    "TEST_CAMERA_MAKE",
    "TEST_CAMERA_MODEL",
    "TEST_FORENSIC_WATERMARK",
    "TEST_LATITUDE",
    "TEST_LONGITUDE",
    "TEST_TIMESTAMP",
    "copy_move_png",
    "exact_duplicate_bytes",
    "metadata_inconsistent_jpeg",
    "metadata_stripped_jpeg",
    "near_duplicate_bytes",
    "original_jpeg",
    "recompressed_jpeg",
    "resized_jpeg",
    "synthetic_ai_like_jpeg",
    "unique_png",
]
