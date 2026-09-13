"""Deterministic evidence-grounded answers for Investigation Copilot V1.

Templates only. Does not recalculate intelligence scores.
"""

from __future__ import annotations

from app.copilot.constants import (
    CITIZEN_LIMITATION,
    CONTEXT_NOT_PROJECT_FACT,
    GPS_UNAVAILABLE,
    INSUFFICIENT_PHRASE,
    ML_NOT_FRAUD_PROBABILITY,
    ML_UNAVAILABLE,
    SATELLITE_UNAVAILABLE,
    TIME_REAL_LIMITATION,
    UNAVAILABLE_PHRASE,
)
from app.copilot.context import data_mode_notice, evidence_by_engine, source_refs_for
from app.copilot.guardrails import legal_refusal_sections
from app.copilot.types import (
    CopilotDraft,
    CopilotIntent,
    CopilotProviderName,
    CopilotRecommendation,
    CopilotSections,
    EvidenceSlice,
    InvestigationBundle,
)
from app.domain.enums import DataMode, RecommendedAction
from app.evidence.adapters.ml import sanitize_ml_text


def _join(parts: list[str], fallback: str) -> str:
    cleaned = [item.strip() for item in parts if item and str(item).strip()]
    return " ".join(cleaned) if cleaned else fallback


def _score_text(item: EvidenceSlice) -> str:
    if item.disposition in {"NOT_ASSESSABLE", "INCONCLUSIVE"} or item.status in {
        "not_assessable",
        "inconclusive",
    }:
        return f"{item.engine}: {item.disposition}"
    if item.score is None:
        return f"{item.engine}: {item.finding}"
    return f"{item.engine} score = {item.score}."


def _map_recommendation(
    bundle: InvestigationBundle,
    *,
    insufficient: bool,
) -> CopilotRecommendation:
    if insufficient:
        return CopilotRecommendation.NEED_MORE_INFORMATION
    action = ""
    if bundle.risk_v2 and bundle.risk_v2.recommended_action:
        action = bundle.risk_v2.recommended_action
    elif bundle.risk and bundle.risk.recommended_action:
        action = bundle.risk.recommended_action
    if action == RecommendedAction.MONITOR.value:
        return CopilotRecommendation.MONITOR
    if action == RecommendedAction.REVIEW.value:
        return CopilotRecommendation.REVIEW
    if action in {RecommendedAction.INSPECT.value, RecommendedAction.INVESTIGATE.value}:
        return CopilotRecommendation.INSPECT
    if action == RecommendedAction.NEED_MORE_INFORMATION.value:
        return CopilotRecommendation.NEED_MORE_INFORMATION
    if not bundle.evidence:
        return CopilotRecommendation.NEED_MORE_INFORMATION
    return CopilotRecommendation.REVIEW


def _missing_lines(bundle: InvestigationBundle) -> list[str]:
    lines: list[str] = []
    if bundle.data_mode == DataMode.REAL:
        for field in bundle.unavailable_fields:
            name = field.get("field")
            reason = field.get("reason")
            if name:
                lines.append(f"{name}: {reason or UNAVAILABLE_PHRASE}")
    engines = {item.engine for item in bundle.evidence}
    for engine, label in (
        ("time", "Time Intelligence"),
        ("satellite", "Satellite evidence"),
        ("geo", "Geospatial evidence"),
        ("citizen", "Citizen evidence"),
        ("milestone", "Milestone evidence"),
        ("graph", "Relationship graph evidence"),
    ):
        if engine not in engines:
            if engine == "time" and bundle.data_mode == DataMode.REAL:
                lines.append(TIME_REAL_LIMITATION)
            elif engine == "satellite":
                lines.append(SATELLITE_UNAVAILABLE)
            elif engine == "geo" and bundle.data_mode == DataMode.REAL:
                lines.append(GPS_UNAVAILABLE)
            else:
                lines.append(f"{label} is not available in the current evidence.")
    for item in bundle.evidence:
        if item.disposition in {"NOT_ASSESSABLE", "INCONCLUSIVE"}:
            lines.append(f"{item.engine}: {item.disposition}. {item.finding}")
    if bundle.pce and bundle.pce.get("missing_information"):
        lines.extend(str(item) for item in bundle.pce["missing_information"])
    unique: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if line in seen:
            continue
        seen.add(line)
        unique.append(line)
    return unique[:12]


def _strongest(bundle: InvestigationBundle) -> list[EvidenceSlice]:
    flagged = [item for item in bundle.evidence if item.disposition == "WHY_FLAGGED"]
    flagged.sort(key=lambda item: (-(item.score or -1), item.evidence_id))
    if flagged:
        return flagged[:4]
    scored = [item for item in bundle.evidence if item.score is not None]
    scored.sort(key=lambda item: (-float(item.score or 0), item.evidence_id))
    return scored[:4] or bundle.evidence[:4]


def _ids(items: list[EvidenceSlice], extra: list[str] | None = None) -> list[str]:
    ids = [item.evidence_id for item in items]
    if extra:
        ids.extend(extra)
    unique: list[str] = []
    seen: set[str] = set()
    for item in ids:
        if not item or item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _observed(bundle: InvestigationBundle) -> list[str]:
    lines = []
    if bundle.allocation_amount is not None:
        lines.append(f"Recorded allocation amount is {bundle.allocation_amount}.")
    if bundle.work_description:
        lines.append(f"Work description: {bundle.work_description}.")
    if bundle.constituency:
        lines.append(f"Constituency: {bundle.constituency}.")
    if bundle.status:
        lines.append(f"Observed status: {bundle.status}.")
    return lines


def _derived(bundle: InvestigationBundle) -> list[str]:
    lines = []
    if bundle.risk and bundle.risk.explanation_type:
        lines.append(
            f"Investigation Priority is {bundle.risk.investigation_priority} "
            f"({bundle.risk.explanation_type})."
        )
    for item in bundle.evidence:
        lines.append(item.finding)
    return lines[:8]


def _draft(
    bundle: InvestigationBundle,
    sections: CopilotSections,
    evidence_ids: list[str],
    *,
    insufficient: bool = False,
    extra_limitations: list[str] | None = None,
) -> CopilotDraft:
    action = _map_recommendation(bundle, insufficient=insufficient)
    sections.recommended_action = action.value
    limitations = [data_mode_notice(bundle)]
    if extra_limitations:
        limitations.extend(extra_limitations)
    if insufficient:
        limitations.append(INSUFFICIENT_PHRASE)
    return CopilotDraft(
        sections=sections,
        evidence_ids=evidence_ids,
        source_refs=source_refs_for(bundle, evidence_ids),
        limitations=limitations,
        recommended_action=action,
        observed_facts=_observed(bundle),
        derived_findings=_derived(bundle),
        unavailable=_missing_lines(bundle),
        insufficient_evidence=insufficient,
        provider=CopilotProviderName.DETERMINISTIC,
        used_llm=False,
    )


def _why_flagged(bundle: InvestigationBundle) -> CopilotDraft:
    risk = bundle.risk
    flagged = [item for item in bundle.evidence if item.disposition == "WHY_FLAGGED"]
    contributing = []
    if risk:
        contributing = [
            item
            for item in risk.contributing
            if item.get("flagged") or str(item.get("disposition")) == "WHY_FLAGGED"
        ]
    if (risk and risk.explanation_type in {"WHY_NOT_FLAGGED", "INSUFFICIENT_EVIDENCE", "INCONCLUSIVE"}) and not flagged:
        return _why_not_flagged(bundle)
    if not flagged and not contributing:
        return _draft(
            bundle,
            CopilotSections(
                answer=INSUFFICIENT_PHRASE,
                why="No stored WHY_FLAGGED evidence is available for this project in the current data mode.",
                evidence=UNAVAILABLE_PHRASE,
                missing=_join(_missing_lines(bundle), UNAVAILABLE_PHRASE),
                recommended_action="",
            ),
            _ids(bundle.evidence, risk.evidence_ids if risk else None),
            insufficient=True,
        )
    scores = [_score_text(item) for item in flagged]
    if contributing:
        names = [
            f"{item.get('display_name') or item.get('signal_id')} contribution {item.get('contribution')}"
            for item in contributing
        ]
        why = "Flagged fused signals: " + "; ".join(names) + "."
    else:
        why = "Stored engine findings with disposition WHY_FLAGGED are the basis of this answer."
    priority = risk.investigation_priority if risk else None
    answer = (
        f"Investigation Priority is elevated ({priority})."
        if priority and priority >= 25
        else "This project has stored WHY_FLAGGED evidence."
    )
    if risk and risk.explanation:
        why = f"{why} {risk.explanation}"
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why=why,
            evidence=_join(scores + [item.finding for item in flagged], UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(flagged, risk.evidence_ids if risk else None),
    )


def _why_not_flagged(bundle: InvestigationBundle) -> CopilotDraft:
    risk = bundle.risk
    not_flagged = [item for item in bundle.evidence if item.disposition == "WHY_NOT_FLAGGED"]
    flagged = [item for item in bundle.evidence if item.disposition == "WHY_FLAGGED"]
    if flagged and risk and risk.explanation_type == "WHY_FLAGGED":
        return _draft(
            bundle,
            CopilotSections(
                answer="This project currently has WHY_FLAGGED evidence, so it is not classified as not flagged.",
                why=risk.explanation or "Stored fusion explanation type is WHY_FLAGGED.",
                evidence=_join([_score_text(item) for item in flagged], UNAVAILABLE_PHRASE),
                missing=_join(_missing_lines(bundle), UNAVAILABLE_PHRASE),
                recommended_action="",
            ),
            _ids(flagged, risk.evidence_ids if risk else None),
        )
    if not bundle.evidence and (not risk or risk.explanation_type == "INSUFFICIENT_EVIDENCE"):
        return _draft(
            bundle,
            CopilotSections(
                answer="The project is not flagged because fused evidence is insufficient.",
                why=(risk.explanation if risk and risk.explanation else INSUFFICIENT_PHRASE),
                evidence=UNAVAILABLE_PHRASE,
                missing=_join(_missing_lines(bundle), UNAVAILABLE_PHRASE),
                recommended_action="",
            ),
            risk.evidence_ids if risk else [],
            insufficient=True,
        )
    why = risk.explanation if risk and risk.explanation else "Stored findings do not currently support a WHY_FLAGGED disposition."
    return _draft(
        bundle,
        CopilotSections(
            answer="This project is not flagged on the stored fused evidence.",
            why=why,
            evidence=_join([_score_text(item) for item in not_flagged or bundle.evidence], UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(not_flagged or bundle.evidence, risk.evidence_ids if risk else None),
    )


def _strongest_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = _strongest(bundle)
    if not items:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No stored Evidence Objects are available.",
                evidence=UNAVAILABLE_PHRASE,
                missing=_join(_missing_lines(bundle), UNAVAILABLE_PHRASE),
                recommended_action="",
            ),
            [],
            insufficient=True,
        )
    return _draft(
        bundle,
        CopilotSections(
            answer="The strongest stored findings are listed from Evidence Objects; they are not a legal conclusion.",
            why=_join([item.finding for item in items], UNAVAILABLE_PHRASE),
            evidence=_join(
                [f"{item.evidence_id}: {_score_text(item)} {item.explanation}" for item in items],
                UNAVAILABLE_PHRASE,
            ),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(items),
    )


def _missing_answer(bundle: InvestigationBundle) -> CopilotDraft:
    missing = _missing_lines(bundle)
    if bundle.lifecycle:
        missing = list(missing) + [
            f"Lifecycle pending: {stage}" for stage in (bundle.lifecycle.pending_stages or [])[:6]
        ]
        missing.extend(bundle.lifecycle.missing[:6])
    insufficient = not bundle.evidence
    return _draft(
        bundle,
        CopilotSections(
            answer="Missing or not-assessable fields from the current evidence are listed below.",
            why="The Copilot reports stored availability only and does not invent government values.",
            evidence=_join([item.evidence_id for item in bundle.evidence], UNAVAILABLE_PHRASE),
            missing=_join(missing, UNAVAILABLE_PHRASE),
            recommended_action="",
        ),
        _ids(bundle.evidence, bundle.risk.evidence_ids if bundle.risk else None),
        insufficient=insufficient,
    )


def _time_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "time")
    if bundle.data_mode == DataMode.REAL:
        extra = [TIME_REAL_LIMITATION]
        finding = TIME_REAL_LIMITATION
        if items:
            finding = f"{TIME_REAL_LIMITATION} Stored Time Intelligence disposition is {items[0].disposition}."
        return _draft(
            bundle,
            CopilotSections(
                answer=finding,
                why="REAL mode uses recommendation date and observed status only. Verified execution dates are not in the extract.",
                evidence=_join([f"{item.evidence_id}: {item.explanation}" for item in items], UNAVAILABLE_PHRASE),
                missing=TIME_REAL_LIMITATION,
                recommended_action="",
            ),
            _ids(items),
            extra_limitations=extra,
        )
    if not items:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No Time Intelligence Evidence Object is stored for this data mode.",
                evidence=UNAVAILABLE_PHRASE,
                missing=UNAVAILABLE_PHRASE,
                recommended_action="",
            ),
            [],
            insufficient=True,
        )
    item = items[0]
    return _draft(
        bundle,
        CopilotSections(
            answer=item.finding,
            why=item.explanation,
            evidence=f"{item.evidence_id}: {_score_text(item)}",
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(items),
        extra_limitations=[data_mode_notice(bundle)] if bundle.data_mode != DataMode.REAL else None,
    )


def _comparables_answer(bundle: InvestigationBundle) -> CopilotDraft:
    cost = evidence_by_engine(bundle, "cost")
    overlap = evidence_by_engine(bundle, "overlap")
    lines: list[str] = []
    ids = _ids(cost + overlap)
    for item in cost:
        if not item.comparables:
            lines.append(f"{item.evidence_id}: comparable projects are not stored on this Cost evidence object.")
            continue
        for comparable in item.comparables[:8]:
            if not isinstance(comparable, dict):
                continue
            ident = comparable.get("internal_project_id") or comparable.get("project_id")
            amount = comparable.get("allocation_amount")
            lines.append(f"Cost comparable {ident} allocation {amount}.")
    for item in overlap:
        if not item.comparables:
            continue
        for match in item.comparables[:8]:
            if not isinstance(match, dict):
                continue
            ident = match.get("linked_internal_project_id") or match.get("linked_project_id")
            score = match.get("overall_overlap_score")
            lines.append(f"Overlap match {ident} overall score {score}.")
    if not lines:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No comparable project identifiers are stored on Cost or Overlap evidence.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Comparable project lists were not persisted for this project.",
                recommended_action="",
            ),
            ids,
            insufficient=True,
        )
    return _draft(
        bundle,
        CopilotSections(
            answer="Comparable works are taken from stored Cost and Overlap Evidence Objects.",
            why="The Copilot does not recompute peer groups. It reports identifiers already stored by those engines.",
            evidence=_join(lines, UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        ids,
    )


def _pce_answer(bundle: InvestigationBundle) -> CopilotDraft:
    pce = bundle.pce
    if not pce:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No Plan → Claim → Evidence comparison is stored for this project.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Plan, claim, or supporting evidence has not been recorded.",
                recommended_action="",
            ),
            _ids(evidence_by_engine(bundle, "pce")),
            insufficient=True,
        )
    overall = pce.get("overall_result") or "INCONCLUSIVE"
    mismatches = pce.get("mismatches") or []
    conflict = ""
    if mismatches:
        conflict = " Conflicting stored comparisons: " + "; ".join(
            f"{item.get('field')}={item.get('status')}" for item in mismatches[:6]
        )
    return _draft(
        bundle,
        CopilotSections(
            answer=f"Plan → Claim → Evidence overall result is {overall}.",
            why=(pce.get("explanation") or "") + conflict,
            evidence=_join(
                [str(item) for item in (pce.get("plan_findings") or [])[:4]]
                + [str(item) for item in (pce.get("claim_findings") or [])[:4]]
                + [str(item) for item in (pce.get("evidence_findings") or [])[:4]],
                UNAVAILABLE_PHRASE,
            ),
            missing=_join(list(pce.get("missing_information") or []) or _missing_lines(bundle), UNAVAILABLE_PHRASE),
            recommended_action="",
        ),
        list(pce.get("evidence_ids") or []) + _ids(evidence_by_engine(bundle, "pce")),
        extra_limitations=[data_mode_notice(bundle)] if bundle.data_mode != DataMode.REAL else None,
    )


def _inspect_answer(bundle: InvestigationBundle) -> CopilotDraft:
    missing = _missing_lines(bundle)
    flagged = [item for item in bundle.evidence if item.disposition == "WHY_FLAGGED"]
    action = _map_recommendation(bundle, insufficient=not bundle.evidence)
    why_parts = [item.finding for item in flagged[:4]]
    if bundle.milestones and bundle.milestones.get("current_recommendation"):
        why_parts.append(
            f"Milestone Advisor last recommendation is {bundle.milestones['current_recommendation']} (officer decides)."
        )
    return _draft(
        bundle,
        CopilotSections(
            answer=f"Recommended next action is {action.value}. This is not a sanction or payment instruction.",
            why=_join(why_parts, "Use stored Investigation Priority and missing evidence to decide what to inspect."),
            evidence=_join([_score_text(item) for item in flagged or bundle.evidence[:4]], UNAVAILABLE_PHRASE),
            missing=_join(missing, UNAVAILABLE_PHRASE),
            recommended_action="",
        ),
        _ids(flagged or bundle.evidence, bundle.risk.evidence_ids if bundle.risk else None),
        insufficient=not bundle.evidence,
    )


def _compliance_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "compliance")
    if not items:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No Compliance Evidence Object is stored.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Compliance rules were not assessed or the result was not persisted.",
                recommended_action="",
            ),
            [],
            insufficient=True,
        )
    item = items[0]
    rules = item.rule_ids or []
    refs = item.guideline_refs or []
    return _draft(
        bundle,
        CopilotSections(
            answer=item.finding,
            why=(
                f"{item.explanation} Compliance is a deterministic rule engine, not a machine-learning model. "
                f"Triggered or referenced rule IDs: {', '.join(rules) if rules else 'none stored'}."
            ),
            evidence=f"{item.evidence_id}: {item.disposition}. Guideline refs: {', '.join(refs) if refs else 'none stored'}.",
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(items),
    )


def _citizen_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "citizen")
    summary = bundle.citizen_summary
    reports = bundle.citizen_reports
    total = int((summary or {}).get("total_submissions") or 0)
    if not items and not reports and total == 0:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No Jan-Sakshi citizen reports are stored for this project.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Citizen field evidence has not been submitted.",
                recommended_action="",
            ),
            [],
            insufficient=True,
            extra_limitations=[CITIZEN_LIMITATION],
        )
    finding = summary.get("aggregate_finding") if summary else None
    explanation = summary.get("explanation") if summary else CITIZEN_LIMITATION
    snippets = [
        f"Report {item.get('citizen_report_id')}: rating {item.get('satisfaction_rating')}; "
        f"{(item.get('observation_text') or 'no observation text')[:180]}"
        for item in reports[:5]
    ]
    ids = list((summary or {}).get("evidence_ids") or []) + _ids(items)
    for report in reports:
        ids.extend(str(value) for value in (report.get("evidence_ids") or []))
    return _draft(
        bundle,
        CopilotSections(
            answer=str(finding or "Citizen reports are stored as supporting evidence only."),
            why=f"{explanation} {CITIZEN_LIMITATION}",
            evidence=_join(snippets or [item.finding for item in items], UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        ids,
        extra_limitations=[CITIZEN_LIMITATION],
    )


def _fact_value(item: EvidenceSlice, key: str) -> str | None:
    for fact in [*item.facts_derived, *item.facts_observed]:
        if fact.get("key") != key:
            continue
        value = fact.get("value")
        if value is None or value == "":
            return None
        return str(value)
    return None


def _ml_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "ml")
    extra = [ML_NOT_FRAUD_PROBABILITY]
    if not items:
        return _draft(
            bundle,
            CopilotSections(
                answer=ML_UNAVAILABLE,
                why="ML evidence is created from a stored Isolation Forest prediction and is not invented.",
                evidence=UNAVAILABLE_PHRASE,
                missing=ML_UNAVAILABLE,
                recommended_action="",
            ),
            [],
            insufficient=True,
            extra_limitations=extra,
        )
    latest = items[-1]
    model_name = _fact_value(latest, "model_name") or "unknown model"
    model_version = _fact_value(latest, "model_version") or latest.engine_version
    score = latest.score
    score_text = "INCONCLUSIVE" if score is None else f"{score}/100"
    available = _fact_value(latest, "feature_availability") or "stored feature availability"
    answer = (
        f"Stored ML evidence is an unsupervised anomaly signal from {model_name} "
        f"(version {model_version}). ml_anomaly_score = {score_text}. "
        "This is not fused into Investigation Priority. "
        + ML_NOT_FRAUD_PROBABILITY
    )
    why = sanitize_ml_text(latest.explanation or "")
    if not why:
        why = (
            "The observed feature pattern is unusual relative to the reference "
            "distribution only when an elevated anomaly signal is stored."
        )
    evidence = _join(
        [
            f"{item.evidence_id}: model { _fact_value(item, 'model_name') or item.engine_version }; "
            f"score {item.score if item.score is not None else item.disposition}; "
            f"data_mode {item.data_mode}"
            for item in items
        ],
        UNAVAILABLE_PHRASE,
    )
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why=why,
            evidence=evidence,
            missing=_join(_missing_lines(bundle), f"Feature availability: {available}"),
            recommended_action="",
        ),
        _ids(items),
        extra_limitations=extra,
    )


def _context_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "context")
    extra = [CONTEXT_NOT_PROJECT_FACT]
    if not items:
        return _draft(
            bundle,
            CopilotSections(
                answer=(
                    "No stored contextual Evidence Object is available for this project. "
                    + CONTEXT_NOT_PROJECT_FACT
                ),
                why="Contextual indicators are retrieved from the source registry and snapshots, not invented.",
                evidence=UNAVAILABLE_PHRASE,
                missing="External context has not been persisted for this project yet.",
                recommended_action="",
            ),
            [],
            insufficient=True,
            extra_limitations=extra,
        )
    lines = []
    years = []
    sources = []
    for item in items:
        lines.append(f"{item.signal_type}: {item.finding}")
        for fact in item.facts_observed + item.facts_derived:
            if fact.get("key") == "reference_year" and fact.get("value") not in (None, ""):
                years.append(str(fact.get("value")))
            if fact.get("key") == "indicator":
                continue
        sources.append(item.evidence_id)
    answer = (
        "External context available for this project is listed below. "
        + CONTEXT_NOT_PROJECT_FACT
        + " "
        + _join(lines, "No contextual indicators were stored.")
    )
    year_text = ", ".join(sorted(set(years))) if years else "not stored as a reference year"
    why = (
        f"Development-indicator reference year(s) in stored facts: {year_text}. "
        "A source URL or publisher, where stored, is cited on the Evidence Object. "
        "This is not project-specific evidence such as expenditure, beneficiaries, or site inspection."
    )
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why=why,
            evidence=_join(sources, UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "Unavailable contextual indicators remain unavailable, not zero."),
            recommended_action="",
        ),
        _ids(items),
        extra_limitations=extra,
    )


def _ml_fraud_clarification(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "ml")
    score_line = "No stored ML anomaly score is present."
    evidence_ids = _ids(items)
    if items:
        latest = items[-1]
        if latest.score is None:
            score_line = (
                f"Stored ML evidence {latest.evidence_id} is {latest.disposition}; "
                "no ml_anomaly_score was produced."
            )
        else:
            score_line = (
                f"Stored ml_anomaly_score for {latest.evidence_id} is {latest.score}/100 "
                f"from model {_fact_value(latest, 'model_name') or 'unknown'} "
                f"version {_fact_value(latest, 'model_version') or latest.engine_version}."
            )
    return _draft(
        bundle,
        CopilotSections(
            answer=ML_NOT_FRAUD_PROBABILITY,
            why=(
                "ml_anomaly_score measures unusualness versus the training distribution. "
                "It does not become fraud, a wrongdoing probability, a legal conclusion, "
                "or confirmed misconduct. Evidence confidence is a separate sufficiency "
                "measure. "
                + score_line
            ),
            evidence=_join([item.evidence_id for item in items], "No ML Evidence Object is stored."),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        evidence_ids,
        extra_limitations=[ML_NOT_FRAUD_PROBABILITY],
        insufficient=not items,
    )


def _engine_topic_answer(
    bundle: InvestigationBundle,
    engine: str,
    *,
    empty_why: str,
    extra_limitations: list[str] | None = None,
) -> CopilotDraft:
    items = evidence_by_engine(bundle, engine)
    if not items:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why=empty_why,
                evidence=UNAVAILABLE_PHRASE,
                missing=empty_why,
                recommended_action="",
            ),
            [],
            insufficient=True,
            extra_limitations=extra_limitations,
        )
    return _draft(
        bundle,
        CopilotSections(
            answer=items[0].finding,
            why=items[0].explanation,
            evidence=_join([f"{item.evidence_id}: {_score_text(item)}" for item in items], UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(items),
        extra_limitations=extra_limitations,
    )


def _signals_answer(bundle: InvestigationBundle) -> CopilotDraft:
    risk_v2 = bundle.risk_v2
    risk = bundle.risk
    if risk_v2:
        contributing = sorted(
            risk_v2.contributing,
            key=lambda item: (-float(item.get("effective_contribution") or 0), str(item.get("group_id"))),
        )
        lines = [
            f"{item.get('display_name') or item.get('group_id')}: raw {item.get('raw_evidence_score')}, "
            f"confidence {item.get('confidence')}, effective {item.get('effective_contribution')}, "
            f"evidence {', '.join(item.get('evidence_ids') or [])}"
            for item in contributing
        ]
        if not lines:
            lines = ["No assessable V2 evidence group currently contributes to Investigation Priority."]
        return _draft(
            bundle,
            CopilotSections(
                answer=(
                    f"Risk Fusion V2 Investigation Priority is {risk_v2.investigation_priority}/100. "
                    f"Evidence Confidence is {risk_v2.evidence_confidence}/100. "
                    "This is not a fraud probability."
                ),
                why=risk_v2.explanation or "Stored Risk Fusion V2 result.",
                evidence=_join(lines, UNAVAILABLE_PHRASE),
                missing=_join(
                    [
                        f"{item.get('display_name')}: {item.get('unavailable_reason') or item.get('state')}"
                        for item in risk_v2.unavailable
                    ],
                    "No unavailable V2 groups were listed.",
                ),
                recommended_action="",
            ),
            list(risk_v2.evidence_ids),
        )
    if not risk:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No fused Investigation Priority snapshot is available.",
                evidence=UNAVAILABLE_PHRASE,
                missing=UNAVAILABLE_PHRASE,
                recommended_action="",
            ),
            _ids(bundle.evidence),
            insufficient=True,
        )
    contributing = sorted(
        risk.contributing,
        key=lambda item: (-float(item.get("contribution") or 0), str(item.get("signal_id"))),
    )
    lines = [
        f"{item.get('display_name') or item.get('signal_id')}: score {item.get('risk_score')}, "
        f"contribution {item.get('contribution')}, evidence {item.get('evidence_id')}"
        for item in contributing
        if item.get("contribution")
    ]
    if not lines:
        lines = ["No assessable fused signal currently contributes to Investigation Priority."]
    return _draft(
        bundle,
        CopilotSections(
            answer=(
                f"Investigation Priority is {risk.investigation_priority} "
                f"(display 0–100). Evidence Confidence is {risk.evidence_confidence}. "
                "This is not a fraud probability."
            ),
            why=risk.explanation or "Stored Risk Fusion V1.1 result.",
            evidence=_join(lines, UNAVAILABLE_PHRASE),
            missing=_join(
                [
                    f"{item.get('display_name')}: {item.get('unavailable_reason') or item.get('state')}"
                    for item in risk.unavailable
                ],
                UNAVAILABLE_PHRASE,
            ),
            recommended_action="",
        ),
        list(risk.evidence_ids),
    )


def _v2_contribution_answer(bundle: InvestigationBundle) -> CopilotDraft:
    risk_v2 = bundle.risk_v2
    if not risk_v2:
        return _signals_answer(bundle)
    ranked = sorted(
        risk_v2.contributing,
        key=lambda item: (-float(item.get("effective_contribution") or 0), str(item.get("group_id"))),
    )
    if not ranked:
        return _draft(
            bundle,
            CopilotSections(
                answer="No assessable V2 evidence group currently contributes.",
                why=risk_v2.explanation or UNAVAILABLE_PHRASE,
                evidence=UNAVAILABLE_PHRASE,
                missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], UNAVAILABLE_PHRASE),
                recommended_action="",
            ),
            list(risk_v2.evidence_ids),
            insufficient=True,
        )
    top = ranked[0]
    lines = [
        f"{item.get('display_name')}: effective contribution {item.get('effective_contribution')} "
        f"(raw {item.get('raw_evidence_score')}, correlation keep {item.get('correlation_factor')})"
        for item in ranked[:5]
    ]
    return _draft(
        bundle,
        CopilotSections(
            answer=(
                f"{top.get('display_name')} contributed most to the V2 Investigation Priority "
                f"({risk_v2.investigation_priority}/100). This is not a fraud finding."
            ),
            why=_join(lines, UNAVAILABLE_PHRASE),
            evidence=_join(
                [", ".join(item.get("evidence_ids") or []) for item in ranked[:5]],
                UNAVAILABLE_PHRASE,
            ),
            missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], "No unavailable groups."),
            recommended_action="",
        ),
        list(risk_v2.evidence_ids),
    )


def _v2_correlated_answer(bundle: InvestigationBundle) -> CopilotDraft:
    risk_v2 = bundle.risk_v2
    if not risk_v2:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No Risk Fusion V2 snapshot is available to explain correlated evidence.",
                evidence=UNAVAILABLE_PHRASE,
                missing=UNAVAILABLE_PHRASE,
                recommended_action="",
            ),
            _ids(bundle.evidence),
            insufficient=True,
        )
    discounted = risk_v2.discounted
    if not discounted:
        return _draft(
            bundle,
            CopilotSections(
                answer="No correlated evidence was discounted in the current V2 result.",
                why="Independent groups were treated as independent corroboration.",
                evidence=_join(
                    [str(item.get("display_name")) for item in risk_v2.independent],
                    "No independent contributing groups.",
                ),
                missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], "None listed."),
                recommended_action="",
            ),
            list(risk_v2.evidence_ids),
        )
    lines = [
        f"{item.get('display_name')}: keep {item.get('correlation_factor')}. {item.get('correlation_reason')}"
        for item in discounted
    ]
    return _draft(
        bundle,
        CopilotSections(
            answer="Correlated evidence was discounted so the same underlying signal is not counted twice.",
            why=_join(lines, UNAVAILABLE_PHRASE),
            evidence=_join(
                [", ".join(item.get("evidence_ids") or []) for item in discounted],
                UNAVAILABLE_PHRASE,
            ),
            missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], "None listed."),
            recommended_action="",
        ),
        list(risk_v2.evidence_ids),
    )


def _v2_conflict_answer(bundle: InvestigationBundle) -> CopilotDraft:
    risk_v2 = bundle.risk_v2
    if not risk_v2:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No Risk Fusion V2 snapshot is available to explain conflicting evidence.",
                evidence=UNAVAILABLE_PHRASE,
                missing=UNAVAILABLE_PHRASE,
                recommended_action="",
            ),
            _ids(bundle.evidence),
            insufficient=True,
        )
    conflicts = risk_v2.conflicting
    if not conflicts:
        return _draft(
            bundle,
            CopilotSections(
                answer="No conflicting V2 evidence groups were recorded for this project.",
                why=risk_v2.explanation or "V2 did not return CONFLICTING_EVIDENCE.",
                evidence=_join(
                    [str(item.get("display_name")) for item in risk_v2.contributing],
                    UNAVAILABLE_PHRASE,
                ),
                missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], "None listed."),
                recommended_action="",
            ),
            list(risk_v2.evidence_ids),
        )
    lines = [str(item.get("summary") or item) for item in conflicts]
    return _draft(
        bundle,
        CopilotSections(
            answer="Evidence sources disagree. V2 returns CONFLICTING_EVIDENCE and does not force a single conclusion.",
            why=_join(lines, UNAVAILABLE_PHRASE),
            evidence=_join(lines, UNAVAILABLE_PHRASE),
            missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], "None listed."),
            recommended_action="",
        ),
        list(risk_v2.evidence_ids),
    )


def _v2_score_change_answer(bundle: InvestigationBundle) -> CopilotDraft:
    risk_v2 = bundle.risk_v2
    risk = bundle.risk
    if not risk_v2:
        return _signals_answer(bundle)
    v1 = risk.investigation_priority if risk else None
    v2 = risk_v2.investigation_priority
    if v1 is None:
        why = "No stored V1.1 Investigation Priority is available for comparison."
    elif v2 is not None and v2 > v1:
        why = (
            f"V2 Investigation Priority ({v2}) is higher than V1.1 ({v1}) because V2 consumes "
            "additional evidence groups and does not silently renormalize missing signals. "
            "Top V2 contributions are listed."
        )
    elif v2 is not None and v2 < v1:
        why = (
            f"V2 Investigation Priority ({v2}) is lower than V1.1 ({v1}) because V2 applies "
            "correlation discounts and does not rescale missing groups onto 0–100."
        )
    else:
        why = f"V2 Investigation Priority ({v2}) matches the stored V1.1 display for this project."
    ranked = sorted(
        risk_v2.contributing,
        key=lambda item: (-float(item.get("effective_contribution") or 0), str(item.get("group_id"))),
    )
    lines = [
        f"{item.get('display_name')}: effective {item.get('effective_contribution')}"
        for item in ranked[:5]
    ]
    return _draft(
        bundle,
        CopilotSections(
            answer=(
                f"Risk Fusion V2 Investigation Priority is {v2}/100 "
                f"(V1.1 was {v1 if v1 is not None else 'not stored'}). "
                "This is not a fraud probability."
            ),
            why=why + " " + _join(lines, ""),
            evidence=_join(list(risk_v2.evidence_ids), UNAVAILABLE_PHRASE),
            missing=_join([str(item.get("display_name")) for item in risk_v2.unavailable], "None listed."),
            recommended_action="",
        ),
        list(risk_v2.evidence_ids),
    )


def _overview_answer(bundle: InvestigationBundle) -> CopilotDraft:
    risk = bundle.risk
    answer = (
        f"Project {bundle.scheme_id or bundle.internal_project_id} is a stored MPLADS work "
        f"in {bundle.constituency or 'an unspecified constituency'}."
    )
    if bundle.lifecycle and bundle.lifecycle.lifecycle_state:
        answer += (
            f" SARVSAKSHI workflow state is {bundle.lifecycle.lifecycle_state}. "
            f"Source status is {bundle.lifecycle.source_status or 'unavailable'}. "
            f"Current stage is {bundle.lifecycle.current_stage}."
        )
    if risk:
        answer += (
            f" Investigation Priority is {risk.investigation_priority} "
            f"({risk.explanation_type})."
        )
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why=risk.explanation if risk and risk.explanation else "Overview is taken from stored project fields and evidence.",
            evidence=_join([_score_text(item) for item in bundle.evidence[:6]], UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), UNAVAILABLE_PHRASE),
            recommended_action="",
        ),
        _ids(bundle.evidence, risk.evidence_ids if risk else None),
        insufficient=not bundle.evidence,
    )


def _lifecycle_where_answer(bundle: InvestigationBundle) -> CopilotDraft:
    life = bundle.lifecycle
    if life is None:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="Lifecycle orchestration context is not available for this project.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Lifecycle state could not be retrieved.",
                recommended_action="",
            ),
            [],
            insufficient=True,
        )
    answer = (
        f"SARVSAKSHI workflow state is {life.lifecycle_state}. "
        f"Source status is {life.source_status or 'unavailable'}. "
        f"Current stage is {life.current_stage}."
    )
    if life.planning_state:
        answer += f" FUTURE planning state is {life.planning_state} (not a sanction)."
    if life.recommendation:
        answer += f" Recommendation: {life.recommendation}."
    pending = ", ".join(life.pending_stages[:8]) or "none listed"
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why=life.explanation or "Lifecycle is derived from observed STATUS plus stored evidence and officer actions.",
            evidence=_join(
                [f"{item.get('stage')}: {item.get('status')}" for item in life.timeline[:12]],
                UNAVAILABLE_PHRASE,
            ),
            missing=_join(life.missing or _missing_lines(bundle), UNAVAILABLE_PHRASE),
            recommended_action="",
        ),
        _ids(bundle.evidence),
        extra_limitations=["SARVSAKSHI workflow state is not an official MPLADS status."],
    )


def _lifecycle_remaining_answer(bundle: InvestigationBundle) -> CopilotDraft:
    life = bundle.lifecycle
    pending = (life.pending_stages if life else []) or []
    missing = (life.missing if life else _missing_lines(bundle)) or _missing_lines(bundle)
    answer = (
        f"Remaining workflow stages: {', '.join(pending) or 'none pending'}. "
        "Unavailable steps are NOT AVAILABLE or INCONCLUSIVE, not suspicious."
    )
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why="Lifecycle orchestration lists stored evidence gaps only and does not invent government values.",
            evidence=_join([item.evidence_id for item in bundle.evidence[:8]], UNAVAILABLE_PHRASE),
            missing=_join(list(missing), UNAVAILABLE_PHRASE),
            recommended_action="",
        ),
        _ids(bundle.evidence),
    )


def _lifecycle_last_milestone_answer(bundle: InvestigationBundle) -> CopilotDraft:
    life = bundle.lifecycle
    last = life.last_milestone_decision if life else None
    rec = (bundle.milestones or {}).get("current_recommendation") if bundle.milestones else None
    if not last and not rec:
        return _draft(
            bundle,
            CopilotSections(
                answer="No milestone officer decision is stored for this project.",
                why="Milestone Advisor records are read only. Absence is not treated as suspicious.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Last milestone decision is not available.",
                recommended_action="",
            ),
            [],
            insufficient=True,
        )
    answer = (
        f"The last milestone officer decision is {last or rec}. "
        "This does not release funds and is not a PFMS payment."
    )
    return _draft(
        bundle,
        CopilotSections(
            answer=answer,
            why="Milestone Advisor officer actions are audited and do not change Investigation Priority.",
            evidence=_join(
                [f"{item.get('milestone_name')}: {item.get('officer_action') or item.get('recommendation')}"
                 for item in (bundle.milestones or {}).get("items") or []],
                last or rec or UNAVAILABLE_PHRASE,
            ),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(evidence_by_engine(bundle, "milestone")),
    )


def _milestone_answer(bundle: InvestigationBundle) -> CopilotDraft:
    items = evidence_by_engine(bundle, "milestone")
    milestones = bundle.milestones
    if not items and not milestones:
        return _draft(
            bundle,
            CopilotSections(
                answer=UNAVAILABLE_PHRASE,
                why="No milestone records are stored.",
                evidence=UNAVAILABLE_PHRASE,
                missing="Milestone Advisor has not recorded a milestone for this project.",
                recommended_action="",
            ),
            [],
            insufficient=True,
        )
    rec = (milestones or {}).get("current_recommendation")
    lines = [
        f"{item.get('milestone_name')}: {item.get('recommendation') or item.get('status')}"
        for item in (milestones or {}).get("items") or []
    ]
    return _draft(
        bundle,
        CopilotSections(
            answer=f"Milestone Advisor recommendation is {rec or (items[0].finding if items else UNAVAILABLE_PHRASE)}. This does not release funds.",
            why=_join(lines or [item.explanation for item in items], "Stored milestone workflow only."),
            evidence=_join([item.evidence_id for item in items] or lines, UNAVAILABLE_PHRASE),
            missing=_join(_missing_lines(bundle), "No additional missing fields were listed."),
            recommended_action="",
        ),
        _ids(items),
    )


def build_deterministic_answer(bundle: InvestigationBundle, intent: CopilotIntent) -> CopilotDraft:
    if intent == CopilotIntent.FORBIDDEN_LEGAL:
        return CopilotDraft(
            sections=legal_refusal_sections(),
            evidence_ids=[],
            source_refs=source_refs_for(bundle, []),
            limitations=[data_mode_notice(bundle)],
            recommended_action=CopilotRecommendation.NEED_MORE_INFORMATION,
            observed_facts=_observed(bundle),
            derived_findings=[],
            unavailable=_missing_lines(bundle),
            insufficient_evidence=False,
            provider=CopilotProviderName.DETERMINISTIC,
        )
    dispatch = {
        CopilotIntent.WHY_FLAGGED: _why_flagged,
        CopilotIntent.WHY_NOT_FLAGGED: _why_not_flagged,
        CopilotIntent.STRONGEST_EVIDENCE: _strongest_answer,
        CopilotIntent.MISSING_INFORMATION: _missing_answer,
        CopilotIntent.TIME_INCONCLUSIVE: _time_answer,
        CopilotIntent.COMPARABLES: _comparables_answer,
        CopilotIntent.PCE_SUMMARY: _pce_answer,
        CopilotIntent.INSPECT_NEXT: _inspect_answer,
        CopilotIntent.COMPLIANCE: _compliance_answer,
        CopilotIntent.CITIZEN: _citizen_answer,
        CopilotIntent.SATELLITE: lambda b: _engine_topic_answer(
            b, "satellite", empty_why=SATELLITE_UNAVAILABLE, extra_limitations=[SATELLITE_UNAVAILABLE]
        ),
        CopilotIntent.GEOSPATIAL: lambda b: _engine_topic_answer(
            b,
            "geo",
            empty_why=GPS_UNAVAILABLE if b.data_mode == DataMode.REAL else UNAVAILABLE_PHRASE,
            extra_limitations=[GPS_UNAVAILABLE] if b.data_mode == DataMode.REAL else None,
        ),
        CopilotIntent.SIGNALS: _signals_answer,
        CopilotIntent.RISK_V2_CONTRIBUTION: _v2_contribution_answer,
        CopilotIntent.RISK_V2_CORRELATED: _v2_correlated_answer,
        CopilotIntent.RISK_V2_CONFLICTING: _v2_conflict_answer,
        CopilotIntent.RISK_V2_SCORE_CHANGE: _v2_score_change_answer,
        CopilotIntent.LIFECYCLE_WHERE: _lifecycle_where_answer,
        CopilotIntent.LIFECYCLE_REMAINING: _lifecycle_remaining_answer,
        CopilotIntent.LIFECYCLE_LAST_MILESTONE: _lifecycle_last_milestone_answer,
        CopilotIntent.MILESTONE: _milestone_answer,
        CopilotIntent.GRAPH: lambda b: _engine_topic_answer(
            b, "graph", empty_why="No relationship-graph Evidence Object is stored."
        ),
        CopilotIntent.DOCUMENTS: lambda b: _engine_topic_answer(
            b, "document", empty_why="No document Evidence Object is stored."
        ),
        CopilotIntent.IMAGES: lambda b: _engine_topic_answer(
            b, "image", empty_why="No image Evidence Object is stored."
        ),
        CopilotIntent.FORENSICS: lambda b: _engine_topic_answer(
            b, "forensics", empty_why="No image-forensics Evidence Object is stored."
        ),
        CopilotIntent.NEED_IMPACT: lambda b: _engine_topic_answer(
            b, "need", empty_why="No Need & Impact Evidence Object is stored."
        ),
        CopilotIntent.EXTERNAL_CONTEXT: _context_answer,
        CopilotIntent.PROJECT_OVERVIEW: _overview_answer,
        CopilotIntent.GENERAL: _overview_answer,
        CopilotIntent.ML_EVIDENCE: _ml_answer,
        CopilotIntent.ML_FRAUD_CLARIFICATION: _ml_fraud_clarification,
    }
    builder = dispatch.get(intent, _overview_answer)
    return builder(bundle)
