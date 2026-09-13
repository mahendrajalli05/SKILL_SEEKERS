from __future__ import annotations

from io import BytesIO

from PIL import Image

from app.engines.image.hashes import (
    average_hash,
    compute_hashes,
    difference_hash,
    hamming_distance,
    is_near_duplicate,
    perceptual_hash,
)
from tests.image_fixtures import different_png, near_duplicate_jpeg, unique_png


def _open(payload: bytes) -> Image.Image:
    return Image.open(BytesIO(payload))


def test_hashes_are_deterministic() -> None:
    image = _open(unique_png())
    first = compute_hashes(image)
    second = compute_hashes(_open(unique_png()))
    assert first == second
    assert len(first["ahash"]) >= 16
    assert first["ahash"] == average_hash(_open(unique_png()))
    assert first["dhash"] == difference_hash(_open(unique_png()))
    assert first["phash"] == perceptual_hash(_open(unique_png()))


def test_exact_same_pixels_have_zero_distance() -> None:
    left = compute_hashes(_open(unique_png()))
    right = compute_hashes(_open(unique_png()))
    assert hamming_distance(left["phash"], right["phash"]) == 0
    assert hamming_distance(left["dhash"], right["dhash"]) == 0


def test_near_duplicate_is_within_threshold() -> None:
    unique = compute_hashes(_open(unique_png()))
    near = compute_hashes(_open(near_duplicate_jpeg()))
    distances = [
        hamming_distance(unique["dhash"], near["dhash"]),
        hamming_distance(unique["phash"], near["phash"]),
        hamming_distance(unique["ahash"], near["ahash"]),
    ]
    assert any(is_near_duplicate(item) for item in distances)


def test_different_image_is_not_near_duplicate() -> None:
    unique = compute_hashes(_open(unique_png()))
    other = compute_hashes(_open(different_png()))
    distances = [
        hamming_distance(unique["dhash"], other["dhash"]),
        hamming_distance(unique["phash"], other["phash"]),
        hamming_distance(unique["ahash"], other["ahash"]),
    ]
    assert all(item is not None and not is_near_duplicate(item) for item in distances)
