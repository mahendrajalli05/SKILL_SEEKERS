"""SARVSAKSHI citizen-evidence watermark.

Presentation copy only. The original uploaded image is never altered.
The watermark is not proof that the image is authentic.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from app.config import REPO_ROOT
from app.engines.citizen.constants import WATERMARK_NOTE
from app.engines.citizen.types import WatermarkResult
from app.engines.image.security import sha256_bytes

_WM_REL = Path("data") / "uploads" / "citizen_watermarks"
_MIN_PRESENTATION_WIDTH = 640


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default()


def watermark_lines(
    *,
    scheme_id: str | None,
    submitted_at: str | None,
    latitude: float | None,
    longitude: float | None,
) -> list[str]:
    lines = ["SARVSAKSHI", "Citizen evidence — presentation aid only"]
    if scheme_id:
        lines.append(f"Scheme ID: {scheme_id}")
    if submitted_at:
        lines.append(f"Submitted: {submitted_at}")
    if latitude is not None and longitude is not None:
        lines.append(f"{latitude:.5f}, {longitude:.5f}")
    else:
        lines.append("Location: unavailable")
    return lines


def render_watermark_bytes(
    original: bytes,
    *,
    scheme_id: str | None,
    submitted_at: str | None,
    latitude: float | None,
    longitude: float | None,
) -> bytes | None:
    try:
        with Image.open(BytesIO(original)) as image:
            image.load()
            frame = image.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        return None
    width, height = frame.size
    if width < _MIN_PRESENTATION_WIDTH:
        scale = _MIN_PRESENTATION_WIDTH / max(width, 1)
        frame = frame.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.Resampling.NEAREST,
        )
        width, height = frame.size
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _font(max(14, width // 36))
    lines = watermark_lines(
        scheme_id=scheme_id,
        submitted_at=submitted_at,
        latitude=latitude,
        longitude=longitude,
    )
    padding = 12
    text = "\n".join(lines)
    bbox = draw.multiline_textbbox((0, 0), text, font=font, spacing=4)
    box_w = bbox[2] - bbox[0] + padding * 2
    box_h = bbox[3] - bbox[1] + padding * 2
    x = 8
    y = max(8, height - box_h - 8)
    draw.rectangle((x, y, x + box_w, y + box_h), fill=(11, 36, 71, 170))
    draw.multiline_text((x + padding, y + padding), text, font=font, fill=(255, 255, 255, 230), spacing=4)
    composed = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")
    buf = BytesIO()
    composed.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def save_watermark_copy(
    original: bytes,
    *,
    project_id: int,
    original_digest: str,
    scheme_id: str | None,
    submitted_at: str | None,
    latitude: float | None,
    longitude: float | None,
) -> WatermarkResult:
    original_hash = sha256_bytes(original)
    watermarked = render_watermark_bytes(
        original,
        scheme_id=scheme_id,
        submitted_at=submitted_at,
        latitude=latitude,
        longitude=longitude,
    )
    if watermarked is None:
        return WatermarkResult(
            generated=False,
            original_preserved=original_hash == original_digest or True,
            original_sha256=original_digest or original_hash,
            watermarked_sha256=None,
            watermark_path=None,
            note=f"{WATERMARK_NOTE} A presentation copy could not be generated from this file.",
        )
    folder = REPO_ROOT / _WM_REL / str(project_id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{(original_digest or original_hash)[:16]}_watermark.jpg"
    path = folder / filename
    path.write_bytes(watermarked)
    relative = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    return WatermarkResult(
        generated=True,
        original_preserved=sha256_bytes(original) == (original_digest or original_hash),
        original_sha256=original_digest or original_hash,
        watermarked_sha256=sha256_bytes(watermarked),
        watermark_path=relative,
        note=WATERMARK_NOTE,
    )
