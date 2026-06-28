"""Редактируемый виджет таймлайна: курсант сам заполняет «дата → событие» (ADR-005/008).

Курсанту виден только заголовок-задание (``timeline.title``). Эталонные события
(``timeline.events``) — ответ преподавателя для будущего отчёта — здесь НЕ показываются.
Введённые строки собираются методом ``entries`` (сырые данные, без сверки).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.stages import Timeline

_INITIAL_ROWS = 3


class EditableTimelineWidget(QWidget):
    """Таблица «Дата → Событие», заполняемая курсантом (эталон скрыт, ADR-005).

    ``timeline.title`` — задание (показываем). ``timeline.events`` — эталон ответа,
    курсанту НЕ показывается. Кнопки добавляют/удаляют строки; ``entries`` собирает
    заполненные строки для слота ответа ``Attempt``.
    """

    def __init__(self, timeline: Timeline, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.timeline_id = timeline.id

        layout = QVBoxLayout(self)

        group = QGroupBox(timeline.title)
        group_layout = QVBoxLayout(group)

        self._table = QTableWidget(_INITIAL_ROWS, 2)
        self._table.setHorizontalHeaderLabels(["Дата", "Событие"])
        self._table.horizontalHeader().setStretchLastSection(True)
        group_layout.addWidget(self._table)

        self.btn_add = QPushButton("Добавить строку")
        self.btn_remove = QPushButton("Удалить строку")
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        btn_row.addStretch()
        group_layout.addLayout(btn_row)

        layout.addWidget(group)

        self.btn_add.clicked.connect(self._add_row)
        self.btn_remove.clicked.connect(self._remove_row)

    def _add_row(self) -> None:
        """Добавить пустую строку в конец таблицы."""
        self._table.insertRow(self._table.rowCount())

    def _remove_row(self) -> None:
        """Удалить выбранную строку (или последнюю, если выбора нет)."""
        if self._table.rowCount() == 0:
            return
        row = self._table.currentRow()
        if row < 0:
            row = self._table.rowCount() - 1
        self._table.removeRow(row)

    def _cell_text(self, row: int, column: int) -> str:
        """Текст ячейки; несозданная/пустая ячейка → ""."""
        item = self._table.item(row, column)
        return item.text() if item is not None else ""

    def entries(self) -> tuple[tuple[str, str], ...]:
        """Заполненные строки «дата → событие»; полностью пустые строки пропускаются."""
        result: list[tuple[str, str]] = []
        for row in range(self._table.rowCount()):
            date = self._cell_text(row, 0)
            event = self._cell_text(row, 1)
            if date.strip() or event.strip():
                result.append((date, event))
        return tuple(result)
