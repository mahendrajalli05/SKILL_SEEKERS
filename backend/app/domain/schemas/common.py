from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.schemas.project import ProjectRead


class DatabaseHealth(BaseModel):
    connected: bool
    dialect: str
    path: str
    tables: list[str] = Field(default_factory=list)


class GovernanceNotice(BaseModel):
    outputs: list[str] = Field(
        default_factory=lambda: ["investigation_priority", "evidence_confidence"]
    )
    does_not_output: list[str] = Field(
        default_factory=lambda: ["legal_fraud_finding", "legal_fraud_probability"]
    )
    principle: str = "AI recommends. Authorized officers decide."


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    database: DatabaseHealth
    llm_enabled: bool
    engine_version: str
    fusion_config_version: str
    governance: GovernanceNotice


class ProjectListResponse(BaseModel):
    items: list[ProjectRead] = Field(default_factory=list)
    total: int = 0
    note: str = "Database starts empty. Load real public MPLADS records in Phase 2."
