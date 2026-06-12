"""Редактор сверки осмотра (Constructor, этапы 3/4): список ожидаемых групп синонимов.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичный
список редакторов групп и кнопки — точки доступа для тестов. Сборка значений в драфт —
через ``to_draft``. Каждая группа — одна ожидаемая группа осмотра (``SynonymSetEditor``).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.synonym_editor import SynonymSetEditor
from educase_core.application.case_builder import InspectionDraft


class InspectionEditor(QWidget):
    """Редактор осмотра: список ожидаемых групп синонимов (каждая — одна группа осмотра)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.group_editors: list[SynonymSetEditor] = []

        self.add_group_button = QPushButton("Добавить группу", self)
        self.remove_group_button = QPushButton("Удалить последнюю", self)
        self.add_group_button.clicked.connect(self.add_group)
        self.remove_group_button.clicked.connect(self.remove_last_group)

        group_buttons = QHBoxLayout()
        group_buttons.addWidget(self.add_group_button)
        group_buttons.addWidget(self.remove_group_button)

        self._groups_layout = QVBoxLayout()

        layout = QVBoxLayout(self)
        layout.addLayout(group_buttons)
        layout.addLayout(self._groups_layout)

    def add_group(self) -> None:
        """Добавить редактор новой ожидаемой группы осмотра в конец списка."""
        editor = SynonymSetEditor(self)
        self.group_editors.append(editor)
        self._groups_layout.addWidget(editor)

    def remove_last_group(self) -> None:
        """Удалить последний редактор группы (если он есть)."""
        if not self.group_editors:
            return
        editor = self.group_editors.pop()
        self._groups_layout.removeWidget(editor)
        editor.deleteLater()

    def to_draft(self) -> InspectionDraft:
        """Собрать ``InspectionDraft`` из всех редакторов групп осмотра."""
        return InspectionDraft(
            groups=tuple(editor.to_draft() for editor in self.group_editors),
        )
