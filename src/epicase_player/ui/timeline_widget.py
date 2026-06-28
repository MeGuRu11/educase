"""Виджет таймлайна сроков наблюдения за очагом."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.stages import Timeline


class TimelineWidget(QWidget):
    """Отображение таймлайна: заголовок в QGroupBox, строки «дата — событие»."""

    def __init__(self, timeline: Timeline, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.timeline = timeline

        layout = QVBoxLayout(self)

        group = QGroupBox(timeline.title)
        group_layout = QVBoxLayout(group)

        for date, event in timeline.events:
            row = QLabel(f"{date} — {event}")
            row.setWordWrap(True)
            group_layout.addWidget(row)

        layout.addWidget(group)
