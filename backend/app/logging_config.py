from __future__ import annotations

import logging
from typing import Any

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Idempotent process-wide logging setup."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    logging.getLogger("sarvsakshi").setLevel(getattr(logging, level.upper(), logging.INFO))
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_extra(**kwargs: Any) -> dict[str, Any]:
    return kwargs
