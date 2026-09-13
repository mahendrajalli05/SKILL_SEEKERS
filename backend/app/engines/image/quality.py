"""Basic technical image-quality checks. Poor quality is not a legal finding."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError

from app.engines.image.constants import (
    BLUR_VARIANCE_THRESHOLD,
    LOW_RESOLUTION_MIN_PX,
    LOW_RESOLUTION_PIXELS,
)


def _laplacian_variance(image: Image.Image) -> float | None:
    gray = image.convert("L")
    width, height = gray.size
    if width < 3 or height < 3:
        return 0.0
    sample = gray
    if width > 256 or height > 256:
        sample = gray.copy()
        sample.thumbnail((256, 256), Image.Resampling.BILINEAR)
        width, height = sample.size
    pixels = list(sample.getdata())

    def at(x: int, y: int) -> int:
        return pixels[y * width + x]

    values: list[int] = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            values.append(
                at(x, y - 1) + at(x, y + 1) + at(x - 1, y) + at(x + 1, y) - (4 * at(x, y))
            )
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((item - mean) ** 2 for item in values) / len(values)


def assess_quality(payload: bytes) -> dict[str, Any]:
    warnings: list[str] = []
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            width, height = image.size
            mode = image.mode
            variance = _laplacian_variance(image)
    except (UnidentifiedImageError, OSError, ValueError):
        return {
            "readable": False,
            "width": None,
            "height": None,
            "pixel_count": None,
            "blur_warning": False,
            "laplacian_variance": None,
            "warnings": ["File could not be decoded as an image."],
            "note": "An unreadable file is a technical quality issue, not a legal finding.",
        }

    pixel_count = width * height
    if width < LOW_RESOLUTION_MIN_PX or height < LOW_RESOLUTION_MIN_PX or pixel_count < LOW_RESOLUTION_PIXELS:
        warnings.append(
            "Resolution is below a useful size for site evidence. This is a technical warning, not a legal finding."
        )
    blur_warning = variance is not None and variance < BLUR_VARIANCE_THRESHOLD
    if blur_warning:
        warnings.append(
            "Image sharpness is low (possible blur or flat colour). This is a technical warning, not a legal finding."
        )
    return {
        "readable": True,
        "width": width,
        "height": height,
        "pixel_count": pixel_count,
        "mode": mode,
        "blur_warning": blur_warning,
        "laplacian_variance": None if variance is None else round(variance, 4),
        "warnings": warnings,
        "note": "Quality checks are technical only. Poor image quality is not treated as wrongdoing.",
    }
