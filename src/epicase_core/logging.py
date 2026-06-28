"""Единая настройка loguru. Вызывать один раз при старте приложения."""
from __future__ import annotations

from loguru import logger

from epicase_core.config import config

_configured = False


def setup_logging(app_name: str) -> None:
    global _configured
    if _configured:
        return
    log_dir = config.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_dir / f"{app_name}.log",
        rotation="2 MB",
        retention=5,
        encoding="utf-8",
        enqueue=True,
    )
    _configured = True
    logger.info("Логирование инициализировано: {}", app_name)
