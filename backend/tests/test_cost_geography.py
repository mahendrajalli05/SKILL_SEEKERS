from __future__ import annotations

from app.engines.cost.geography import ConstituencyKind, classify_constituency


def test_named_parliamentary_constituency_is_geographic() -> None:
    for value in ("KURNOOL", "ELURU", "ARAKU(ST)", "AMALAPURAM(SC)", "GURGAON"):
        result = classify_constituency(value)
        assert result.usable_as_geography is True
        assert result.kind == ConstituencyKind.GEOGRAPHIC
        assert "official" in result.reason


def test_rajya_sabha_labels_are_not_geographic() -> None:
    sitting = classify_constituency("Sitting Rajya Sabha")
    nominated = classify_constituency("Nominated Rajya Sabha")
    for result in (sitting, nominated):
        assert result.usable_as_geography is False
        assert result.kind == ConstituencyKind.NON_GEOGRAPHIC
        assert "chamber" in result.reason.casefold() or "house" in result.reason.casefold()


def test_blank_constituency_is_unusable() -> None:
    for value in ("", "   ", None):
        result = classify_constituency(value)
        assert result.usable_as_geography is False
        assert result.kind.value in {"unusable", "non_geographic"}


def test_classification_is_deterministic() -> None:
    first = classify_constituency("Sitting Rajya Sabha")
    second = classify_constituency("Sitting Rajya Sabha")
    assert first == second


def test_does_not_claim_official_constituency_validation() -> None:
    result = classify_constituency("KURNOOL")
    assert "not validated against an official constituency list" in result.reason
    sitting = classify_constituency("Sitting Rajya Sabha")
    assert sitting.usable_as_geography is False
