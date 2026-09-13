from __future__ import annotations

from app.copilot.providers import resolve_provider
from app.copilot.providers.deterministic import DeterministicProvider
from app.config import reset_settings_cache


def test_default_provider_is_deterministic(monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_LLM_ENABLED", "false")
    reset_settings_cache()
    provider = resolve_provider()
    assert isinstance(provider, DeterministicProvider)
    assert provider.uses_llm is False


def test_external_requires_explicit_allow(monkeypatch) -> None:
    monkeypatch.setenv("SARVSAKSHI_LLM_ENABLED", "true")
    monkeypatch.setenv("SARVSAKSHI_LLM_PROVIDER", "external")
    monkeypatch.setenv("SARVSAKSHI_LLM_API_KEY", "sk-test")
    monkeypatch.setenv("SARVSAKSHI_LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("SARVSAKSHI_LLM_MODEL", "test-model")
    monkeypatch.setenv("SARVSAKSHI_LLM_EXTERNAL_ALLOWED", "false")
    reset_settings_cache()
    provider = resolve_provider()
    assert isinstance(provider, DeterministicProvider)
    reset_settings_cache()
