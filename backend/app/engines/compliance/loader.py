"""Load and validate the data-driven MPLADS compliance rule catalog."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.engines.compliance.constants import (
    ALLOWED_OPERATORS,
    ALLOWED_SEVERITIES,
    DEFAULT_RULES_PATH,
    RULE_ID_PATTERN,
)
from app.engines.compliance.errors import ComplianceRuleError
from app.engines.compliance.types import ComplianceRule, RuleSet, SourceReference

_RULE_ID_RE = re.compile(RULE_ID_PATTERN)


def _require_str(payload: dict[str, Any], key: str, *, allow_empty: bool = False) -> str:
    if key not in payload:
        raise ComplianceRuleError(f"Rule catalog field '{key}' is required.")
    value = payload[key]
    if value is None:
        raise ComplianceRuleError(f"Rule catalog field '{key}' must be a string.")
    if not isinstance(value, str):
        raise ComplianceRuleError(f"Rule catalog field '{key}' must be a string.")
    text = value.strip()
    if not text and not allow_empty:
        raise ComplianceRuleError(f"Rule catalog field '{key}' must be non-empty.")
    return text


def _parse_source(payload: dict[str, Any], rule_id: str) -> SourceReference:
    if not isinstance(payload, dict):
        raise ComplianceRuleError(f"{rule_id}: source_reference must be an object.")
    document = str(payload.get("document") or "").strip()
    url = str(payload.get("url") or "").strip()
    source_id = str(payload.get("source_id") or "").strip()
    quote = str(payload.get("quote") or "").strip()
    if not document or not url or not source_id or not quote:
        raise ComplianceRuleError(
            f"{rule_id}: source_reference requires document, source_id, url, and quote."
        )
    para_raw = payload.get("para")
    para = None if para_raw in (None, "") else str(para_raw).strip()
    return SourceReference(
        document=document,
        para=para,
        source_id=source_id,
        url=url,
        quote=quote,
    )


def _parse_logic(payload: Any, rule_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        raise ComplianceRuleError(f"{rule_id}: evaluation_logic must be a non-empty object.")
    operator = str(payload.get("operator") or "").strip()
    if operator not in ALLOWED_OPERATORS:
        raise ComplianceRuleError(
            f"{rule_id}: unknown evaluation operator '{operator}'."
        )
    return dict(payload)


def parse_rule(payload: Any) -> ComplianceRule:
    if not isinstance(payload, dict):
        raise ComplianceRuleError("Each rule must be a JSON object.")
    rule_id = str(payload.get("rule_id") or "").strip()
    if not rule_id:
        raise ComplianceRuleError("Each rule must have a rule_id.")
    if not _RULE_ID_RE.match(rule_id):
        raise ComplianceRuleError(f"{rule_id}: rule_id must match {RULE_ID_PATTERN}.")
    severity = str(payload.get("severity") or "").strip()
    if severity not in ALLOWED_SEVERITIES:
        raise ComplianceRuleError(
            f"{rule_id}: severity must be one of {sorted(ALLOWED_SEVERITIES)}."
        )
    required = payload.get("required_fields", [])
    if required is None:
        required = []
    if not isinstance(required, list) or any(not isinstance(item, str) for item in required):
        raise ComplianceRuleError(f"{rule_id}: required_fields must be a list of strings.")
    limitations = payload.get("limitations") or []
    if not isinstance(limitations, list) or any(not isinstance(item, str) for item in limitations):
        raise ComplianceRuleError(f"{rule_id}: limitations must be a list of strings.")
    return ComplianceRule(
        rule_id=rule_id,
        category=_require_str(payload, "category"),
        title=_require_str(payload, "title"),
        description=_require_str(payload, "description"),
        severity=severity,
        required_fields=tuple(item.strip() for item in required if item.strip()),
        evaluation_logic=_parse_logic(payload.get("evaluation_logic"), rule_id),
        source_reference=_parse_source(payload.get("source_reference"), rule_id),
        limitations=tuple(item.strip() for item in limitations if str(item).strip()),
        not_assessable_template=str(payload.get("not_assessable_template") or "").strip(),
    )


def parse_ruleset(payload: Any) -> RuleSet:
    if not isinstance(payload, dict):
        raise ComplianceRuleError("Rule catalog must be a JSON object.")
    rules_raw = payload.get("rules")
    if not isinstance(rules_raw, list) or not rules_raw:
        raise ComplianceRuleError("Rule catalog must contain a non-empty rules list.")
    rules = [parse_rule(item) for item in rules_raw]
    seen: set[str] = set()
    for rule in rules:
        if rule.rule_id in seen:
            raise ComplianceRuleError(f"Duplicate rule_id '{rule.rule_id}'.")
        seen.add(rule.rule_id)
    ordered = tuple(sorted(rules, key=lambda item: item.rule_id))
    sources = payload.get("sources") or []
    if not isinstance(sources, list):
        raise ComplianceRuleError("sources must be a list.")
    return RuleSet(
        engine=_require_str(payload, "engine"),
        engine_version=_require_str(payload, "engine_version"),
        guideline_document=_require_str(payload, "guideline_document"),
        effective_from=str(payload.get("effective_from") or "").strip(),
        disclaimer=str(payload.get("disclaimer") or "").strip(),
        sources=tuple(item for item in sources if isinstance(item, dict)),
        rules=ordered,
    )


def load_rules(path: Path | None = None) -> RuleSet:
    catalog = path or DEFAULT_RULES_PATH
    if not catalog.is_file():
        raise ComplianceRuleError(f"Rule catalog not found: {catalog}")
    try:
        payload = json.loads(catalog.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ComplianceRuleError(f"Rule catalog is not valid JSON: {exc}") from exc
    return parse_ruleset(payload)


def source_reference_dict(rule: ComplianceRule) -> dict[str, Any]:
    ref = rule.source_reference
    return {
        "document": ref.document,
        "para": ref.para,
        "source_id": ref.source_id,
        "url": ref.url,
        "quote": ref.quote,
    }
