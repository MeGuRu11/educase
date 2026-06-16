"""Редакторы таймлайнов (Constructor, этап 6): один таймлайн и список таймлайнов.

Таймлайн — заголовок + таблица пар «дата → событие». Без визуальной полировки: только
функциональные виджеты и layout-менеджеры. Публичные поля ввода, списки вложенных редакторов
и кнопки — точки доступа для тестов. Сборка значений в драфты — через ``to_draft``; id
таймлайна присваивает билдер.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import make_placeholder, refresh_placeholder, wrap_in_card
from educase_core.application.case_builder import TimelineDraft


class TimelineEditor(QWidget):
    """Редактор одного таймлайна: заголовок + таблица пар «дата/событие»."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_edit = QLineEdit(self)

        self.events_table = QTableWidget(0, 2, self)
        self.events_table.setHorizontalHeaderLabels(["Дата", "Событие"])
        self.events_table.setMinimumHeight(140)

        self.add_row_button = QPushButton("+ строка", self)
        self.remove_row_button = QPushButton("− строка", self)
        self.add_row_button.clicked.connect(self.add_event_row)
        self.remove_row_button.clicked.connect(self.remove_last_event_row)

        form = QFormLayout()
        form.addRow("Заголовок", self.title_edit)

        row_buttons = QHBoxLayout()
        row_buttons.addWidget(self.add_row_button)
        row_buttons.addWidget(self.remove_row_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.events_table)
        layout.addLayout(row_buttons)

    def add_event_row(self) -> None:
        """Добавить пустую строку «дата/событие»."""
        self.events_table.insertRow(self.events_table.rowCount())

    def remove_last_event_row(self) -> None:
        """Удалить последнюю строку таблицы событий (если она есть)."""
        count = self.events_table.rowCount()
        if count:
            self.events_table.removeRow(count - 1)

    def _collect_events(self) -> tuple[tuple[str, str], ...]:
        rows: list[tuple[str, str]] = []
        for row in range(self.events_table.rowCount()):
            date_item = self.events_table.item(row, 0)
            event_item = self.events_table.item(row, 1)
            date = date_item.text() if date_item is not None else ""
            event = event_item.text() if event_item is not None else ""
            if not date.strip() and not event.strip():
                continue
            rows.append((date, event))
        return tuple(rows)

    def to_draft(self) -> TimelineDraft:
        """Собрать ``TimelineDraft`` из заголовка и таблицы событий."""
        return TimelineDraft(
            title=self.title_edit.text(),
            events=self._collect_events(),
        )


class TimelineListEditor(QWidget):
    """Редактор списка таймлайнов этапа."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.timeline_editors: list[TimelineEditor] = []
        self._timeline_cards: list[QGroupBox] = []

        self.add_timeline_button = QPushButton("Добавить", self)
        self.add_timeline_button.setIcon(load_icon("add"))
        self.remove_timeline_button = QPushButton("Удалить", self)
        self.remove_timeline_button.setIcon(load_icon("delete"))
        self.add_timeline_button.clicked.connect(self.add_timeline)
        self.remove_timeline_button.clicked.connect(self.remove_last_timeline)

        timeline_buttons = QHBoxLayout()
        timeline_buttons.addWidget(self.add_timeline_button)
        timeline_buttons.addWidget(self.remove_timeline_button)
        timeline_buttons.addStretch(1)

        self._empty_label = make_placeholder("Пока не добавлено ни одного срока наблюдения")

        self._timelines_layout = QVBoxLayout()

        layout = QVBoxLayout(self)
        layout.addLayout(timeline_buttons)
        layout.addWidget(self._empty_label)
        layout.addLayout(self._timelines_layout)

        self._refresh_empty()

    def add_timeline(self) -> None:
        """Добавить редактор нового таймлайна в конец списка."""
        editor = TimelineEditor(self)
        self.timeline_editors.append(editor)
        card = wrap_in_card(editor, f"Срок наблюдения {len(self.timeline_editors)}")
        self._timeline_cards.append(card)
        self._timelines_layout.addWidget(card)
        self._refresh_empty()

    def remove_last_timeline(self) -> None:
        """Удалить последний редактор таймлайна (если он есть)."""
        if not self.timeline_editors:
            return
        self.timeline_editors.pop()
        card = self._timeline_cards.pop()
        self._timelines_layout.removeWidget(card)
        card.deleteLater()
        self._refresh_empty()

    def _refresh_empty(self) -> None:
        """Обновить видимость подсказки пустого состояния списка таймлайнов."""
        refresh_placeholder(self._empty_label, is_empty=len(self.timeline_editors) == 0)

    def to_draft(self) -> tuple[TimelineDraft, ...]:
        """Собрать драфты всех таймлайнов."""
        return tuple(editor.to_draft() for editor in self.timeline_editors)
