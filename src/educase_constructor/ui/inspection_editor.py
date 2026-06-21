"""Редактор сверки осмотра (Constructor, этапы 3/4): список ожидаемых групп синонимов.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичный
список редакторов групп и кнопки — точки доступа для тестов. Сборка значений в драфт —
через ``to_draft``. Каждая группа — одна ожидаемая группа осмотра (``SynonymSetEditor``).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import make_placeholder, refresh_placeholder, wrap_in_card
from educase_constructor.ui.synonym_editor import SynonymSetEditor
from educase_core.application.case_builder import InspectionDraft


class InspectionEditor(QWidget):
    """Редактор осмотра: список ожидаемых групп синонимов (каждая — одна группа осмотра)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.group_editors: list[SynonymSetEditor] = []
        self._group_cards: list[QGroupBox] = []

        self.add_group_button = QPushButton("Добавить", self)
        self.add_group_button.setIcon(load_icon("add"))
        self.remove_group_button = QPushButton("Удалить", self)
        self.remove_group_button.setIcon(load_icon("delete"))
        self.add_group_button.clicked.connect(self.add_group)
        self.remove_group_button.clicked.connect(self.remove_last_group)

        group_buttons = QHBoxLayout()
        group_buttons.addWidget(self.add_group_button)
        group_buttons.addWidget(self.remove_group_button)
        group_buttons.addStretch(1)

        self._empty_label = make_placeholder("Пока не добавлено ни одной группы")

        self._groups_layout = QVBoxLayout()

        layout = QVBoxLayout(self)
        layout.addLayout(group_buttons)
        layout.addWidget(self._empty_label)
        layout.addLayout(self._groups_layout)

        self._refresh_empty()

    def add_group(self) -> None:
        """Добавить редактор новой ожидаемой группы осмотра в конец списка."""
        editor = SynonymSetEditor(self)
        self.group_editors.append(editor)
        card = wrap_in_card(editor, f"Группа {len(self.group_editors)}")
        self._group_cards.append(card)
        self._groups_layout.addWidget(card)
        self._refresh_empty()

    def remove_last_group(self) -> None:
        """Удалить последний редактор группы (если он есть)."""
        if not self.group_editors:
            return
        self.group_editors.pop()
        card = self._group_cards.pop()
        self._groups_layout.removeWidget(card)
        card.deleteLater()
        self._refresh_empty()

    def _refresh_empty(self) -> None:
        """Обновить видимость подсказки пустого состояния списка групп осмотра."""
        refresh_placeholder(self._empty_label, is_empty=len(self.group_editors) == 0)

    def load(self, draft: InspectionDraft) -> None:
        """Заполнить редактор значениями ``InspectionDraft`` (открытие кейса на правку).

        Текущие группы удаляются и пересобираются из ``draft.groups`` (симметрично ``to_draft``).
        """
        while self.group_editors:
            self.remove_last_group()
        for group in draft.groups:
            self.add_group()
            self.group_editors[-1].load(group)
        self._refresh_empty()

    def to_draft(self) -> InspectionDraft:
        """Собрать ``InspectionDraft`` из всех редакторов групп осмотра."""
        return InspectionDraft(
            groups=tuple(editor.to_draft() for editor in self.group_editors),
        )
