from __future__ import annotations

from app.geo.constituency import (
    ConstituencyKind,
    classify_constituency,
    geographic_constituency_reason,
    is_geographic_constituency,
)


def test_geographic_helper_accepts_named_constituencies() -> None:
    for value in ("KURNOOL", "ELURU", "ARAKU(ST)", "VISAKHAPATNAM"):
        assert is_geographic_constituency(value) is True
        assert classify_constituency(value).kind == ConstituencyKind.GEOGRAPHIC
        assert "official constituency list" in geographic_constituency_reason(value)


def test_rajya_sabha_labels_are_excluded_from_geographic_filters() -> None:
    for value in ("Sitting Rajya Sabha", "Nominated Rajya Sabha"):
        result = classify_constituency(value)
        assert is_geographic_constituency(value) is False
        assert result.kind == ConstituencyKind.NON_GEOGRAPHIC
        assert result.value == value
        assert "not a geographic" in result.reason.casefold() or "chamber" in result.reason.casefold()


def test_blank_values_are_not_fabricated_into_constituencies() -> None:
    for value in ("", "  ", None):
        result = classify_constituency(value)
        assert is_geographic_constituency(value) is False
        assert result.usable_as_geography is False
        assert result.value == (value or "").strip() or result.value == ""
