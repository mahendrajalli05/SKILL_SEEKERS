"""Lightweight image-transformation analysis.

Scientifically conservative. Recompression residue and repeated-region
checks are prototype indicators. Uncertain outcomes return INCONCLUSIVE.
No fabricated manipulation score is produced.
"""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.engines.forensics.constants import (
    COPY_MOVE_BLOCK_PX,
    COPY_MOVE_MIN_PAIRS,
    COPY_MOVE_MIN_SEPARATION_BLOCKS,
    ELA_UNEVEN_RATIO,
    INCONCLUSIVE,
    RECOMPRESSION_LOW_QUALITY,
)
from app.engines.image.quality import assess_quality


def _open_rgb(payload: bytes) -> Image.Image | None:
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            return image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        return None


def _jpeg_quantization(payload: bytes) -> dict[str, Any]:
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            tables = getattr(image, "quantization", None) or {}
            fmt = (image.format or "").upper()
    except (UnidentifiedImageError, OSError, ValueError, AttributeError):
        return {"format": None, "tables": {}, "estimated_quality": None}
    numeric: dict[str, list[int]] = {}
    if isinstance(tables, dict):
        for key, table in tables.items():
            try:
                numeric[str(key)] = [int(item) for item in table]
            except (TypeError, ValueError):
                continue
    estimated = None
    first = next(iter(numeric.values()), None)
    if first:
        avg = sum(first) / max(1, len(first))
        estimated = max(1, min(100, int(round(100 - (avg * 0.85)))))
    return {
        "format": fmt,
        "tables": numeric,
        "estimated_quality": estimated,
        "table_count": len(numeric),
    }


def _recompression_residue(image: Image.Image) -> dict[str, Any]:
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=90)
    try:
        with Image.open(buf) as recompressed:
            recompressed.load()
            other = recompressed.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        return {
            "available": False,
            "result": INCONCLUSIVE,
            "note": "Recompression residue could not be computed.",
        }

    width, height = image.size
    sample = image
    other_sample = other
    if width * height > 160 * 160:
        sample = image.copy()
        sample.thumbnail((160, 160), Image.Resampling.BILINEAR)
        other_sample = other.copy()
        other_sample.thumbnail((160, 160), Image.Resampling.BILINEAR)
        width, height = sample.size

    diffs: list[int] = []
    px = list(sample.getdata())
    oy = list(other_sample.getdata())
    for left, right in zip(px, oy):
        diffs.append(abs(left[0] - right[0]) + abs(left[1] - right[1]) + abs(left[2] - right[2]))
    if not diffs:
        return {"available": False, "result": INCONCLUSIVE, "note": "No pixels compared."}
    mean = sum(diffs) / len(diffs)
    variance = sum((item - mean) ** 2 for item in diffs) / len(diffs)
    peak = max(diffs)
    ratio = (peak / mean) if mean > 0.5 else 0.0
    uneven = ratio >= ELA_UNEVEN_RATIO and peak >= 40
    return {
        "available": True,
        "mean_residue": round(mean, 4),
        "variance": round(variance, 4),
        "peak": peak,
        "peak_to_mean": round(ratio, 4),
        "uneven": uneven,
        "result": INCONCLUSIVE if not uneven else INCONCLUSIVE,
        "note": (
            "Prototype JPEG recompression residue. Uneven residue is not a validated "
            "manipulation test. The result remains INCONCLUSIVE unless independent "
            "signals also support review."
        ),
    }


def _repeated_regions(image: Image.Image) -> dict[str, Any]:
    gray = image.convert("L")
    width, height = gray.size
    block = COPY_MOVE_BLOCK_PX
    if width < block * 3 or height < block * 3:
        return {
            "available": False,
            "result": INCONCLUSIVE,
            "match_pairs": 0,
            "note": "Image is too small for a reliable repeated-region check.",
        }
    seen: dict[str, tuple[int, int]] = {}
    matches: list[dict[str, int]] = []
    min_sep = COPY_MOVE_MIN_SEPARATION_BLOCKS * block
    for y in range(0, height - block + 1, block):
        for x in range(0, width - block + 1, block):
            crop = gray.crop((x, y, x + block, y + block))
            block_bytes = bytes(crop.getdata())
            try:
                digest = hashlib.md5(block_bytes, usedforsecurity=False).hexdigest()
            except TypeError:
                digest = hashlib.md5(block_bytes).hexdigest()
            prior = seen.get(digest)
            if prior is None:
                seen[digest] = (x, y)
                continue
            px, py = prior
            if abs(x - px) >= min_sep or abs(y - py) >= min_sep:
                matches.append({"x1": px, "y1": py, "x2": x, "y2": y})
    pair_count = len(matches)
    available = True
    if pair_count >= COPY_MOVE_MIN_PAIRS:
        result = "REPEATED_REGION_SIGNAL"
        note = (
            f"{pair_count} identical {block}px block pair(s) were found at separated locations. "
            "This is a possible copy-move indicator for review, not proof of manipulation."
        )
    else:
        result = INCONCLUSIVE if pair_count else NO_MATCH
        note = (
            "No separated identical blocks were found at the prototype grid size. "
            "Absence of a match is not proof that the image is unedited."
            if pair_count == 0
            else "Repeated blocks were below the review threshold."
        )
    return {
        "available": available,
        "result": result,
        "match_pairs": pair_count,
        "matches": matches[:8],
        "block_px": block,
        "note": note,
    }


NO_MATCH = "NO_REPEATED_REGION"


def analyze_transformation(
    payload: bytes,
    *,
    metadata_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quality = assess_quality(payload)
    image = _open_rgb(payload)
    if image is None:
        return {
            "readable": False,
            "result": INCONCLUSIVE,
            "recompression": {"available": False, "result": INCONCLUSIVE},
            "resampling": {"available": False, "result": INCONCLUSIVE},
            "repeated_regions": {"available": False, "result": INCONCLUSIVE},
            "note": "Transformation analysis is INCONCLUSIVE because the file could not be decoded.",
        }

    jpeg = _jpeg_quantization(payload)
    estimated_quality = jpeg.get("estimated_quality")
    low_quality = (
        jpeg.get("format") == "JPEG"
        and estimated_quality is not None
        and int(estimated_quality) <= RECOMPRESSION_LOW_QUALITY
    )
    residue = _recompression_residue(image) if jpeg.get("format") == "JPEG" else {
        "available": False,
        "result": INCONCLUSIVE,
        "note": "Recompression residue is only computed for JPEG files.",
    }

    meta = metadata_details or {}
    actual_w = extra_w = image.size[0]
    actual_h = extra_h = image.size[1]
    if meta.get("actual_width"):
        actual_w = int(meta["actual_width"])
    if meta.get("actual_height"):
        actual_h = int(meta["actual_height"])
    pixel_x = meta.get("pixel_x")
    pixel_y = meta.get("pixel_y")
    dimension_mismatch = False
    if pixel_x and pixel_y and (int(pixel_x) != actual_w or int(pixel_y) != actual_h):
        dimension_mismatch = True
        resampling_result = "DIMENSION_MISMATCH"
        resampling_note = (
            f"EXIF pixel dimensions ({pixel_x}x{pixel_y}) differ from decoded size "
            f"({actual_w}x{actual_h}). This may indicate resampling or metadata edit. "
            "It is not proof of manipulation."
        )
    else:
        resampling_result = INCONCLUSIVE
        resampling_note = (
            "No EXIF-vs-pixel dimension mismatch was identified. "
            "Resampling cannot be confirmed from this file alone."
        )

    repeated = _repeated_regions(image)
    notes = [
        residue.get("note") or "",
        repeated.get("note") or "",
        resampling_note,
    ]
    if low_quality:
        notes.append(
            f"JPEG quantization suggests a lower save quality (about {estimated_quality}). "
            "Recompression is common and is not treated as proof of manipulation."
        )

    return {
        "readable": True,
        "result": INCONCLUSIVE,
        "width": actual_w,
        "height": actual_h,
        "quality": quality,
        "recompression": {
            **jpeg,
            **residue,
            "low_quality_jpeg": low_quality,
        },
        "resampling": {
            "available": pixel_x is not None and pixel_y is not None,
            "result": resampling_result,
            "dimension_mismatch": dimension_mismatch,
            "exif_width": pixel_x,
            "exif_height": pixel_y,
            "actual_width": actual_w,
            "actual_height": actual_h,
            "note": resampling_note,
        },
        "repeated_regions": repeated,
        "notes": [item for item in notes if item],
    }
