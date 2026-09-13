"""Final End-to-End Demo Cases V1 constants.

Application orchestration only. Does not score intelligence or change
Risk Fusion V2. Controlled prototype scenarios — not official MPLADS cases.
"""

from __future__ import annotations

from app.engines.cost.evaluate import DEMO_INTERNAL_IDS

LAYER_NAME = "demo-cases"
LAYER_VERSION = "final-demo-cases-v1"
FIXTURE_LAYER = "demo-evidence-fixtures-v1"
FIXTURE_SOURCE = "demo-evidence-fixtures-v1"

DEMO_NOTICE = (
    "Controlled prototype scenario. Some values are synthetic and are not "
    "official MPLADS records. DEMO / SYNTHETIC / CONTROLLED PROTOTYPE "
    "evidence fixtures are not official MPLADS evidence."
)
FIXTURE_NOTICE = (
    "DEMO / SYNTHETIC / CONTROLLED PROTOTYPE. Labelled HYBRID evidence "
    "fixtures for demonstration only. Not official MPLADS evidence."
)
HYBRID_NOTICE = (
    "DEMO / HYBRID — Base project identity comes from a real MPLADS extract. "
    "Fields and attachments marked SYNTHETIC are prototype enrichment and are "
    "not official MPLADS records."
)
GOVERNANCE_NOTE = (
    "AI recommends. Authorized officers decide. Investigation Priority and "
    "Evidence Confidence are review rankings, not a legal finding of fraud. "
    "This prototype does not sanction a project or release funds."
)
NO_FRAUD_NOTE = (
    "This demonstration does not confirm fraud and does not output a fraud probability."
)
NO_SANCTION_NOTE = (
    "Officer actions are audited and do not change intelligence scores. "
    "No automatic sanction. PFMS is not integrated."
)

CASE_IDS = ("GHOST", "OVERBILL", "STUCK", "CLEAN")

JOURNEY_STEPS = (
    "PROJECT",
    "PASSPORT",
    "LIFECYCLE",
    "PLAN",
    "CLAIM",
    "EVIDENCE",
    "RISK",
    "COPILOT",
    "DECISION",
    "SUMMARY",
)

FORBIDDEN_PHRASES = (
    "fraud confirmed",
    "fraud has been established",
    "this is fraud",
    "automatic sanction",
    "automatic payment",
    "pfms payment",
    "release funds",
)


def assert_fusion_v2_unchanged() -> None:
    """Demo Cases must not rewrite Risk Fusion V2."""
    from app.engines.fusion_v2.constants import ENGINE_VERSION as FUSION_V2_VERSION
    from app.engines.fusion_v2.constants import GROUP_WEIGHTS
    from app.engines.lifecycle.constants import FROZEN_FUSION_V2_VERSION, FROZEN_FUSION_V2_WEIGHTS

    if FUSION_V2_VERSION != FROZEN_FUSION_V2_VERSION:
        raise RuntimeError("Risk Fusion V2 version changed; Demo Cases V1 must not rewrite it.")
    if GROUP_WEIGHTS != FROZEN_FUSION_V2_WEIGHTS:
        raise RuntimeError("Risk Fusion V2 weights changed; Demo Cases V1 must not rewrite them.")


def internal_project_id_for(case_id: str) -> str:
    key = str(case_id or "").strip().upper().replace("-", "").replace("_", "")
    if key == "OVERBILL":
        return DEMO_INTERNAL_IDS["OVERBILL"]
    if key not in DEMO_INTERNAL_IDS:
        raise KeyError(case_id)
    return DEMO_INTERNAL_IDS[key]
