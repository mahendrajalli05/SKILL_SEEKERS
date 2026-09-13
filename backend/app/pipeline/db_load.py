"""Load the cleaned work-level extract into SQLite.

Reads ``data/processed/mplads_works_cleaned.csv`` only. Does not modify
``data/raw/``, does not invent government fields, and does not populate
evidence, risk, graph, citizen, or review tables.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete, func, insert, inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.config import REPO_ROOT
from app.db import get_engine, get_session_factory, init_db
from app.logging_config import get_logger
from app.models import Base
from app.models.project import Project
from app.models.snapshot import DatasetSnapshot
from app.pipeline.clean import INTERNAL_ID_PREFIX, INTERNAL_ID_SCHEME, OUTPUT_COLUMN_ORDER

logger = get_logger("sarvsakshi.db_load")

DEFAULT_CLEANED_CSV = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.csv"
DEFAULT_CLEANED_PROVENANCE = REPO_ROOT / "data" / "processed" / "mplads_works_cleaned.provenance.json"
INSERT_CHUNK_SIZE = 200
CLEANED_SNAPSHOT_FILENAME = "mplads_works_cleaned.csv"

REQUIRED_CSV_COLUMNS = tuple(OUTPUT_COLUMN_ORDER)
SOURCE_VALUE_COLUMNS = (
    "source_mp_name",
    "source_work",
    "source_category",
    "source_state",
    "source_constituency",
    "source_ida",
    "source_city",
    "source_ward",
    "source_block",
    "source_village",
    "source_recommended_date",
    "source_allocation_amount",
    "source_ida_approval",
    "source_status",
    "source_house",
)
# Government fields that must not be invented on ``project``.
FORBIDDEN_PROJECT_COLUMNS = frozenset(
    {
        "district",
        "implementing_district",
        "vendor",
        "contractor",
        "latitude",
        "longitude",
        "gps",
        "expenditure",
        "utilised_amount",
        "sanctioned_amount",
        "sanction_date",
        "date_of_completion",
        "completion_date",
        "unique_work_number",
    }
)


class LoadError(ValueError):
    """Cleaned-extract load failed validation."""


@dataclass
class FailedRow:
    csv_row_number: int
    internal_project_id: str
    reason: str


@dataclass
class LoadResult:
    database_path: Path
    table_count: int
    csv_row_count: int
    loaded_row_count: int
    failed_rows: list[FailedRow] = field(default_factory=list)
    snapshot_id: int | None = None
    replaced_previous: bool = False

    @property
    def ok(self) -> bool:
        return not self.failed_rows and self.loaded_row_count == self.csv_row_count


def read_cleaned_frame(csv_path: Path) -> pd.DataFrame:
    if not csv_path.is_file():
        raise FileNotFoundError(f"Cleaned extract not found: {csv_path}")
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    missing = [name for name in REQUIRED_CSV_COLUMNS if name not in frame.columns]
    if missing:
        raise LoadError(f"Cleaned CSV is missing required columns: {missing}")
    extra = [name for name in FORBIDDEN_PROJECT_COLUMNS if name in frame.columns]
    if extra:
        raise LoadError(f"Refusing to load invented government columns: {extra}")
    return frame


def read_cleaned_provenance(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _cell(row: pd.Series, column: str) -> str:
    value = row.get(column, "")
    if value is None:
        return ""
    return str(value)


def _optional_int(text: str, *, field_name: str, csv_row_number: int) -> int:
    raw = text.strip()
    if not raw:
        raise LoadError(f"row {csv_row_number}: {field_name} is blank")
    try:
        number = float(raw)
    except ValueError as exc:
        raise LoadError(f"row {csv_row_number}: {field_name} is not an integer") from exc
    if not number.is_integer():
        raise LoadError(f"row {csv_row_number}: {field_name} is not an integer")
    return int(number)


def _optional_amount(text: str, csv_row_number: int) -> int | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        number = float(raw)
    except ValueError as exc:
        raise LoadError(f"row {csv_row_number}: allocation_amount is not numeric") from exc
    if not number.is_integer():
        raise LoadError(f"row {csv_row_number}: allocation_amount is not an integer")
    return int(number)


def _optional_date(text: str, csv_row_number: int) -> date | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise LoadError(f"row {csv_row_number}: recommended_date is not ISO YYYY-MM-DD") from exc


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        parsed = date.fromisoformat(text)
        return datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)
    normalised = text.replace("Z", "+00:00")
    parsed_dt = datetime.fromisoformat(normalised)
    if parsed_dt.tzinfo is None:
        return parsed_dt.replace(tzinfo=timezone.utc)
    return parsed_dt


def mapping_from_cleaned_row(
    row: pd.Series,
    *,
    csv_row_number: int,
    snapshot_id: int,
) -> dict[str, Any]:
    internal_project_id = _cell(row, "internal_project_id").strip()
    if not internal_project_id:
        raise LoadError(f"row {csv_row_number}: missing internal_project_id")
    if not internal_project_id.startswith(INTERNAL_ID_PREFIX):
        raise LoadError(
            f"row {csv_row_number}: internal_project_id is not labelled as an internal key"
        )

    mapping: dict[str, Any] = {
        "internal_project_id": internal_project_id,
        "internal_id_kind": _cell(row, "internal_id_kind").strip(),
        "internal_id_scheme": _cell(row, "internal_id_scheme").strip() or INTERNAL_ID_SCHEME,
        "source_dataset": _cell(row, "source_dataset"),
        "source_first_row_number": _optional_int(
            _cell(row, "source_first_row_number"),
            field_name="source_first_row_number",
            csv_row_number=csv_row_number,
        ),
        "source_duplicate_count": _optional_int(
            _cell(row, "source_duplicate_count"),
            field_name="source_duplicate_count",
            csv_row_number=csv_row_number,
        ),
        "mp_name": _cell(row, "mp_name"),
        "work_description": _cell(row, "work_description"),
        "category": _cell(row, "category"),
        "state": _cell(row, "state"),
        "constituency": _cell(row, "constituency"),
        "ida": _cell(row, "ida"),
        "city": _cell(row, "city"),
        "ward": _cell(row, "ward"),
        "block": _cell(row, "block"),
        "village": _cell(row, "village"),
        "recommended_date": _optional_date(_cell(row, "recommended_date"), csv_row_number),
        "allocation_amount": _optional_amount(_cell(row, "allocation_amount"), csv_row_number),
        "ida_approval": _cell(row, "ida_approval"),
        "status": _cell(row, "status"),
        "house": _cell(row, "house"),
        "lifecycle_stage": _cell(row, "lifecycle_stage").strip() or "UNKNOWN",
        "snapshot_id": snapshot_id,
        "is_synthetic": False,
        "synthetic_label": None,
        "agency_id": None,
    }
    if not mapping["internal_id_kind"]:
        raise LoadError(f"row {csv_row_number}: missing internal_id_kind")
    for column in SOURCE_VALUE_COLUMNS:
        mapping[column] = _cell(row, column)
    return mapping


def _delete_previous_cleaned_load(session: Any) -> bool:
    snapshots = session.scalars(
        select(DatasetSnapshot).where(
            DatasetSnapshot.original_filename == CLEANED_SNAPSHOT_FILENAME
        )
    ).all()
    if not snapshots:
        return False
    snapshot_ids = [row.id for row in snapshots]
    session.execute(delete(Project).where(Project.snapshot_id.in_(snapshot_ids)))
    session.execute(delete(DatasetSnapshot).where(DatasetSnapshot.id.in_(snapshot_ids)))
    return True


def _insert_snapshot(session: Any, provenance: dict[str, Any], record_count: int) -> DatasetSnapshot:
    stats = provenance.get("stats") if isinstance(provenance.get("stats"), dict) else {}
    snapshot = DatasetSnapshot(
        source_url=provenance.get("source_url"),
        extracted_at=_parse_datetime(provenance.get("source_extracted_at")),
        download_date=str(provenance.get("source_download_date") or "") or None,
        publisher=provenance.get("source_publisher"),
        file_sha256=provenance.get("cleaned_sha256"),
        original_filename=CLEANED_SNAPSHOT_FILENAME,
        source_filename=provenance.get("primary_source_filename")
        or stats.get("source_filename"),
        source_sha256=provenance.get("source_sha256"),
        internal_id_scheme=provenance.get("internal_id_scheme") or INTERNAL_ID_SCHEME,
        cleaned_at=_parse_datetime(provenance.get("cleaned_at")),
        record_count=record_count,
        notes=provenance.get("notes"),
    )
    session.add(snapshot)
    session.flush()
    return snapshot


def validate_loaded_row_count(session: Any, expected: int) -> int:
    actual = session.scalar(
        select(func.count())
        .select_from(Project)
        .where(Project.is_synthetic.is_(False))
    ) or 0
    if actual != expected:
        raise LoadError(
            f"Database row count {actual} does not match cleaned dataset row count {expected}."
        )
    distinct_ids = session.scalar(
        select(func.count(func.distinct(Project.internal_project_id))).where(
            Project.is_synthetic.is_(False)
        )
    ) or 0
    if distinct_ids != actual:
        raise LoadError(
            "internal_project_id is not unique in the loaded project table "
            f"(rows={actual}, distinct={distinct_ids})."
        )
    return actual


def load_cleaned_works(
    *,
    csv_path: Path | None = None,
    provenance_path: Path | None = None,
    replace: bool = True,
) -> LoadResult:
    csv_path = Path(csv_path) if csv_path is not None else DEFAULT_CLEANED_CSV
    provenance_path = (
        Path(provenance_path) if provenance_path is not None else DEFAULT_CLEANED_PROVENANCE
    )

    init_db()
    engine = get_engine()
    frame = read_cleaned_frame(csv_path)
    provenance = read_cleaned_provenance(provenance_path)
    csv_row_count = int(len(frame))

    failed: list[FailedRow] = []
    mappings: list[dict[str, Any]] = []
    session = get_session_factory()()
    try:
        replaced = _delete_previous_cleaned_load(session) if replace else False
        snapshot = _insert_snapshot(session, provenance, csv_row_count)
        snapshot_id = int(snapshot.id)

        for offset, (_, row) in enumerate(frame.iterrows()):
            csv_row_number = offset + 2  # header is row 1
            try:
                mappings.append(
                    mapping_from_cleaned_row(
                        row, csv_row_number=csv_row_number, snapshot_id=snapshot_id
                    )
                )
            except LoadError as exc:
                failed.append(
                    FailedRow(
                        csv_row_number=csv_row_number,
                        internal_project_id=_cell(row, "internal_project_id").strip(),
                        reason=str(exc),
                    )
                )

        if failed:
            session.rollback()
            return LoadResult(
                database_path=Path(str(engine.url.database)),
                table_count=len(Base.metadata.tables),
                csv_row_count=csv_row_count,
                loaded_row_count=0,
                failed_rows=failed,
                snapshot_id=None,
                replaced_previous=replaced,
            )

        for start in range(0, len(mappings), INSERT_CHUNK_SIZE):
            chunk = mappings[start : start + INSERT_CHUNK_SIZE]
            session.execute(insert(Project), chunk)

        validate_loaded_row_count(session, csv_row_count)
        session.commit()
        loaded = csv_row_count
        logger.info(
            "cleaned_works_loaded path=%s rows=%s snapshot_id=%s",
            engine.url.database,
            loaded,
            snapshot_id,
        )
        return LoadResult(
            database_path=Path(str(engine.url.database)),
            table_count=len(inspect(engine).get_table_names()),
            csv_row_count=csv_row_count,
            loaded_row_count=loaded,
            failed_rows=[],
            snapshot_id=snapshot_id,
            replaced_previous=replaced,
        )
    except IntegrityError as exc:
        session.rollback()
        raise LoadError(f"SQLite rejected the load (uniqueness or constraint): {exc}") from exc
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def table_names(engine=None) -> list[str]:
    return sorted(inspect(engine or get_engine()).get_table_names())


def project_index_names(engine=None) -> set[str]:
    indexes = inspect(engine or get_engine()).get_indexes("project")
    return {index["name"] for index in indexes if index.get("name")}


def sqlite_user_table_count(engine=None) -> int:
    with (engine or get_engine()).connect() as connection:
        count = connection.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        ).scalar()
    return int(count or 0)
