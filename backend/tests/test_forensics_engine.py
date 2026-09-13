from __future__ import annotations

from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.document.constants import ENGINE_VERSION as DOCUMENT_VERSION
from app.engines.forensics.ai import (
    UnavailableAiGenerationDetector,
    analyze_ai_generation,
    get_ai_detector,
    reset_ai_detector,
    set_ai_detector,
)
from app.engines.forensics.constants import (
    AI_GENERATION_ANALYSIS_UNAVAILABLE,
    ENGINE_VERSION,
    METADATA_ANOMALY,
    NO_STRONG_FORENSIC_SIGNAL,
    POTENTIAL_MANIPULATION,
)
from app.engines.forensics.evaluate import evaluate_image_forensics
from app.engines.forensics.integrity import check_integrity
from app.engines.forensics.metadata import analyze_metadata
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_VERSION
from app.engines.geo.constants import ENGINE_VERSION as GEO_VERSION
from app.engines.graph.constants import ENGINE_VERSION as GRAPH_VERSION
from app.engines.image.constants import ENGINE_VERSION as IMAGE_VERSION
from app.engines.image.security import sha256_bytes
from app.engines.milestone.constants import ENGINE_VERSION as MILESTONE_VERSION
from app.engines.need.constants import ENGINE_VERSION as NEED_VERSION
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from app.engines.citizen.constants import ENGINE_VERSION as CITIZEN_VERSION
from app.domain.enums import DataMode
from tests.forensics_fixtures import (
    copy_move_png,
    metadata_inconsistent_jpeg,
    metadata_stripped_jpeg,
    original_jpeg,
    recompressed_jpeg,
    resized_jpeg,
    unique_png,
)
from tests.image_fixtures import jpeg_with_exif_gps


def test_frozen_engines_unchanged() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert FUSION_VERSION == "risk-fusion-v1.1"
    assert GRAPH_VERSION == "relationship-graph-v1"
    assert PCE_VERSION == "plan-claim-evidence-v1"
    assert DOCUMENT_VERSION == "document-blueprint-v1"
    assert IMAGE_VERSION == "image-evidence-v1"
    assert GEO_VERSION == "geospatial-consistency-v1"
    assert NEED_VERSION == "need-impact-v1"
    assert MILESTONE_VERSION == "milestone-advisor-v1"
    assert CITIZEN_VERSION == "jan-sakshi-v1"
    assert ENGINE_VERSION == "image-forensics-v1"


def test_integrity_does_not_rewrite_bytes() -> None:
    payload = original_jpeg()
    digest = sha256_bytes(payload)
    result = check_integrity(payload, stored_sha256=digest, mime_type="image/jpeg", file_size=len(payload))
    assert result.bytes_unmodified is True
    assert result.content_sha256 == digest
    assert sha256_bytes(payload) == digest


def test_missing_exif_is_not_manipulation() -> None:
    signal = analyze_metadata(unique_png(), data_mode=DataMode.REAL)
    assert signal.result != POTENTIAL_MANIPULATION
    blob = " ".join(signal.findings + signal.notes).casefold()
    assert "not proof of manipulation" in blob or "not treated as manipulation" in blob
    assert "fraud" not in blob
    assert "fake" not in blob


def test_inconsistent_metadata_is_anomaly_only() -> None:
    signal = analyze_metadata(metadata_inconsistent_jpeg(), data_mode=DataMode.HYBRID)
    assert signal.result == METADATA_ANOMALY
    blob = " ".join(signal.findings + signal.notes).casefold()
    assert "photoshop" in blob or "editor" in blob or "timestamp" in blob
    assert "definitely manipulated" not in blob
    assert "fraud" not in blob


def test_stripped_metadata_is_inconclusive_or_unavailable() -> None:
    signal = analyze_metadata(metadata_stripped_jpeg(), data_mode=DataMode.REAL)
    assert signal.result in {NO_STRONG_FORENSIC_SIGNAL, "INCONCLUSIVE"}
    assert signal.details.get("exif_present") in {False, False}


def test_recompress_and_resize_do_not_claim_certainty() -> None:
    original = original_jpeg()
    recompressed = recompressed_jpeg(original)
    resized = resized_jpeg(original)
    for payload, label in ((original, "original"), (recompressed, "recompressed"), (resized, "resized")):
        result = evaluate_image_forensics(
            image_id=1,
            project_id=1,
            payload=payload,
            stored_sha256=sha256_bytes(payload),
            mime_type="image/jpeg",
            file_size=len(payload),
            data_mode=DataMode.SYNTHETIC,
            image_analysis={"integrity_status": "UNIQUE", "quality": {"readable": True, "warnings": []}},
        )
        assert result.manipulation_signal.result in {
            NO_STRONG_FORENSIC_SIGNAL,
            "INCONCLUSIVE",
            POTENTIAL_MANIPULATION,
        }
        if label != "original":
            assert result.manipulation_signal.result != "DEFINITELY_MANIPULATED"
        assert "fraud" not in result.explanation.casefold()
        assert "this image is fake" not in result.explanation.casefold()
        assert "definitely manipulated" not in result.explanation.casefold()
        assert result.bytes_unmodified is True


def test_copy_move_is_potential_manipulation() -> None:
    payload = copy_move_png()
    result = evaluate_image_forensics(
        image_id=2,
        project_id=1,
        payload=payload,
        stored_sha256=sha256_bytes(payload),
        mime_type="image/png",
        file_size=len(payload),
        data_mode=DataMode.SYNTHETIC,
        image_analysis={"integrity_status": "UNIQUE", "quality": {"readable": True, "warnings": []}},
    )
    assert result.manipulation_signal.result == POTENTIAL_MANIPULATION
    assert "not" in " ".join(result.manipulation_signal.notes).casefold()
    assert "definitely manipulated" not in result.explanation.casefold()


def test_camera_exif_has_timestamp_available() -> None:
    signal = analyze_metadata(jpeg_with_exif_gps(), data_mode=DataMode.REAL)
    assert signal.details.get("display") in {"TIMESTAMP_AVAILABLE", METADATA_ANOMALY}
    assert signal.details.get("capture_timestamp") or signal.details.get("exif_present")


def test_ai_detector_default_unavailable() -> None:
    reset_ai_detector()
    detector = get_ai_detector()
    assert isinstance(detector, UnavailableAiGenerationDetector)
    signal = analyze_ai_generation(original_jpeg(), data_mode=DataMode.REAL)
    assert signal.result == AI_GENERATION_ANALYSIS_UNAVAILABLE
    assert signal.details.get("external_transmission") is False
    assert signal.details.get("score") is None
    assert "definitely ai-generated" not in " ".join(signal.findings).casefold()


def test_ai_detector_plugin_abstraction() -> None:
    class StubDetector:
        name = "stub-local"

        def available(self) -> bool:
            return False

        def analyze(self, payload: bytes) -> dict:
            _ = payload
            return {
                "capability": AI_GENERATION_ANALYSIS_UNAVAILABLE,
                "result": "INCONCLUSIVE",
                "score": None,
                "explanation": "Stub local detector returned INCONCLUSIVE without a validated score.",
                "external_transmission": False,
            }

    set_ai_detector(StubDetector())
    try:
        signal = analyze_ai_generation(original_jpeg(), data_mode=DataMode.REAL)
        assert signal.result in {AI_GENERATION_ANALYSIS_UNAVAILABLE, "INCONCLUSIVE"}
        assert signal.details.get("score") is None
    finally:
        reset_ai_detector()
