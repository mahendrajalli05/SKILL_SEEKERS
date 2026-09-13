from __future__ import annotations

from sqlalchemy.orm import Session

from app.db import get_session_factory
from app.models.fusion import FusionScore
from app.models.project import Project


SYNTHETIC_LABEL = "SYNTHETIC: unit-test placeholder (not a government project)"
SYNTHETIC_INTERNAL_ID = "internal:synthetic:unit-test-placeholder-1"


def _synthetic_project(**overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": SYNTHETIC_INTERNAL_ID,
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "is_synthetic": True,
        "synthetic_label": SYNTHETIC_LABEL,
        "lifecycle_stage": "UNKNOWN",
    }
    values.update(overrides)
    return Project(**values)


def test_can_insert_synthetic_row_with_observed_government_fields_null(client) -> None:
    session: Session = get_session_factory()()
    try:
        row = _synthetic_project()
        session.add(row)
        session.commit()
        session.refresh(row)
        assert row.id is not None
        assert row.internal_project_id == SYNTHETIC_INTERNAL_ID
        assert row.mp_name is None
        assert row.allocation_amount is None
        assert row.recommended_date is None
        assert row.state is None
        assert row.is_synthetic is True
        assert row.synthetic_label.startswith("SYNTHETIC")
    finally:
        session.close()


def test_fusion_score_accepts_null_priority_until_engines_exist(client) -> None:
    session: Session = get_session_factory()()
    try:
        project = _synthetic_project()
        session.add(project)
        session.flush()
        score = FusionScore(
            project_id=project.id,
            investigation_priority=None,
            evidence_confidence=None,
            config_version="p0-v1",
        )
        session.add(score)
        session.commit()
        assert score.investigation_priority is None
        assert score.evidence_confidence is None
    finally:
        session.close()
