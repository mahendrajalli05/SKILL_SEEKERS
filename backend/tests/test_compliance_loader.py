from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.engines.compliance.constants import DEFAULT_RULES_PATH
from app.engines.compliance.errors import ComplianceRuleError
from app.engines.compliance.loader import load_rules, parse_ruleset


MINIMAL_SOURCE = {
    "document": "Guidelines on MPLADS, 2023",
    "para": "3.2.4",
    "source_id": "TEST-SOURCE",
    "url": "https://example.invalid/mplads",
    "quote": "Sanction or rejection within 45 days from the date of receipt.",
}


def _rule(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "rule_id": "R001",
        "category": "SANCTION_TIMELINE",
        "title": "45-day sanction",
        "description": "Sanction within 45 days.",
        "severity": "attention",
        "required_fields": ["recommended_date", "sanction_date"],
        "evaluation_logic": {
            "operator": "date_diff_gt",
            "left_field": "sanction_date",
            "right_field": "recommended_date",
            "threshold": 45,
        },
        "source_reference": dict(MINIMAL_SOURCE),
        "limitations": ["MCC calendar unavailable."],
        "not_assessable_template": "Sanction-date evidence is unavailable in the current real dataset.",
    }
    payload.update(overrides)
    return payload


def _catalog(rules: list[dict[str, object]]) -> dict[str, object]:
    return {
        "engine": "compliance",
        "engine_version": "compliance-rules-v1",
        "guideline_document": "Guidelines on MPLADS, 2023",
        "effective_from": "2023-04-01",
        "disclaimer": "Deterministic rule engine.",
        "sources": [],
        "rules": rules,
    }


def test_production_rules_load_and_preserve_source_references() -> None:
    ruleset = load_rules()
    assert ruleset.engine == "compliance"
    assert ruleset.engine_version == "compliance-rules-v1"
    assert DEFAULT_RULES_PATH.is_file()
    ids = [rule.rule_id for rule in ruleset.rules]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    assert "R001" in ids
    r001 = next(rule for rule in ruleset.rules if rule.rule_id == "R001")
    assert r001.source_reference.para == "3.2.4"
    assert "sansad.in" in r001.source_reference.url
    assert "45 days" in r001.source_reference.quote
    assert r001.category == "SANCTION_TIMELINE"
    assert r001.severity == "attention"
    blob = json.dumps(r001.source_reference.__dict__)
    assert "fraud" not in blob.casefold()


def test_load_rules_from_path(tmp_path: Path) -> None:
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(_catalog([_rule()])), encoding="utf-8")
    ruleset = load_rules(path)
    assert len(ruleset.rules) == 1
    assert ruleset.rules[0].rule_id == "R001"
    assert ruleset.rules[0].source_reference.source_id == "TEST-SOURCE"


def test_missing_rule_file_raises() -> None:
    with pytest.raises(ComplianceRuleError, match="not found"):
        load_rules(Path("does-not-exist-compliance-rules.json"))


def test_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ComplianceRuleError, match="not valid JSON"):
        load_rules(path)


@pytest.mark.parametrize(
    "payload, match",
    [
        ("not-an-object", "JSON object"),
        (_catalog([]), "non-empty rules list"),
        (_catalog([_rule(rule_id="")]), "rule_id"),
        (_catalog([_rule(rule_id="X1")]), "rule_id must match"),
        (_catalog([_rule(severity="critical")]), "severity"),
        (_catalog([_rule(evaluation_logic={"operator": "predict_ml"})]), "unknown evaluation operator"),
        (_catalog([_rule(), _rule()]), "Duplicate rule_id"),
        (_catalog([_rule(required_fields="sanction_date")]), "required_fields"),
        (
            _catalog([_rule(source_reference={"document": "only"})]),
            "source_reference requires",
        ),
        (_catalog([_rule(category="")]), "category"),
    ],
)
def test_malformed_rule_catalog_is_rejected(payload: object, match: str) -> None:
    with pytest.raises(ComplianceRuleError, match=match):
        parse_ruleset(payload)


def test_empty_rules_list_is_malformed() -> None:
    with pytest.raises(ComplianceRuleError, match="non-empty"):
        parse_ruleset(_catalog([]))
