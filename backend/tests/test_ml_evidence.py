from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.config import reset_settings_cache
from app.db import get_session_factory, init_db, reset_engine
from app.domain.enums import DataMode, EvidenceDisposition, SignalType, SourceType
from app.engines.compliance.constants import ENGINE_VERSION as COMPLIANCE_VERSION
from app.engines.cost.constants import ENGINE_VERSION as COST_VERSION
from app.engines.fusion.constants import ENGINE_VERSION as FUSION_V1_VERSION
from app.engines.fusion.constants import INTEGRATED_WEIGHTS
from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
from app.engines.fusion_v2.constants import GROUP_WEIGHTS, SIGNAL_TYPE_TO_GROUP
from app.engines.fusion_v2.fuse import fuse_evidence_v2
from app.engines.overlap.constants import ENGINE_VERSION as OVERLAP_VERSION
from app.engines.pce.constants import ENGINE_VERSION as PCE_VERSION
from app.engines.time.constants import ENGINE_VERSION as TIME_VERSION
from app.evidence.adapters.ml import (
    prediction_to_evidence,
    sanitize_ml_text,
    stored_ml_text_is_neutral,
)
from app.evidence.repository import add_evidence_object, list_project_evidence
from app.identity.scheme_id import reset_scheme_id_cache
from app.ml.constants import GOVERNANCE_NOTE
from app.ml.errors import MalformedMlInferenceError, ModelMissingError
from app.ml.evidence import create_project_ml_evidence, create_project_ml_evidence_payload
from app.ml.inference.cost import predict_cost
from app.ml.inference.loader import reset_model_cache
from app.ml.training.cost_train import train_from_session
from app.ml.types import ModelIdentity, MlPrediction, PredictionStatus, FeatureAvailability
from app.search.enrichment_display import reset_enrichment_display_cache
from app.search.hybrid import reset_hybrid_id_cache
from fusion_v2_fixtures import make_group_evidence
from tests.ml_fixtures import insert_real_work, seed_real_training_rows


@pytest.fixture()
def ml_client(tmp_path, monkeypatch) -> TestClient:
    db_path = tmp_path / "sarvsakshi-ml-evidence.db"
    models = tmp_path / "ml-models"
    monkeypatch.setenv("SARVSAKSHI_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("SARVSAKSHI_ML_MODELS_DIR", str(models))
    monkeypatch.setenv("SARVSAKSHI_LLM_ENABLED", "false")
    reset_settings_cache()
    reset_engine()
    reset_scheme_id_cache()
    reset_enrichment_display_cache()
    reset_hybrid_id_cache()
    reset_model_cache()
    init_db()
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
    reset_engine()
    reset_scheme_id_cache()
    reset_enrichment_display_cache()
    reset_hybrid_id_cache()
    reset_settings_cache()
    reset_model_cache()


def _train() -> str:
    session = get_session_factory()()
    try:
        seed_real_training_rows(session, n=48)
        record = train_from_session(session)
    finally:
        session.close()
    reset_model_cache()
    return record.model_version


def _subject(session, *, suffix: str = "subject", amount: int = 250_000, **kwargs):
    row = insert_real_work(session, suffix=suffix, amount=amount, **kwargs)
    row.source_dataset = "github_vonter_india-mplads-works_MPLADS.csv"
    session.flush()
    return row


def _facts(obj) -> dict:
    return {fact.key: fact.value for fact in obj.evidence_facts}


def test_create_ml_evidence_for_existing_project(ml_client: TestClient) -> None:
    version = _train()
    session = get_session_factory()()
    try:
        project = _subject(session)
        session.commit()
        project_id = project.id
        internal_id = project.internal_project_id
    finally:
        session.close()

    created = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL", "model_version": version},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["assessment_kind"] == "PROJECT_STORED_EVIDENCE"
    assert body["evidence_kind"] == "PROJECT_STORED_EVIDENCE"
    assert body["persisted"] is True
    assert body["fraud_probability"] is None
    assert body["model_version"] == version
    assert body["feature_schema_version"]
    assert body["training_data_hash"]
    assert body["data_mode"] == "REAL"
    assert body["ml_anomaly_score"] is not None
    assert "training distribution" in body["explanation"].lower() or "anomaly" in body["explanation"].lower()
    assert stored_ml_text_is_neutral(body["explanation"])
    assert stored_ml_text_is_neutral(body["finding"])
    assert "fraud" not in body["explanation"].casefold()
    assert body["limitations"]

    listed = ml_client.get(f"/api/v1/projects/{project_id}/evidence")
    assert listed.status_code == 200
    items = listed.json()["items"]
    assert any(item["engine_name"] == "ml" for item in items)
    ml_item = next(item for item in items if item["engine_name"] == "ml")
    assert ml_item["signal_type"] == SignalType.ML_ANOMALY_SIGNAL.value
    assert ml_item["evidence_id"] == body["evidence_id"]
    assert ml_item["data_mode"] == "REAL"
    assert ml_item["source_type"] == SourceType.ML_MODEL.value
    assert internal_id in ml_item["source_ids"]
    assert ml_item["score"] == body["ml_anomaly_score"]
    assert ml_item["confidence"] != ml_item["score"] or ml_item["score"] is None
    facts = {fact["key"]: fact["value"] for fact in ml_item["evidence_facts"]}
    assert facts["model_name"] == "cost-anomaly-v1"
    assert facts["model_version"] == version
    assert facts["feature_schema_version"]
    assert facts["training_data_hash"]
    assert facts["ml_anomaly_score"] is not None
    assert facts["data_mode"] == "REAL"
    assert facts["ml_score_is_distributional_rank"] is True
    assert stored_ml_text_is_neutral(str(ml_item))
    assert stored_ml_text_is_neutral(ml_item["finding"])
    assert stored_ml_text_is_neutral(ml_item["explanation"])
    assert stored_ml_text_is_neutral(str(ml_item["provenance"]))
    assert stored_ml_text_is_neutral(str(facts.get("limitations") or ""))
    assert stored_ml_text_is_neutral(str(facts.get("ml_anomaly_finding") or ""))
    assert "fraud" not in str(ml_item).casefold()

    filtered = ml_client.get(
        f"/api/v1/projects/{project_id}/evidence",
        params={"engine": "ml", "signal_type": SignalType.ML_ANOMALY_SIGNAL.value},
    )
    assert len(filtered.json()["items"]) == 1


def test_missing_project_missing_model_and_version(ml_client: TestClient) -> None:
    missing_project = ml_client.post("/api/v2/projects/999999/ml-evidence", json={"data_mode": "REAL"})
    assert missing_project.status_code == 404
    assert missing_project.json()["error"]["code"] == "not_found"

    session = get_session_factory()()
    try:
        project = _subject(session, suffix="nomodel")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    missing_model = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL"},
    )
    assert missing_model.status_code == 503
    assert missing_model.json()["error"]["code"] == "model_missing"

    _train()
    mismatch = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL", "model_version": "not-this-version"},
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["error"]["code"] == "model_version_mismatch"


def test_missing_required_feature_is_inconclusive(ml_client: TestClient) -> None:
    _train()
    session = get_session_factory()()
    try:
        project = _subject(session, suffix="no-amount", amount=250_000)
        project.allocation_amount = None
        project.category = ""
        session.commit()
        project_id = project.id
    finally:
        session.close()

    created = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL"},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["disposition"] == EvidenceDisposition.INCONCLUSIVE.value
    assert body["ml_anomaly_score"] is None
    assert "INCONCLUSIVE" in body["finding"]


def test_unsupported_data_mode_and_synthetic_rules(ml_client: TestClient) -> None:
    _train()
    session = get_session_factory()()
    try:
        real = _subject(session, suffix="real-mode")
        synthetic = _subject(session, suffix="synth-mode")
        synthetic.is_synthetic = True
        synthetic.synthetic_label = "SYNTHETIC: ml evidence unit test"
        session.commit()
        real_id = real.id
        synth_id = synthetic.id
    finally:
        session.close()

    bad = ml_client.post(
        f"/api/v2/projects/{real_id}/ml-evidence",
        json={"data_mode": "NOT_A_MODE"},
    )
    assert bad.status_code == 422

    synth_on_real = ml_client.post(
        f"/api/v2/projects/{real_id}/ml-evidence",
        json={"data_mode": "SYNTHETIC"},
    )
    assert synth_on_real.status_code == 422
    assert synth_on_real.json()["error"]["code"] == "unsupported_data_mode"

    real_on_synth = ml_client.post(
        f"/api/v2/projects/{synth_id}/ml-evidence",
        json={"data_mode": "REAL"},
    )
    assert real_on_synth.status_code == 422
    assert real_on_synth.json()["error"]["code"] == "unsupported_data_mode"

    stored = ml_client.post(
        f"/api/v2/projects/{synth_id}/ml-evidence",
        json={"data_mode": "SYNTHETIC"},
    )
    assert stored.status_code == 200, stored.text
    assert stored.json()["data_mode"] == "SYNTHETIC"
    listed = ml_client.get(f"/api/v1/projects/{synth_id}/evidence").json()["items"]
    ml_item = next(item for item in listed if item["engine_name"] == "ml")
    assert ml_item["data_mode"] == "SYNTHETIC"
    assert ml_item["source_type"] != SourceType.MPLADS_PROJECT_RECORD.value
    assert "SYNTHETIC" in ml_item["provenance"]["notes"]
    assert stored_ml_text_is_neutral(ml_item["explanation"])
    assert stored_ml_text_is_neutral(ml_item["finding"])


def test_hybrid_mode_is_not_labelled_real(ml_client: TestClient) -> None:
    _train()
    session = get_session_factory()()
    try:
        project = _subject(session, suffix="hybrid-mode")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    created = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "HYBRID"},
    )
    assert created.status_code == 200, created.text
    assert created.json()["data_mode"] == "HYBRID"
    listed = ml_client.get(f"/api/v1/projects/{project_id}/evidence").json()["items"]
    ml_item = next(item for item in listed if item["engine_name"] == "ml")
    assert ml_item["data_mode"] == "HYBRID"
    assert ml_item["source_type"] == SourceType.HYBRID_ENRICHMENT.value
    assert ml_item["provenance"]["enrichment_used"] is True
    assert ml_item["data_mode"] != "REAL"
    assert stored_ml_text_is_neutral(ml_item["explanation"])
    assert stored_ml_text_is_neutral(ml_item["finding"])


def test_immutability_second_prediction_appends(ml_client: TestClient) -> None:
    version = _train()
    session = get_session_factory()()
    try:
        project = _subject(session, suffix="immutable")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    first = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL", "model_version": version},
    ).json()
    second = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL", "model_version": version},
    ).json()
    assert first["evidence_id"] != second["evidence_id"]

    listed = ml_client.get(f"/api/v1/projects/{project_id}/evidence", params={"engine": "ml"}).json()
    ids = [item["evidence_id"] for item in listed["items"]]
    assert first["evidence_id"] in ids
    assert second["evidence_id"] in ids
    original = next(item for item in listed["items"] if item["evidence_id"] == first["evidence_id"])
    assert original["explanation"] == first["explanation"]
    assert original["engine_version"] == version

    session = get_session_factory()()
    try:
        from app.models.project import Project

        project = session.get(Project, project_id)
        prediction = predict_cost(
            {
                "state": project.state,
                "constituency": project.constituency,
                "category": project.category,
                "work_description": project.work_description,
                "allocation_amount": project.allocation_amount,
                "recommendation_date": project.recommended_date,
                "status": project.status,
                "house": project.house,
                "data_mode": "REAL",
            },
            data_mode="REAL",
            requested_version=version,
        )
        prediction.model.model_version = "cost-anomaly-v1-other-version"
        other = prediction_to_evidence(prediction, project, data_mode=DataMode.REAL)
        add_evidence_object(session, other)
        session.commit()
        stored = list_project_evidence(session, project_id, engine="ml")
        versions = {item.engine_version for item in stored}
        assert version in versions
        assert "cost-anomaly-v1-other-version" in versions
        first_row = next(item for item in stored if item.evidence_id == first["evidence_id"])
        assert first_row.explanation == first["explanation"]
    finally:
        session.close()


def test_corrupted_artifact_and_malformed_output(ml_client: TestClient, tmp_path: Path, monkeypatch) -> None:
    _train()
    session = get_session_factory()()
    try:
        project = _subject(session, suffix="corrupt")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    from app.ml.registry.store import artifact_path

    path = artifact_path("cost-anomaly-v1")
    path.write_bytes(b"not-a-joblib")
    reset_model_cache()
    corrupted = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL"},
    )
    assert corrupted.status_code == 503
    assert corrupted.json()["error"]["code"] == "corrupted_model_artifact"

    def fake_predict(*_args, **_kwargs):
        return MlPrediction(
            model=ModelIdentity(
                model_name="",
                model_version="",
                model_type="IsolationForest",
                training_mode="REAL",
                training_data_hash="",
                feature_schema_version="",
                created_at="",
            ),
            status=PredictionStatus.SCORED,
            ml_anomaly_score=None,
            decision_label="ELEVATED",
            feature_availability=FeatureAvailability(coverage=1.0),
            feature_values={},
            contributions=[],
            explanation="",
            limitations=[],
            data_mode="REAL",
        )

    monkeypatch.setattr("app.ml.evidence.predict_cost", fake_predict)
    reset_model_cache()
    with pytest.raises(MalformedMlInferenceError):
        session = get_session_factory()()
        try:
            create_project_ml_evidence(session, project_id, data_mode="REAL", model_version=None)
        finally:
            session.close()


def test_persistence_failure(ml_client: TestClient, monkeypatch) -> None:
    _train()
    session = get_session_factory()()
    try:
        project = _subject(session, suffix="persist-fail")
        session.commit()
        project_id = project.id
    finally:
        session.close()

    def boom(*_args, **_kwargs):
        raise SQLAlchemyError("persist failed")

    monkeypatch.setattr("app.ml.evidence.add_evidence_object", boom)
    response = ml_client.post(
        f"/api/v2/projects/{project_id}/ml-evidence",
        json={"data_mode": "REAL"},
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "database_error"


def test_new_project_assessment_is_not_stored_evidence(ml_client: TestClient) -> None:
    _train()
    predict = ml_client.post(
        "/api/v2/ml/predict",
        json={
            "state": "Andhra Pradesh",
            "constituency": "KURNOOL",
            "category": "Normal/Others",
            "work_description": "Construction of water tanks",
            "allocation_amount": 250000,
            "recommendation_date": "2023-06-01",
            "data_mode": "REAL",
        },
    )
    assert predict.status_code == 200
    body = predict.json()
    assert body["assessment_kind"] == "NEW_PROJECT_ASSESSMENT"
    assert body["evidence_kind"] == "NEW_PROJECT_ASSESSMENT"
    assert body["persisted"] is False

    assess = ml_client.post("/api/v2/projects/assess", json={"allocation_amount": 250000, "category": "Normal/Others", "data_mode": "REAL"})
    assert assess.status_code == 200
    payload = assess.json()
    assert payload["assessment_kind"] == "NEW_PROJECT_ASSESSMENT"
    assert payload["evidence_kind"] == "NEW_PROJECT_ASSESSMENT"
    assert payload["persisted"] is False
    assert payload["project_id"] is None


def test_frozen_engines_and_risk_fusion_ignore_ml() -> None:
    assert COST_VERSION == "cost-peer-v1.1"
    assert TIME_VERSION == "time-peer-v1"
    assert OVERLAP_VERSION == "overlap-multi-v1"
    assert COMPLIANCE_VERSION == "compliance-rules-v1"
    assert PCE_VERSION == "plan-claim-evidence-v1"
    assert FUSION_V1_VERSION == "risk-fusion-v1.1"
    assert FUSION_V2_VERSION == "risk-fusion-v2"
    assert INTEGRATED_WEIGHTS == {
        "cost": 0.25,
        "schedule": 0.15,
        "overlap": 0.15,
        "compliance": 0.15,
    }
    assert round(sum(GROUP_WEIGHTS.values()), 4) == 1.0
    assert SignalType.ML_ANOMALY_SIGNAL.value not in SIGNAL_TYPE_TO_GROUP
    assert "ml" not in GROUP_WEIGHTS

    cost = make_group_evidence("cost", score=80)
    without_ml = fuse_evidence_v2(
        [cost],
        project_id=101,
        internal_project_id="internal:fusion-v2:101",
        requested_data_mode=DataMode.REAL,
    )
    from tests.test_evidence_schema import _provenance, valid_evidence

    ml_obj = valid_evidence(
        engine_name="ml",
        engine_version="cost-anomaly-v1-test",
        signal_type=SignalType.ML_ANOMALY_SIGNAL,
        score=99,
        finding="ELEVATED_ANOMALY_SIGNAL: unsupervised Isolation Forest placed this work in the upper tail.",
        explanation="Allocation is unusual relative to the training distribution.",
        source_type=SourceType.ML_MODEL,
        provenance=_provenance(source_type=SourceType.ML_MODEL),
        evidence_id="ev:ml:101:ML_ANOMALY_SIGNAL:REAL:deadbeef",
    )
    with_ml = fuse_evidence_v2(
        [cost, ml_obj],
        project_id=101,
        internal_project_id="internal:fusion-v2:101",
        requested_data_mode=DataMode.REAL,
    )
    assert without_ml.investigation_priority == with_ml.investigation_priority
    assert "ml" not in {item.group_id for item in with_ml.contributing_evidence_groups}


def test_sanitize_uses_neutral_anomaly_language() -> None:
    cleaned = sanitize_ml_text("This is not a fraud probability.")
    assert "fraud" not in cleaned.casefold()
    assert "probability of wrongdoing" not in cleaned.casefold()
    assert "likelihood of wrongdoing" not in cleaned.casefold()
    assert "legal finding" not in cleaned.casefold()
    assert "legal guilt" not in cleaned.casefold()
    assert stored_ml_text_is_neutral(cleaned)
    assert "distribution" in cleaned.casefold() or "anomaly" in cleaned.casefold()

    governance = sanitize_ml_text(GOVERNANCE_NOTE)
    assert stored_ml_text_is_neutral(governance)
    assert "sanction" in governance.casefold() or "training distribution" in governance.casefold()

    finding = sanitize_ml_text("This is an ML anomaly signal, not a legal finding.")
    assert stored_ml_text_is_neutral(finding)
    assert "anomaly signal" in finding.casefold()


def test_stored_ml_finding_is_neutral_anomaly_language() -> None:
    from app.ml.types import FeatureAvailability, MlPrediction, ModelIdentity, PredictionStatus

    identity = ModelIdentity(
        model_name="cost-anomaly-v1",
        model_version="cost-anomaly-v1-test",
        model_type="IsolationForest",
        training_mode="REAL",
        training_data_hash="abc",
        feature_schema_version="cost-features-v1",
        created_at="2026-09-10T00:00:00+00:00",
    )
    elevated = MlPrediction(
        model=identity,
        status=PredictionStatus.SCORED,
        ml_anomaly_score=91,
        decision_label="ELEVATED",
        feature_availability=FeatureAvailability(available=["log_allocation"], coverage=1.0),
        feature_values={"log_allocation": 12.0},
        contributions=[],
        explanation=(
            "Allocation is unusual relative to the training distribution. "
            "Isolation Forest score 91/100 is a distributional rank, not a fraud probability."
        ),
        limitations=[GOVERNANCE_NOTE],
        data_mode="REAL",
    )
    from app.models.project import Project

    project = Project(
        id=1,
        internal_project_id="internal:test:ml-neutral",
        internal_id_kind="internal_surrogate_hash",
        internal_id_scheme="sarvsakshi_internal_work_v1",
        allocation_amount=250000,
        category="Normal/Others",
        constituency="KURNOOL",
        work_description="Construction of water tanks",
        is_synthetic=False,
        source_dataset="github_vonter_india-mplads-works_MPLADS.csv",
        lifecycle_stage="FUTURE",
    )
    obj = prediction_to_evidence(elevated, project, data_mode=DataMode.REAL)
    assert "ELEVATED_ANOMALY_SIGNAL" in obj.finding
    assert "training distribution" in obj.finding.casefold()
    assert stored_ml_text_is_neutral(obj.finding)
    assert stored_ml_text_is_neutral(obj.explanation)
    assert stored_ml_text_is_neutral(str(obj.model_dump(mode="json")))


def test_missing_model_service_without_http(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_DATABASE_PATH", str(tmp_path / "x.db"))
    monkeypatch.setenv("SARVSAKSHI_ML_MODELS_DIR", str(tmp_path / "models"))
    reset_settings_cache()
    reset_engine()
    init_db()
    session = get_session_factory()()
    try:
        project = _subject(session, suffix="svc-missing")
        session.commit()
        with pytest.raises(ModelMissingError):
            create_project_ml_evidence_payload(session, project.id, data_mode="REAL")
    finally:
        session.close()
        reset_engine()
        reset_settings_cache()
