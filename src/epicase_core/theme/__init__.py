"""Общий стилевой слой EduCase.

Тема — единый QSS-ресурс для Constructor и Player. Этот пакет НЕ импортирует
PySide6: загрузчик лишь читает текст ресурса и возвращает строку, чтобы не
нарушать границу «core не зависит от GUI-фреймворка». Применяет тему каждый GUI
у себя в ``__main__`` через ``app.setStyleSheet(load_qss())``.
"""
from __future__ import annotations

from importlib.resources import files

__all__ = ["load_qss"]


def load_qss() -> str:
    """Прочитать базовую тему ``theme.qss`` из этого пакета и вернуть как строку.

    Чтение через :mod:`importlib.resources`, поэтому ресурс корректно
    находится и в обычной установке, и внутри собранного PyInstaller EXE
    (при условии, что ``theme.qss`` упакован в ``datas`` spec-файла).
    """
    return files("epicase_core.theme").joinpath("theme.qss").read_text(encoding="utf-8")
