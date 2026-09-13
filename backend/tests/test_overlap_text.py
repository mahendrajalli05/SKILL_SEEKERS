from __future__ import annotations

from app.engines.overlap.text import (
    combine_place_text,
    constituency_fields,
    embedding_text,
    normalize_work_text,
    overlap_tokens,
    preserve_source_text,
    rare_block_tokens,
)


def test_preserves_original_source_text() -> None:
    raw = "NA - Construction of water tanks"
    assert preserve_source_text(raw) == raw
    assert preserve_source_text(None) == ""


def test_embedding_text_strips_prefix_and_casefolds() -> None:
    assert embedding_text("NA - Construction of water tanks") == "construction of water tanks"
    assert embedding_text("WS/MP023/2023-2024/1 - Construction of water tanks") == (
        "construction of water tanks"
    )


def test_normalize_does_not_invent_wording() -> None:
    assert normalize_work_text("  Construction of  roads ") == "Construction of roads"
    assert "sector" not in embedding_text("Construction of roads")


def test_empty_description_is_empty_embedding_text() -> None:
    assert embedding_text("") == ""
    assert embedding_text(None) == ""
    assert overlap_tokens("") == frozenset()


def test_rare_tokens_drop_generic_construction_filler() -> None:
    rare = rare_block_tokens("NA - Construction of water tanks")
    assert "water" in rare
    assert "tank" in rare
    assert "construction" not in rare


def test_place_text_joins_observed_fields_only() -> None:
    text = combine_place_text(city="", ward="", block="Guntur", village="Pedakakani")
    assert text == "Guntur | Pedakakani"
    assert combine_place_text(city="", ward="", block="", village="") == ""


def test_rajya_sabha_is_not_geographic() -> None:
    value, usable, kind, reason = constituency_fields("Sitting Rajya Sabha")
    assert usable is False
    assert kind == "non_geographic"
    assert reason is not None
    assert value == "Sitting Rajya Sabha"
