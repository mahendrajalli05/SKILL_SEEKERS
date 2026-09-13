"""Resolve the Copilot LLM provider.

Default: deterministic grounded templates. External calls require an explicit
allow flag. The application remains functional with no API key.
"""

from __future__ import annotations

from app.config import get_settings
from app.copilot.providers.deterministic import DeterministicProvider
from app.copilot.providers.external import ExternalProvider
from app.copilot.providers.local import LocalProvider
from app.copilot.types import CopilotProviderName


def resolve_provider():
    settings = get_settings()
    if not settings.llm_enabled:
        return DeterministicProvider()
    provider = (settings.llm_provider or CopilotProviderName.DISABLED.value).strip().lower()
    if provider in {CopilotProviderName.LOCAL.value, "open", "ollama"}:
        if settings.llm_base_url:
            return LocalProvider(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                timeout=settings.llm_timeout_seconds,
            )
    if provider == CopilotProviderName.EXTERNAL.value:
        if (
            settings.llm_external_allowed
            and settings.llm_api_key
            and settings.llm_base_url
            and settings.llm_model
        ):
            return ExternalProvider(
                base_url=settings.llm_base_url,
                model=settings.llm_model,
                api_key=settings.llm_api_key,
                timeout=settings.llm_timeout_seconds,
            )
    return DeterministicProvider()
