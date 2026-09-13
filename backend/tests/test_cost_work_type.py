from __future__ import annotations

from app.engines.cost.work_type import (
    derive_work_type,
    strip_observed_work_prefixes,
    work_type_representation,
    work_type_similarity,
    work_type_tokens,
)


def test_strips_na_prefix() -> None:
    assert (
        strip_observed_work_prefixes("NA - Construction of water tanks")
        == "Construction of water tanks"
    )


def test_strips_ws_work_code_prefix() -> None:
    raw = "WS/MP521/2023-2024/2223 - Improvement of electricity distribution infrastructure"
    assert (
        strip_observed_work_prefixes(raw)
        == "Improvement of electricity distribution infrastructure"
    )


def test_same_title_different_prefixes_share_work_type() -> None:
    na = derive_work_type("NA - Construction of community centers and community halls")
    ws = derive_work_type(
        "WS/MP023/2023-2024/16604 - Construction of community centers and community halls"
    )
    assert na == ws
    assert na == "construction of community centers and community halls"


def test_empty_description_is_empty_work_type() -> None:
    assert derive_work_type("") == ""
    assert derive_work_type(None) == ""


def test_representation_uses_observed_category_not_invented_codes() -> None:
    text = work_type_representation(
        category="Repair and Renovation",
        work_description="NA - Construction of New Building",
    )
    assert text == "Repair and Renovation | construction of new building"
    assert "sector" not in text.casefold()


def test_does_not_invent_government_category_from_roads_title() -> None:
    key = derive_work_type(
        "NA - Construction of roads, approach roads, link roads and pathways"
    )
    other = derive_work_type(
        "NA - Construction of roads, link roads, pathways or any other road with or without drainage system"
    )
    assert key != other


def test_similar_road_titles_have_high_token_similarity() -> None:
    left = "NA - Construction of roads, approach roads, link roads and pathways"
    right = (
        "NA - Construction of roads, link roads, pathways or any other road "
        "with or without drainage system"
    )
    score = work_type_similarity(left, right)
    assert score >= 0.5
    assert work_type_similarity(left, left) == 1.0
    assert work_type_similarity(left, "NA - Construction of water tanks") < 0.5


def test_work_type_tokens_are_deterministic() -> None:
    title = "NA - Construction of water tanks"
    assert work_type_tokens(title) == work_type_tokens(title)
    assert "construction" in work_type_tokens(title)
    assert "water" in work_type_tokens(title)
    assert "of" not in work_type_tokens(title)

