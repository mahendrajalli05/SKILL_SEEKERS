from __future__ import annotations

from app.engines.overlap.embeddings import HashedTokenEmbedder
from app.engines.overlap.similarity import cosine_similarity


def test_hashed_embedder_is_deterministic() -> None:
    text = "construction of water tanks"
    first = HashedTokenEmbedder().embed([text])[0]
    second = HashedTokenEmbedder().embed([text])[0]
    assert first is not None
    assert first == second
    assert cosine_similarity(first, second) == 1.0


def test_identical_texts_have_cosine_one() -> None:
    embedder = HashedTokenEmbedder()
    left, right = embedder.embed(["NA - Construction of water tanks"] * 2)
    assert cosine_similarity(left, right) == 1.0


def test_empty_text_returns_none_vector() -> None:
    embedder = HashedTokenEmbedder()
    assert embedder.embed([""]) == [None]
    assert cosine_similarity(None, embedder.embed(["tanks"])[0]) is None


def test_near_duplicate_titles_are_more_similar_than_unrelated() -> None:
    embedder = HashedTokenEmbedder()
    tanks, tank, roads = embedder.embed(
        [
            "Construction of water tanks",
            "Construction of water tank",
            "Construction of roads, approach roads, link roads and pathways",
        ]
    )
    near = cosine_similarity(tanks, tank)
    far = cosine_similarity(tanks, roads)
    assert near is not None
    assert far is not None
    assert near > 0.85
    assert near > far
    assert far < 0.55
