"""Investigation Copilot.

Evidence-grounded officer assistant. Deterministic templates are the default.
LLM providers are optional, isolated, and off unless explicitly enabled.
"""

from app.copilot.constants import ENGINE_VERSION, GOVERNANCE_NOTE

TEMPLATE_MODE = "template"
LLM_MODE = "llm"
ENGINE_NAME = "copilot"

__all__ = ["ENGINE_NAME", "ENGINE_VERSION", "GOVERNANCE_NOTE", "LLM_MODE", "TEMPLATE_MODE"]
