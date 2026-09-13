from __future__ import annotations

from app.domain.enums import DataMode, SourceType
from app.evidence.constants import HYBRID_ENRICHMENT_RELATIVE_PATH
from app.evidence.provenance import build_provenance, build_source_ids, resolve_data_mode
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot


def _project(**overrides: object) -> Project:
    values: dict[str, object] = {
        "internal_project_id": "internal:prov:1",
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": "sarvsakshi_internal_work_v1",
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "source_first_row_number": 12,
        "is_synthetic": False,
        "lifecycle_stage": "FUTURE",
    }
    values.update(overrides)
    return Project(**values)


def test_real_provenance_cites_extract_not_synthetic() -> None:
    snapshot = DatasetSnapshot(
        source_url="https://example.invalid/mplads.csv",
        download_date="2026-09-09",
        publisher="Test publisher",
        file_sha256="abc",
        source_filename="github_vonter_india-mplads-works_MPLADS.csv",
    )
    project = _project()
    provenance = build_provenance(
        project,
        data_mode=DataMode.REAL,
        source_type=SourceType.MPLADS_PROJECT_RECORD,
        source_ids=build_source_ids(project.internal_project_id),
        snapshot=snapshot,
    )
    assert provenance.data_mode == DataMode.REAL
    assert provenance.enrichment_used is False
    assert provenance.source_url == "https://example.invalid/mplads.csv"
    assert "real MPLADS" in provenance.notes
    assert "SYNTHETIC test record" not in provenance.notes


def test_hybrid_provenance_keeps_enrichment_path() -> None:
    project = _project()
    provenance = build_provenance(
        project,
        data_mode=DataMode.HYBRID,
        source_type=SourceType.HYBRID_ENRICHMENT,
        source_ids=build_source_ids(project.internal_project_id, ["project:2"]),
    )
    assert provenance.enrichment_used is True
    assert provenance.enrichment_path == HYBRID_ENRICHMENT_RELATIVE_PATH
    assert project.internal_project_id in provenance.source_ids
    assert "project:2" in provenance.source_ids
    assert "HYBRID" in provenance.notes


def test_resolve_data_mode_never_marks_real_as_synthetic() -> None:
    assert resolve_data_mode(is_synthetic=False) == DataMode.REAL
    assert resolve_data_mode(is_synthetic=False, engine_mode="HYBRID_TEST") == DataMode.HYBRID
    assert resolve_data_mode(is_synthetic=True, engine_mode="REAL") == DataMode.SYNTHETIC
