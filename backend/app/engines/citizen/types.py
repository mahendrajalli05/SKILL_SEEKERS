"""Jan-Sakshi / Citizen Evidence V1 types."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _as_dict(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, list):
        return [_as_dict(item) for item in value]
    if isinstance(value, dict):
        return {key: _as_dict(item) for key, item in value.items()}
    return value


@dataclass
class LocationVerification:
    result: str
    project_gps_available: bool
    citizen_gps_available: bool
    distance_meters: float | None
    threshold_meters: float
    distance_band: str | None
    reason: str
    prototype_rule_note: str
    project_location_synthetic: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackAnalysis:
    sentiment: str
    issue_category: str | None
    extracted_issues: list[str]
    complaint_severity: str
    evidence_confidence: float
    grounded_in_text: bool
    insufficient_text: bool
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DuplicateSignal:
    flagged: bool
    flag: str | None
    matched_image_id: int | None
    matched_report_id: int | None
    exact_duplicate: bool
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PceFraming:
    claim: str | None
    citizen_evidence: str | None
    result: str
    note: str
    claim_marked_false: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WatermarkResult:
    generated: bool
    original_preserved: bool
    original_sha256: str | None
    watermarked_sha256: str | None
    watermark_path: str | None
    note: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CitizenReportRecord:
    citizen_report_id: int
    project_id: int
    scheme_id: str | None
    internal_project_id: str
    satisfaction_rating: int | None
    observation_text: str | None
    issue_category: str | None
    submitted_at: str | None
    image_id: int | None
    submission_status: str
    verification_result: str
    timestamp_status: str
    data_mode: str
    provenance: dict[str, Any]
    location_verification: dict[str, Any]
    analysis: dict[str, Any] | None
    duplicate: dict[str, Any] | None
    watermark: dict[str, Any] | None
    plan_claim_evidence: dict[str, Any] | None
    evidence_ids: list[str]
    rejection_reason: str | None
    reasons: list[str]
    synthetic: bool
    synthetic_badge: str | None
    image_hash: str | None
    image_metadata: dict[str, Any] | None
    thumbnail_data_url: str | None
    original_image_preserved: bool
    privacy: dict[str, Any]
    engine_version: str
    engine_name: str
    governance_note: str
    latitude: float | None = None
    longitude: float | None = None
    location_included: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if not self.location_included:
            payload.pop("latitude", None)
            payload.pop("longitude", None)
        return payload


@dataclass
class CitizenSummary:
    project_id: int
    internal_project_id: str
    scheme_id: str | None
    data_mode: str
    total_submissions: int
    verified_location_submissions: int
    rejected_submissions: int
    inconclusive_submissions: int
    average_satisfaction: float | None
    satisfaction_distribution: dict[str, int]
    recurring_issue_categories: list[dict[str, Any]]
    repeated_complaint_themes: list[str]
    citizen_evidence_confidence: float
    sample_size_status: str
    aggregate_finding: str
    explanation: str
    provenance: dict[str, Any]
    synthetic_badge: str | None
    investigation_priority_unchanged: bool
    evidence_ids: list[str]
    engine_version: str
    engine_name: str
    governance_note: str
    privacy_note: str
    limitations: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
