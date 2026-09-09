"""Investigation Copilot.

P0 plan: deterministic evidence-grounded templates first.
LLM integration is optional, isolated behind SARVSAKSHI_LLM_ENABLED, and must
never invent evidence. Not implemented in this foundation slice.
"""

TEMPLATE_MODE = "template"
LLM_MODE = "llm"
