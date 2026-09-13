"""Exact-file and similar-text document integrity. Not a fraud conclusion."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.document.constants import (
    INTEGRITY_DUPLICATE_FILE,
    INTEGRITY_SIMILAR_DOCUMENT,
    INTEGRITY_UNIQUE,
)
from app.models.artifacts import Document, PlanArtifact


def find_duplicate_files(
    session: Session,
    *,
    project_id: int,
    content_sha256: str,
    exclude_id: int | None = None,
) -> list[Document]:
    stmt = select(Document).where(
        Document.project_id == project_id,
        Document.content_sha256 == content_sha256,
    )
    if exclude_id is not None:
        stmt = stmt.where(Document.id != exclude_id)
    return list(session.scalars(stmt).all())


def find_similar_documents(
    session: Session,
    *,
    project_id: int,
    text_sha256: str,
    file_sha256: str,
    exclude_id: int | None = None,
) -> list[int]:
    stmt = (
        select(PlanArtifact)
        .join(Document, PlanArtifact.document_id == Document.id)
        .where(
            Document.project_id == project_id,
            PlanArtifact.text_sha256 == text_sha256,
        )
    )
    if exclude_id is not None:
        stmt = stmt.where(Document.id != exclude_id)
    ids: list[int] = []
    for artifact in session.scalars(stmt).all():
        document = artifact.document
        if document is None or document.content_sha256 == file_sha256:
            continue
        ids.append(document.id)
    return ids


def integrity_status(*, duplicate_of_id: int | None, similar_ids: list[int]) -> str:
    if duplicate_of_id is not None:
        return INTEGRITY_DUPLICATE_FILE
    if similar_ids:
        return INTEGRITY_SIMILAR_DOCUMENT
    return INTEGRITY_UNIQUE
