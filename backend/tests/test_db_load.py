from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import REPO_ROOT, reset_settings_cache
from app.db import get_engine, get_session_factory, init_db, reset_engine
from app.models import Base
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot
from app.pipeline.clean import INTERNAL_ID_PREFIX, INTERNAL_ID_SCHEME, OUTPUT_COLUMN_ORDER
from app.pipeline.db_load import (
    FORBIDDEN_PROJECT_COLUMNS,
    LoadError,
    load_cleaned_works,
    project_index_names,
    sqlite_user_table_count,
)


CLEANED_CSV = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.csv"
CLEANED_PROVENANCE = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.provenance.json"

REQUIRED_INDEXES = {
    "ix_project_internal_project_id",
    "ix_project_state",
    "ix_project_constituency",
    "ix_project_category",
    "ix_project_status",
    "ix_project_mp_name",
    "ix_project_recommended_date",
}

EMPTY_EXTENSIBLE_TABLES = (
    "implementing_agency",
    "document",
    "photo",
    "photo_details",
    "claim",
    "plan",
    "plan_artifact",
    "guideline_rule",
    "guideline_snippet",
    "evidence_object",
    "evidence_fact",
    "overlap_link",
    "graph_edge",
    "fusion_score",
    "officer_decision",
    "audit_event",
    "copilot_turn",
    "citizen_report",
)


def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "sarvsakshi.db"
    monkeypatch.setenv("SARVSAKSHI_DATABASE_PATH", str(db_path))
    reset_settings_cache()
    reset_engine()
    init_db()
    return db_path


def _cleaned_row(internal_id: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "internal_project_id": internal_id,
        "internal_id_kind": "internal_surrogate_hash",
        "internal_id_scheme": INTERNAL_ID_SCHEME,
        "source_dataset": "github_vonter_india-mplads-works_MPLADS.csv",
        "source_first_row_number": "1",
        "source_duplicate_count": "1",
        "source_mp_name": "Shri Test MP",
        "source_work": "NA - Street lights",
        "source_category": "Normal/Others",
        "source_state": "Andhra Pradesh",
        "source_constituency": "GUNTUR",
        "source_ida": "DISTRICT COLLECTOR GUNTUR_IDA",
        "source_city": "",
        "source_ward": "",
        "source_block": "Tenali",
        "source_village": "Village A",
        "source_recommended_date": "2024-01-15",
        "source_allocation_amount": "250000",
        "source_ida_approval": "Action Pending",
        "source_status": "Unsanctioned",
        "source_house": "Lok Sabha",
        "mp_name": "Shri Test MP",
        "work_description": "NA - Street lights",
        "category": "Normal/Others",
        "state": "Andhra Pradesh",
        "constituency": "GUNTUR",
        "ida": "DISTRICT COLLECTOR GUNTUR_IDA",
        "city": "",
        "ward": "",
        "block": "Tenali",
        "village": "Village A",
        "recommended_date": "2024-01-15",
        "allocation_amount": "250000",
        "ida_approval": "Action Pending",
        "status": "Unsanctioned",
        "house": "Lok Sabha",
        "lifecycle_stage": "FUTURE",
    }
    row.update(overrides)
    return row


def _write_fixture(path: Path, rows: list[dict[str, object]]) -> None:
    frame = pd.DataFrame(rows, columns=list(OUTPUT_COLUMN_ORDER))
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8")


def _write_provenance(path: Path) -> None:
    path.write_text(
        '{"dataset_name": "TEST FIXTURE", "output_filename": "mplads_works_cleaned.csv",'
        ' "primary_source_filename": "github_vonter_india-mplads-works_MPLADS.csv",'
        ' "source_url": "https://example.invalid/MPLADS.csv",'
        ' "source_extracted_at": "2026-09-09", "source_download_date": "2026-09-09",'
        ' "source_publisher": "TEST FIXTURE — not a government extract",'
        ' "source_sha256": "abc", "cleaned_sha256": "def",'
        ' "cleaned_at": "2026-09-09T18:35:42+00:00",'
        f' "internal_id_scheme": "{INTERNAL_ID_SCHEME}",'
        ' "notes": "SYNTHETIC fixture for database load tests. Not a government extract."}',
        encoding="utf-8",
    )


@pytest.fixture()
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = _isolated_db(tmp_path, monkeypatch)
    yield db_path
    reset_engine()
    reset_settings_cache()


def test_database_creation_creates_sqlite_file_and_tables(isolated_db: Path) -> None:
    assert isolated_db.is_file()
    names = set(inspect(get_engine()).get_table_names())
    assert "project" in names
    assert "dataset_snapshot" in names
    assert sqlite_user_table_count() >= 19


def test_schema_has_cleaned_fields_and_named_indexes(isolated_db: Path) -> None:
    columns = {column["name"] for column in inspect(get_engine()).get_columns("project")}
    for name in (
        "internal_project_id",
        "source_mp_name",
        "source_work",
        "mp_name",
        "state",
        "constituency",
        "category",
        "status",
        "recommended_date",
        "allocation_amount",
        "lifecycle_stage",
    ):
        assert name in columns
    assert not (columns & FORBIDDEN_PROJECT_COLUMNS)
    indexes = project_index_names()
    assert REQUIRED_INDEXES.issubset(indexes)
    unique_index = next(
        index
        for index in inspect(get_engine()).get_indexes("project")
        if index["name"] == "ix_project_internal_project_id"
    )
    assert bool(unique_index["unique"]) is True
    assert unique_index["column_names"] == ["internal_project_id"]


def test_internal_project_id_uniqueness_is_enforced(isolated_db: Path) -> None:
    session: Session = get_session_factory()()
    try:
        shared = {
            "internal_project_id": f"{INTERNAL_ID_PREFIX}duplicate-test",
            "internal_id_kind": "internal_surrogate_hash",
            "internal_id_scheme": INTERNAL_ID_SCHEME,
            "is_synthetic": True,
            "synthetic_label": "SYNTHETIC: uniqueness test (not a government project)",
            "lifecycle_stage": "UNKNOWN",
        }
        session.add(Project(**shared))
        session.commit()
        session.add(Project(**shared))
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


def test_loading_preserves_source_values_and_row_count(
    isolated_db: Path, tmp_path: Path
) -> None:
    csv_path = tmp_path / "processed" / "mplads_works_cleaned.csv"
    provenance_path = tmp_path / "processed" / "mplads_works_cleaned.provenance.json"
    rows = [
        _cleaned_row(f"{INTERNAL_ID_PREFIX}aaa", source_first_row_number="2"),
        _cleaned_row(
            f"{INTERNAL_ID_PREFIX}bbb",
            source_first_row_number="3",
            source_mp_name="  Raw  Name  ",
            source_work="Original WORK text",
            source_status="",
            mp_name="Raw Name",
            work_description="Original WORK text",
            status="",
            lifecycle_stage="UNKNOWN",
            source_allocation_amount="100000",
            allocation_amount="100000",
        ),
    ]
    _write_fixture(csv_path, rows)
    _write_provenance(provenance_path)

    result = load_cleaned_works(csv_path=csv_path, provenance_path=provenance_path)
    assert result.failed_rows == []
    assert result.csv_row_count == 2
    assert result.loaded_row_count == 2
    assert result.ok is True

    session: Session = get_session_factory()()
    try:
        loaded = session.scalars(select(Project).order_by(Project.id)).all()
        assert len(loaded) == 2
        by_id = {row.internal_project_id: row for row in loaded}
        first = by_id[f"{INTERNAL_ID_PREFIX}aaa"]
        second = by_id[f"{INTERNAL_ID_PREFIX}bbb"]
        assert first.source_mp_name == "Shri Test MP"
        assert first.source_work == "NA - Street lights"
        assert first.source_allocation_amount == "250000"
        assert first.allocation_amount == 250000
        assert first.recommended_date.isoformat() == "2024-01-15"
        assert first.is_synthetic is False
        assert second.source_mp_name == "  Raw  Name  "
        assert second.source_work == "Original WORK text"
        assert second.source_status == ""
        snapshot = session.get(DatasetSnapshot, result.snapshot_id)
        assert snapshot is not None
        assert snapshot.source_url == "https://example.invalid/MPLADS.csv"
        assert snapshot.record_count == 2
        assert snapshot.original_filename == "mplads_works_cleaned.csv"
        for table in EMPTY_EXTENSIBLE_TABLES:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            assert count == 0
    finally:
        session.close()


def test_reload_replaces_previous_rows(isolated_db: Path, tmp_path: Path) -> None:
    csv_path = tmp_path / "processed" / "mplads_works_cleaned.csv"
    provenance_path = tmp_path / "processed" / "mplads_works_cleaned.provenance.json"
    _write_fixture(csv_path, [_cleaned_row(f"{INTERNAL_ID_PREFIX}one")])
    _write_provenance(provenance_path)
    first = load_cleaned_works(csv_path=csv_path, provenance_path=provenance_path)
    _write_fixture(
        csv_path,
        [
            _cleaned_row(f"{INTERNAL_ID_PREFIX}two", source_first_row_number="4"),
            _cleaned_row(f"{INTERNAL_ID_PREFIX}three", source_first_row_number="5"),
        ],
    )
    second = load_cleaned_works(csv_path=csv_path, provenance_path=provenance_path)
    assert first.ok and second.ok
    assert second.replaced_previous is True
    assert second.loaded_row_count == 2
    session: Session = get_session_factory()()
    try:
        ids = set(session.scalars(select(Project.internal_project_id)))
        assert ids == {f"{INTERNAL_ID_PREFIX}two", f"{INTERNAL_ID_PREFIX}three"}
        snapshots = session.scalars(select(DatasetSnapshot)).all()
        assert len(snapshots) == 1
    finally:
        session.close()


def test_failed_rows_are_reported_and_not_partially_committed(
    isolated_db: Path, tmp_path: Path
) -> None:
    csv_path = tmp_path / "processed" / "mplads_works_cleaned.csv"
    provenance_path = tmp_path / "processed" / "mplads_works_cleaned.provenance.json"
    rows = [
        _cleaned_row(f"{INTERNAL_ID_PREFIX}ok"),
        _cleaned_row("not-internal", source_first_row_number="9"),
    ]
    _write_fixture(csv_path, rows)
    _write_provenance(provenance_path)
    result = load_cleaned_works(csv_path=csv_path, provenance_path=provenance_path)
    assert len(result.failed_rows) == 1
    assert result.loaded_row_count == 0
    assert result.ok is False
    session: Session = get_session_factory()()
    try:
        assert session.scalar(select(Project).limit(1)) is None
    finally:
        session.close()


@pytest.mark.skipif(not CLEANED_CSV.is_file(), reason="cleaned extract is not present")
def test_real_cleaned_dataset_row_count_matches_database(
    isolated_db: Path,
) -> None:
    csv_count = len(pd.read_csv(CLEANED_CSV, dtype=str, keep_default_na=False))
    result = load_cleaned_works(csv_path=CLEANED_CSV, provenance_path=CLEANED_PROVENANCE)
    assert result.failed_rows == []
    assert result.csv_row_count == csv_count
    assert result.loaded_row_count == csv_count
    session: Session = get_session_factory()()
    try:
        db_count = session.scalar(
            select(func.count()).select_from(Project).where(Project.is_synthetic.is_(False))
        )
        assert db_count == csv_count
        sample = session.scalars(select(Project).limit(1)).first()
        assert sample is not None
        assert sample.internal_project_id.startswith(INTERNAL_ID_PREFIX)
        assert sample.source_dataset
        assert sample.source_mp_name is not None
    finally:
        session.close()


def test_row_count_validator_rejects_mismatch(isolated_db: Path) -> None:
    from app.pipeline.db_load import validate_loaded_row_count

    session: Session = get_session_factory()()
    try:
        with pytest.raises(LoadError, match="does not match cleaned dataset row count"):
            validate_loaded_row_count(session, 5)
    finally:
        session.close()


def test_models_metadata_includes_extensible_tables(isolated_db: Path) -> None:
    assert set(EMPTY_EXTENSIBLE_TABLES).issubset(Base.metadata.tables)
