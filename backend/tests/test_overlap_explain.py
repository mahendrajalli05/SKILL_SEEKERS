from __future__ import annotations

from datetime import date

from app.engines.overlap.explain import why_linked_text, why_not_linked_text
from app.engines.overlap.scoring import score_pair
from app.engines.overlap.text import combine_place_text, constituency_fields, embedding_text, rare_block_tokens
from app.engines.overlap.types import OverlapAssessmentOutcome, OverlapMode, OverlapRecord


def _record(project_id: int, **overrides: object) -> OverlapRecord:
    work = str(overrides.pop("work", "NA - Construction of water tanks"))
    constituency = str(overrides.pop("constituency", "KURNOOL"))
    value, usable, kind, _reason = constituency_fields(constituency)
    village = str(overrides.pop("village", ""))
    return OverlapRecord(
        project_id=project_id,
        internal_project_id=f"internal:synthetic:overlap:{project_id}",
        source_work=work,
        work_description=work,
        embedding_text=embedding_text(work),
        category=str(overrides.pop("category", "Normal/Others")),
        constituency=value,
        constituency_usable=usable,
        constituency_kind=kind,
        state="Andhra Pradesh",
        allocation_amount=overrides.pop("amount", 500_000),  # type: ignore[arg-type]
        recommended_date=overrides.pop("rec_date", date(2023, 6, 1)),  # type: ignore[arg-type]
        village=village,
        place_text=combine_place_text(village=village),
        rare_tokens=rare_block_tokens(work),
    )


def test_why_linked_uses_required_example_shape() -> None:
    left = _record(1)
    right = _record(2, amount=520_000, rec_date=date(2023, 6, 20))
    signals = score_pair(left, right, 0.92)
    text = why_linked_text(signals, mode=OverlapMode.REAL)
    assert "92% semantic similarity" in text
    assert "same constituency" in text
    assert "category" in text
    assert "allocation" in text.casefold()
    assert "45-day" in text or "recommendation" in text
    assert "fraud" not in text.casefold()
    if signals.outcome == OverlapAssessmentOutcome.POTENTIAL_DUPLICATE:
        assert "Potential Duplicate" in text
    else:
        assert "Potential Overlap" in text


def test_why_not_linked_explains_insufficient_or_weak_signals() -> None:
    left = _record(1, work="NA - Construction of water tanks")
    right = _record(2, work="NA - Purchase of ambulance")
    signals = score_pair(left, right, 0.2)
    text = why_not_linked_text(signals, mode=OverlapMode.REAL, candidate_count=1)
    assert "not linked" in text.casefold()
    assert "Evidence Confidence" in text
    assert "fraud" not in text.casefold()
    assert "Geographic evidence unavailable" in text or "unavailable" in text.casefold()
