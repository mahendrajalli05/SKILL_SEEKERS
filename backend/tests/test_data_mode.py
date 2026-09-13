from __future__ import annotations

from app.scope import default_data_mode, resolve_data_mode
from app.search.enrichment_display import SyntheticEnrichmentDisplay, enrichment_for


def test_default_application_mode_is_hybrid() -> None:
    assert default_data_mode() == "HYBRID"
    assert resolve_data_mode(None) == "HYBRID"
    assert resolve_data_mode("real") == "REAL"
    assert resolve_data_mode("HYBRID") == "HYBRID"
    assert resolve_data_mode("hybrid-test") == "HYBRID"


def test_enrichment_display_does_not_invent_rows() -> None:
    missing = enrichment_for("internal:does-not-exist-in-synthetic-layer")
    assert missing is None
    sample = SyntheticEnrichmentDisplay(
        internal_project_id="internal:x",
        implementing_district=None,
        implementing_agency=None,
        vendor_name=None,
        sanction_date=None,
        planned_start_date=None,
        planned_completion_date=None,
        actual_start_date=None,
        actual_completion_date=None,
        expenditure_amount=None,
        latitude=None,
        longitude=None,
        physical_progress_percent=None,
        milestone_number=None,
        milestone_amount=None,
        milestone_total_amount=None,
    )
    payload = sample.as_payload()
    assert payload["label"] == "SYNTHETIC"
    assert payload["implementing_district"] is None
    assert payload["expenditure"] is None
    assert "0" not in str(payload["physical_progress_percent"])
