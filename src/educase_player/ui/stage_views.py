"""Фабрика виджетов-заглушек для рендереров этапов.

Точка расширения (СЕМ): когда появятся реальные рендереры этапов, фабрика
будет возвращать специфичный для типа виджет вместо заглушки.
"""
from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from educase_core.domain.stages import Stage


def build_stage_view(stage: Stage) -> QWidget:
    """Создать виджет-заглушку для этапа.

    Содержит заголовок (stage.title), опционально intro и строку-заглушку.
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)

    layout.addWidget(QLabel(stage.title))

    if stage.intro:
        intro_label = QLabel(stage.intro)
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

    layout.addWidget(QLabel("Рендерер этапа в разработке"))
    layout.addStretch()

    return widget
