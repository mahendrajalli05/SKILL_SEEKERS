from __future__ import annotations

from app.engines.image.quality import assess_quality
from tests.image_fixtures import corrupt_jpeg, tiny_png, unique_png


def test_readable_image_reports_dimensions() -> None:
    result = assess_quality(unique_png())
    assert result["readable"] is True
    assert result["width"] == 96
    assert result["height"] == 96
    assert "not treated as wrongdoing" in result["note"].casefold() or "not a legal finding" in result["note"].casefold()
    assert "fraud" not in result["note"].casefold()


def test_low_resolution_warning() -> None:
    result = assess_quality(tiny_png())
    assert result["readable"] is True
    assert result["warnings"]
    assert any("resolution" in item.casefold() for item in result["warnings"])
    blob = " ".join(result["warnings"]).casefold()
    assert "fraud" not in blob


def test_corrupt_image_is_unreadable() -> None:
    result = assess_quality(corrupt_jpeg())
    assert result["readable"] is False
    assert result["warnings"]
    assert "fraud" not in " ".join(result["warnings"]).casefold()
