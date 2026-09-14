from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Runtime settings. LLM stays off unless explicitly enabled later."""

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_prefix="SARVSAKSHI_",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://skill-seekers.vercel.app"
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_URL", "SARVSAKSHI_DATABASE_URL"),
    )
    database_path: str = "data/processed/sarvsakshi.db"
    llm_enabled: bool = False
    llm_api_key: str = ""
    llm_model: str = ""
    llm_provider: str = "disabled"
    llm_base_url: str = ""
    llm_external_allowed: bool = False
    llm_timeout_seconds: float = 12.0

    fusion_config_version: str = "p0-v1"
    engine_version: str = "skeleton-0"
    # Application scope only. Does not delete or hide rows in SQLite.
    pilot_state: str = "Andhra Pradesh"
    default_data_mode: str = "HYBRID"
    geospatial_threshold_meters: float = 500.0
    citizen_radius_meters: float = 500.0
    citizen_insufficient_sample_max: int = 3
    citizen_community_signal_min: int = 10
    citizen_min_reports_for_concern: int = 3
    citizen_rate_limit_count: int = 20
    citizen_rate_limit_window_seconds: int = 3600
    forensics_ai_backend: str = "unavailable"
    forensics_ai_external_enabled: bool = False
    satellite_provider: str = "unavailable"
    ml_models_dir: str = ""
    context_data_dir: str = "data/external"
    context_http_timeout_seconds: float = 8.0
    context_live_fetch: bool = False
    data_gov_in_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def sqlite_path(self) -> Path:
        path = Path(self.database_path)
        if not path.is_absolute():
            path = REPO_ROOT / path
        return path

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url.replace("postgres://", "postgresql://", 1)
        return "sqlite:///" + self.sqlite_path.resolve().as_posix()

    @property
    def ml_models_path(self) -> Path:
        if self.ml_models_dir:
            path = Path(self.ml_models_dir)
            return path if path.is_absolute() else REPO_ROOT / path
        return BACKEND_DIR / "app" / "ml" / "models"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
