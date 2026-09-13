"""Deterministic intent parsing for Investigation Copilot V1.

Keyword/phrase matching only. Does not call an LLM.
"""

from __future__ import annotations

import re

from app.copilot.types import CopilotIntent

_LEGAL = re.compile(
    r"\b(?:is this fraud|prove fraud|declare fraud|prosecute|guilty|"
    r"legal (?:finding|conclusion)|criminal)\b",
    re.IGNORECASE,
)

_PATTERNS: tuple[tuple[CopilotIntent, re.Pattern[str]], ...] = (
    (CopilotIntent.WHY_NOT_FLAGGED, re.compile(r"why (?:was |is )?(?:this )?(?:project )?not flagged|why not flagged", re.I)),
    (CopilotIntent.WHY_FLAGGED, re.compile(r"why (?:is |was )?(?:this )?(?:project )?(?:flagged|high priority)|why flagged", re.I)),
    (CopilotIntent.TIME_INCONCLUSIVE, re.compile(r"time (?:intelligence )?(?:inconclusive|unavailable|not assessable)|actual delay", re.I)),
    (CopilotIntent.COMPARABLES, re.compile(r"comparable|cost peer|peer (?:project|work)|used as cost", re.I)),
    (CopilotIntent.PCE_SUMMARY, re.compile(r"plan\s*(?:→|->|vs)?\s*claim|summarize (?:the )?plan|pce", re.I)),
    (CopilotIntent.INSPECT_NEXT, re.compile(r"inspect next|what should i inspect|recommended (?:next )?action|next step", re.I)),
    (CopilotIntent.STRONGEST_EVIDENCE, re.compile(r"strongest evidence|what evidence supports|evidence supports", re.I)),
    (CopilotIntent.LIFECYCLE_WHERE, re.compile(r"where is this project in its lifecycle|in its lifecycle|lifecycle (?:state|stage|status)|workflow state", re.I)),
    (CopilotIntent.LIFECYCLE_REMAINING, re.compile(r"remains to be verified|what remains|remaining (?:to verify|stages|steps|evidence)", re.I)),
    (CopilotIntent.LIFECYCLE_LAST_MILESTONE, re.compile(r"last milestone decision|last milestone", re.I)),
    (CopilotIntent.MISSING_INFORMATION, re.compile(r"missing|what information is (?:not |un)?available|unavailable", re.I)),
    (CopilotIntent.COMPLIANCE, re.compile(r"compliance|triggered rules?|guideline", re.I)),
    (CopilotIntent.CITIZEN, re.compile(r"citizen|jan[-\s]?sakshi|community feedback", re.I)),
    (CopilotIntent.SATELLITE, re.compile(r"satellite|remote[-\s]?sensing", re.I)),
    (CopilotIntent.GEOSPATIAL, re.compile(r"\bgps\b|geospatial|location consistency", re.I)),
    (CopilotIntent.RISK_V2_CORRELATED, re.compile(r"discounted as correlated|correlated evidence|shared semantic", re.I)),
    (CopilotIntent.RISK_V2_CONFLICTING, re.compile(r"conflicting evidence|evidence (?:is )?conflict|which evidence is conflicting|disagree", re.I)),
    (CopilotIntent.RISK_V2_SCORE_CHANGE, re.compile(r"new score higher|score higher|why is the new score|v2 score", re.I)),
    (CopilotIntent.RISK_V2_CONTRIBUTION, re.compile(r"which evidence contributed most|evidence contributed most", re.I)),
    (CopilotIntent.SIGNALS, re.compile(r"signals? contributed|investigation priority|which signals", re.I)),
    (CopilotIntent.MILESTONE, re.compile(r"milestone", re.I)),
    (CopilotIntent.GRAPH, re.compile(r"relationship graph|\bgraph\b|connected (?:projects|works)", re.I)),
    (CopilotIntent.DOCUMENTS, re.compile(r"\bdocuments?\b|blueprint|boq", re.I)),
    (CopilotIntent.IMAGES, re.compile(r"\bimages?\b|photographs?|photo evidence", re.I)),
    (CopilotIntent.FORENSICS, re.compile(r"forensic|ai[-\s]?generated|manipulation", re.I)),
    (
        CopilotIntent.EXTERNAL_CONTEXT,
        re.compile(
            r"external context|cost context|reference cost|development indicator|"
            r"what year is this development|project-specific evidence|"
            r"what source supports this cost|infrastructure context|"
            r"contextual (?:evidence|intelligence|data)",
            re.I,
        ),
    ),
    (CopilotIntent.NEED_IMPACT, re.compile(r"need\s*(?:and|&)\s*impact|need score|impact score", re.I)),
    (
        CopilotIntent.ML_FRAUD_CLARIFICATION,
        re.compile(
            r"fraud probability|is this a fraud|ml .{0,50}fraud|"
            r"wrongdoing probability|likelihood of wrongdoing|"
            r"confirm(?:ed)? misconduct|legal guilt|"
            r"(?:ml|anomaly score|isolation forest|model).{0,50}"
            r"(?:wrongdoing|misconduct|guilt|corruption|legal conclusion)",
            re.I,
        ),
    ),
    (CopilotIntent.ML_EVIDENCE, re.compile(r"\bml\b|machine learning|isolation forest|anomaly score|which model generated|model generated this score|model version", re.I)),
    (CopilotIntent.PROJECT_OVERVIEW, re.compile(r"summarize (?:this )?project|project overview|tell me about this project", re.I)),
)


def parse_intent(question: str, *, previous_intent: CopilotIntent | None = None) -> CopilotIntent:
    text = (question or "").strip()
    if not text:
        return previous_intent or CopilotIntent.GENERAL
    if _LEGAL.search(text):
        return CopilotIntent.FORBIDDEN_LEGAL
    for intent, pattern in _PATTERNS:
        if pattern.search(text):
            return intent
    if previous_intent and len(text.split()) <= 6:
        return previous_intent
    return CopilotIntent.GENERAL
