"""Конфигурация и пути. Никаких хардкод-путей по коду — только отсюда / из ENV."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _data_dir() -> Path:
    """Каталог данных приложения (Windows: %LOCALAPPDATA%/EduCase)."""
    base = os.environ.get("EDUCASE_DATA_DIR")
    if base:
        return Path(base)
    local = os.environ.get("LOCALAPPDATA") or str(Path.home())
    return Path(local) / "EduCase"


@dataclass(frozen=True)
class Config:
    data_dir: Path = field(default_factory=_data_dir)


config = Config()
