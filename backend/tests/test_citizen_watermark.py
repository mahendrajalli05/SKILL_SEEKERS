from __future__ import annotations

from app.engines.citizen.watermark import render_watermark_bytes, save_watermark_copy
from app.engines.image.security import sha256_bytes
from tests.image_fixtures import unique_png


def test_watermark_does_not_alter_original_bytes() -> None:
    original = unique_png()
    digest = sha256_bytes(original)
    copy = bytearray(original)
    rendered = render_watermark_bytes(
        original,
        scheme_id="SVK-AP-000001",
        submitted_at="2026-09-10T09:00:00+00:00",
        latitude=18.1167,
        longitude=83.4,
    )
    assert rendered is not None
    assert sha256_bytes(original) == digest
    assert bytes(copy) == original
    assert sha256_bytes(rendered) != digest
    result = save_watermark_copy(
        original,
        project_id=1,
        original_digest=digest,
        scheme_id="SVK-AP-000001",
        submitted_at="2026-09-10T09:00:00+00:00",
        latitude=18.1167,
        longitude=83.4,
    )
    assert result.generated is True
    assert result.original_preserved is True
    assert result.original_sha256 == digest
    assert result.watermarked_sha256 != digest
    assert "not proof" in result.note.casefold()
