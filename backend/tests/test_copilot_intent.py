from __future__ import annotations

from app.copilot.intent import parse_intent
from app.copilot.types import CopilotIntent


def test_why_flagged_and_not_flagged_intents() -> None:
    assert parse_intent("Why is this project flagged?") == CopilotIntent.WHY_FLAGGED
    assert parse_intent("Why was this project not flagged?") == CopilotIntent.WHY_NOT_FLAGGED


def test_example_officer_questions() -> None:
    assert parse_intent("What evidence supports the overlap finding?") == CopilotIntent.STRONGEST_EVIDENCE
    assert parse_intent("What information is missing?") == CopilotIntent.MISSING_INFORMATION
    assert parse_intent("Why is Time Intelligence inconclusive?") == CopilotIntent.TIME_INCONCLUSIVE
    assert parse_intent("Show comparable projects.") == CopilotIntent.COMPARABLES
    assert parse_intent("Summarize Plan → Claim → Evidence.") == CopilotIntent.PCE_SUMMARY
    assert parse_intent("What should I inspect next?") == CopilotIntent.INSPECT_NEXT
    assert parse_intent("Show the project's citizen feedback.") == CopilotIntent.CITIZEN
    assert parse_intent("Why can't satellite verification be completed?") == CopilotIntent.SATELLITE
    assert parse_intent("Which signals contributed most to the current investigation priority?") == CopilotIntent.SIGNALS


def test_legal_fraud_question_is_forbidden_intent() -> None:
    assert parse_intent("Is this fraud?") == CopilotIntent.FORBIDDEN_LEGAL


def test_short_follow_up_keeps_previous_intent() -> None:
    assert parse_intent("and overlap?", previous_intent=CopilotIntent.STRONGEST_EVIDENCE) == CopilotIntent.STRONGEST_EVIDENCE
