"""Загрузка SVG-иконок Constructor как QIcon (путь резолвится как theme.qss)."""
from __future__ import annotations

from importlib.resources import files

from PySide6.QtGui import QIcon


def load_icon(name: str) -> QIcon:
    """Вернуть QIcon из resources/icons/<name>.svg (name без расширения)."""
    path = files("epicase_constructor").joinpath("resources", "icons", f"{name}.svg")
    return QIcon(str(path))
