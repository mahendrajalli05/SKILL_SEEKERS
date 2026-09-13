"""Deterministic aHash / dHash / pHash. Not a legal similarity finding."""

from __future__ import annotations

import math
from typing import Any

from PIL import Image

from app.engines.image.constants import NEAR_DUPLICATE_MAX_DISTANCE


def _to_grayscale_matrix(image: Image.Image, size: tuple[int, int]) -> list[list[int]]:
    gray = image.convert("L").resize(size, Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    width, height = size
    return [pixels[row * width : (row + 1) * width] for row in range(height)]


def _bits_to_hex(bits: list[int]) -> str:
    value = 0
    for bit in bits:
        value = (value << 1) | (1 if bit else 0)
    width = max(16, (len(bits) + 3) // 4)
    return f"{value:0{width}x}"


def average_hash(image: Image.Image) -> str:
    matrix = _to_grayscale_matrix(image, (8, 8))
    mean = sum(sum(row) for row in matrix) / 64.0
    bits = [1 if pixel >= mean else 0 for row in matrix for pixel in row]
    return _bits_to_hex(bits)


def difference_hash(image: Image.Image) -> str:
    matrix = _to_grayscale_matrix(image, (9, 8))
    bits: list[int] = []
    for row in matrix:
        for col in range(8):
            bits.append(1 if row[col] < row[col + 1] else 0)
    return _bits_to_hex(bits)


def _dct_2d(block: list[list[float]]) -> list[list[float]]:
    size = len(block)
    scale0 = math.sqrt(1.0 / size)
    scale = math.sqrt(2.0 / size)
    out = [[0.0] * size for _ in range(size)]
    for u in range(size):
        cu = scale0 if u == 0 else scale
        for v in range(size):
            cv = scale0 if v == 0 else scale
            total = 0.0
            for x in range(size):
                for y in range(size):
                    total += (
                        block[x][y]
                        * math.cos(((2 * x + 1) * u * math.pi) / (2 * size))
                        * math.cos(((2 * y + 1) * v * math.pi) / (2 * size))
                    )
            out[u][v] = cu * cv * total
    return out


def perceptual_hash(image: Image.Image) -> str:
    matrix = _to_grayscale_matrix(image, (32, 32))
    block = [[float(pixel) for pixel in row] for row in matrix]
    dct = _dct_2d(block)
    low = [dct[u][v] for u in range(8) for v in range(8)]
    # Skip DC coefficient so uniform brightness shifts do not dominate.
    ac = low[1:]
    median = sorted(ac)[len(ac) // 2]
    bits = [1 if value >= median else 0 for value in low]
    return _bits_to_hex(bits)


def hamming_distance(left: str | None, right: str | None) -> int | None:
    if not left or not right:
        return None
    cleaned_left = left.strip().lower()
    cleaned_right = right.strip().lower()
    if len(cleaned_left) != len(cleaned_right):
        return None
    try:
        return bin(int(cleaned_left, 16) ^ int(cleaned_right, 16)).count("1")
    except ValueError:
        return None


def similarity_from_distance(distance: int, bits: int = 64) -> float:
    return round(max(0.0, min(1.0, 1.0 - (distance / bits))), 4)


def compute_hashes(image: Image.Image) -> dict[str, str]:
    return {
        "ahash": average_hash(image),
        "dhash": difference_hash(image),
        "phash": perceptual_hash(image),
    }


def best_perceptual_distance(left: dict[str, Any], right: dict[str, Any]) -> tuple[str, int] | None:
    best: tuple[str, int] | None = None
    for name in ("dhash", "phash", "ahash"):
        distance = hamming_distance(left.get(name), right.get(name))
        if distance is None:
            continue
        if best is None or distance < best[1]:
            best = (name, distance)
    return best


def is_near_duplicate(distance: int | None) -> bool:
    return distance is not None and distance <= NEAR_DUPLICATE_MAX_DISTANCE
