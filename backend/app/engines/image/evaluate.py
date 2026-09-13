"""Image Evidence V1 evaluation: hashes, reuse, metadata, quality."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.domain.enums import DataMode
from app.engines.image.constants import (
    ANALYSIS_COMPLETE,
    ANALYSIS_UNREADABLE,
    EXACT_DUPLICATE,
    EXACT_DUPLICATE_CONFIDENCE,
    GOVERNANCE_NOTE,
    INTEGRITY_EXACT_DUPLICATE,
    INTEGRITY_POTENTIAL_REUSE,
    INTEGRITY_UNIQUE,
    INTEGRITY_UNREADABLE,
    NEAR_DUPLICATE_MAX_DISTANCE,
    POTENTIAL_IMAGE_REUSE,
    SUPPORTING_ONLY_NOTE,
)
from app.engines.image.forensics import assess_authenticity
from app.engines.image.hashes import (
    compute_hashes,
    hamming_distance,
    is_near_duplicate,
    similarity_from_distance,
)
from app.engines.image.metadata import extract_metadata
from app.engines.image.quality import assess_quality
from app.engines.image.types import ImageAnalysis, ReuseMatch
from app.models.artifacts import Photo


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _reuse_confidence(distance: int) -> float:
    if distance <= 0:
        return 0.9
    span = max(1, NEAR_DUPLICATE_MAX_DISTANCE)
    return round(max(0.4, min(0.9, 0.9 - (distance / span) * 0.4)), 4)


def evaluate_payload(
    session: Session,
    photo: Photo,
    payload: bytes,
) -> ImageAnalysis:
    authenticity = assess_authenticity(payload)
    quality = assess_quality(payload)
    metadata = extract_metadata(payload)
    notes = [GOVERNANCE_NOTE, SUPPORTING_ONLY_NOTE]
    hashes: dict[str, str | None] = {"ahash": None, "dhash": None, "phash": None}
    readable = bool(quality.get("readable"))
    try:
        with Image.open(BytesIO(payload)) as image:
            image.load()
            hashes = compute_hashes(image)
    except (UnidentifiedImageError, OSError, ValueError):
        readable = False

    duplicate_of_id: int | None = None
    exact = False
    matches: list[ReuseMatch] = []
    peers = []
    if photo.data_mode:
        from app.engines.image.repository import list_comparable_photos

        peers = list_comparable_photos(
            session,
            data_mode=photo.data_mode,
            exclude_id=photo.id,
        )
    for peer in peers:
        if photo.content_sha256 and peer.content_sha256 == photo.content_sha256:
            exact = True
            if duplicate_of_id is None:
                duplicate_of_id = peer.id
            matches.append(
                ReuseMatch(
                    image_id=photo.id,
                    matched_image_id=peer.id,
                    matched_project_id=peer.project_id,
                    hash_name="sha256",
                    distance=0,
                    similarity=1.0,
                    explanation=(
                        f"SHA-256 of this file matches image {peer.id}. "
                        f"{EXACT_DUPLICATE}. High visual/file identity is not proof of wrongdoing."
                    ),
                    confidence=EXACT_DUPLICATE_CONFIDENCE,
                    data_mode=peer.data_mode,
                )
            )
            continue
        if not readable:
            continue
        peer_hashes = {"ahash": peer.ahash, "dhash": peer.dhash, "phash": peer.phash}
        distances = {
            "dhash": hamming_distance(hashes.get("dhash"), peer_hashes["dhash"]),
            "phash": hamming_distance(hashes.get("phash"), peer_hashes["phash"]),
            "ahash": hamming_distance(hashes.get("ahash"), peer_hashes["ahash"]),
        }
        usable = [(name, dist) for name, dist in distances.items() if dist is not None]
        if not usable:
            continue
        name, distance = min(usable, key=lambda item: item[1])
        if not is_near_duplicate(distance):
            continue
        matches.append(
            ReuseMatch(
                image_id=photo.id,
                matched_image_id=peer.id,
                matched_project_id=peer.project_id,
                hash_name=name,
                distance=distance,
                similarity=similarity_from_distance(distance),
                explanation=(
                    f"Perceptual {name} distance is {distance} of 64 bits versus image {peer.id}. "
                    f"{POTENTIAL_IMAGE_REUSE}. High visual similarity alone is not proof of wrongdoing."
                ),
                confidence=_reuse_confidence(distance),
                data_mode=peer.data_mode,
            )
        )

    exact_matches = [item for item in matches if item.hash_name == "sha256"]
    reuse_matches = [item for item in matches if item.hash_name != "sha256"]
    if exact:
        reuse_matches = []
    potential = bool(reuse_matches) and not exact
    if not readable:
        integrity = INTEGRITY_UNREADABLE
        status = ANALYSIS_UNREADABLE
        notes.append("File could not be decoded as an image.")
    elif exact:
        integrity = INTEGRITY_EXACT_DUPLICATE
        status = ANALYSIS_COMPLETE
    elif potential:
        integrity = INTEGRITY_POTENTIAL_REUSE
        status = ANALYSIS_COMPLETE
    else:
        integrity = INTEGRITY_UNIQUE
        status = ANALYSIS_COMPLETE

    mode = DataMode(photo.data_mode) if photo.data_mode else DataMode.REAL
    analysis = ImageAnalysis(
        image_id=photo.id,
        project_id=photo.project_id,
        content_sha256=photo.content_sha256 or "",
        ahash=hashes.get("ahash"),
        dhash=hashes.get("dhash"),
        phash=hashes.get("phash"),
        integrity_status=integrity,
        duplicate_of_id=duplicate_of_id,
        exact_duplicate=exact,
        potential_reuse=potential,
        exact_matches=exact_matches,
        reuse_matches=reuse_matches,
        metadata_fields=list(metadata.get("fields") or []),
        metadata_status=str(metadata.get("status") or "METADATA_UNAVAILABLE"),
        gps_available=bool(metadata.get("gps_available")),
        gps_message=metadata.get("gps_message"),
        capture_timestamp=metadata.get("capture_timestamp"),
        latitude=metadata.get("latitude"),
        longitude=metadata.get("longitude"),
        quality=quality,
        authenticity=authenticity,
        data_mode=mode,
        notes=notes,
    )
    _ = status
    analysis.notes.append(authenticity.explanation)
    return analysis


def persistable_analysis(analysis: ImageAnalysis) -> dict[str, Any]:
    payload = analysis.as_dict()
    payload["captured_at"] = analysis.capture_timestamp
    return payload


def captured_at(analysis: ImageAnalysis) -> datetime | None:
    return _parse_datetime(analysis.capture_timestamp)
