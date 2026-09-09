from __future__ import annotations

from functools import lru_cache
from pathlib import Path

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
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_path: str = "data/processed/sarvsakshi.db"
    llm_enabled: bool = False
    llm_api_key: str = ""
    llm_model: str = ""

    fusion_config_version: str = "p0-v1"
    engine_version: str = "skeleton-0"

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
        return "sqlite:///" + self.sqlite_path.resolve().as_posix()


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
