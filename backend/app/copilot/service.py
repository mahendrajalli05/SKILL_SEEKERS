"""Investigation Copilot V1 orchestration.

Retrieves stored evidence, builds a grounded answer, validates citations,
and never recalculates Cost / Time / Overlap / Compliance / Risk Fusion.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.copilot.answer import build_deterministic_answer
from app.copilot.constants import (
    ENGINE_VERSION,
    GOVERNANCE_NOTE,
    MAX_QUESTION_CHARS,
    SUGGESTED_QUESTIONS,
)
from app.copilot.context import compact_context, data_mode_notice
from app.copilot.errors import CopilotError
from app.copilot.grounding import is_grounded
from app.copilot.guardrails import draft_violates_guardrails, strip_sensitive
from app.copilot.intent import parse_intent
from app.copilot.memory import list_session_turns, new_session_id, persist_turn
from app.copilot.providers import resolve_provider
from app.copilot.retrieval import engines_present, parse_copilot_data_mode, retrieve_bundle
from app.copilot.types import CopilotIntent
from app.logging_config import get_logger
from app.models.project import Project

logger = get_logger("sarvsakshi.copilot")


def _history_payload(turns) -> list[dict[str, str]]:
    return [
        {"question": item.question, "intent": item.intent, "answer": item.answer[:400]}
        for item in turns
    ]


def copilot_context(session: Session, project: Project, data_mode: str | None, session_id: str | None) -> dict:
    mode = parse_copilot_data_mode(data_mode, project)
    bundle = retrieve_bundle(session, project, mode)
    sid = session_id or new_session_id()
    turns = list_session_turns(session, project.id, sid) if session_id else []
    return {
        "project_id": project.id,
        "internal_project_id": bundle.internal_project_id,
        "scheme_id": bundle.scheme_id,
        "data_mode": mode.value,
        "data_mode_notice": data_mode_notice(bundle),
        "engines_present": engines_present(bundle),
        "evidence_count": len(bundle.evidence),
        "suggested_questions": list(SUGGESTED_QUESTIONS),
        "session_id": sid,
        "turns": [
            {
                "question": item.question,
                "answer": item.answer,
                "intent": item.intent,
                "evidence_ids": item.evidence_ids,
                "recommended_action": item.recommended_action,
                "provider": item.provider,
                "created_at": item.created_at,
            }
            for item in turns
        ],
        "limitations": compact_context(bundle, CopilotIntent.GENERAL)["limitations"],
        "governance_note": GOVERNANCE_NOTE,
        "engine_version": ENGINE_VERSION,
        "llm_provider": resolve_provider().name,
    }


def chat(
    session: Session,
    project: Project,
    *,
    question: str,
    data_mode: str | None,
    session_id: str | None,
) -> dict:
    text = (question or "").strip()
    if not text:
        raise CopilotError("A question is required.", code="empty_question", status_code=422)
    if len(text) > MAX_QUESTION_CHARS:
        raise CopilotError("The question is too long.", code="question_too_long", status_code=422)
    mode = parse_copilot_data_mode(data_mode, project)
    sid = session_id or new_session_id()
    turns = list_session_turns(session, project.id, sid)
    previous = None
    if turns and turns[-1].intent:
        try:
            previous = CopilotIntent(turns[-1].intent)
        except ValueError:
            previous = None
    intent = parse_intent(text, previous_intent=previous)
    bundle = retrieve_bundle(session, project, mode, question=text)
    provider = resolve_provider()
    fallback = build_deterministic_answer(bundle, intent)
    try:
        draft = provider.complete(text, bundle, intent, _history_payload(turns))
    except Exception:
        logger.info(
            "copilot_provider_fallback project_id=%s intent=%s provider=%s",
            project.id,
            intent.value,
            provider.name,
        )
        draft = fallback
    if draft_violates_guardrails(draft) or not is_grounded(draft, bundle):
        logger.info(
            "copilot_grounding_fallback project_id=%s intent=%s",
            project.id,
            intent.value,
        )
        draft = fallback
    answer = strip_sensitive(draft.sections.render())
    persist_turn(
        session,
        project_id=project.id,
        session_id=sid,
        question=text,
        answer=answer,
        intent=intent.value,
        data_mode=mode.value,
        evidence_ids=draft.evidence_ids,
        recommended_action=draft.recommended_action.value,
        provider=draft.provider.value if hasattr(draft.provider, "value") else str(draft.provider),
        used_llm=draft.used_llm,
    )
    session.commit()
    logger.info(
        "copilot_chat project_id=%s intent=%s provider=%s evidence_count=%s llm=%s",
        project.id,
        intent.value,
        draft.provider,
        len(draft.evidence_ids),
        draft.used_llm,
    )
    return {
        "project_id": project.id,
        "internal_project_id": bundle.internal_project_id,
        "scheme_id": bundle.scheme_id,
        "session_id": sid,
        "question": text,
        "intent": intent.value,
        "answer": answer,
        "sections": {
            "answer": strip_sensitive(draft.sections.answer),
            "why": strip_sensitive(draft.sections.why),
            "evidence": strip_sensitive(draft.sections.evidence),
            "missing": strip_sensitive(draft.sections.missing),
            "recommended_action": draft.recommended_action.value,
        },
        "evidence_ids": draft.evidence_ids,
        "source_refs": [item.as_dict() for item in draft.source_refs],
        "data_mode": mode.value,
        "data_mode_notice": data_mode_notice(bundle),
        "limitations": [strip_sensitive(item) for item in draft.limitations],
        "recommended_action": draft.recommended_action.value,
        "observed_facts": draft.observed_facts,
        "derived_findings": draft.derived_findings,
        "unavailable": draft.unavailable,
        "insufficient_evidence": draft.insufficient_evidence,
        "hybrid_used": mode.value in {"HYBRID", "SYNTHETIC"} or bundle.is_synthetic,
        "provider": draft.provider.value if hasattr(draft.provider, "value") else str(draft.provider),
        "used_llm": draft.used_llm,
        "governance_note": GOVERNANCE_NOTE,
        "engine_version": ENGINE_VERSION,
    }
