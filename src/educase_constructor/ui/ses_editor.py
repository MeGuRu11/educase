"""Редактор этапа 5 «Оценка СЭС» (Constructor).

Вступление, контекстный поиск, необязательный выбор уровня СЭС и задания по документам. Без
визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля ввода,
флаг и вложенные редакторы — точки доступа для тестов. Сборка значений в драфт — через
``to_draft``; поле выбора уровня собирается только при включённом флаге.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.document_editor import DocumentListEditor
from educase_constructor.ui.field_editor import FieldEditor
from educase_constructor.ui.search_editor import SearchEditor
from educase_core.application.case_builder import SesDraft


class SesEditor(QWidget):
    """Редактор этапа «Оценка СЭС»: вступление, поиск, выбор уровня СЭС, документы."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.intro_edit.setPlaceholderText("Краткое введение к этапу, которое увидит курсант")
        self.search_editor = SearchEditor(self)
        self.include_level_checkbox = QCheckBox("Добавить выбор уровня СЭС", self)
        self.level_field_editor = FieldEditor(self)
        self.documents_editor = DocumentListEditor(self)

        intro_form = QFormLayout()
        intro_form.addRow("Вступление", self.intro_edit)

        search_box = QGroupBox("Поиск")
        search_box_layout = QVBoxLayout(search_box)
        search_box_layout.addWidget(self.search_editor)

        level_box = QGroupBox("Выбор уровня СЭС")
        level_box_layout = QVBoxLayout(level_box)
        level_box_layout.addWidget(self.include_level_checkbox)
        level_box_layout.addWidget(self.level_field_editor)

        documents_box = QGroupBox("Документы")
        documents_box_layout = QVBoxLayout(documents_box)
        documents_box_layout.addWidget(self.documents_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(intro_form)
        layout.addWidget(search_box)
        layout.addWidget(level_box)
        layout.addWidget(documents_box)

    def to_draft(self) -> SesDraft:
        """Собрать ``SesDraft`` из вступления, поиска, выбора уровня и документов."""
        level_choice = (
            self.level_field_editor.to_draft()
            if self.include_level_checkbox.isChecked()
            else None
        )
        return SesDraft(
            intro=self.intro_edit.text(),
            search=self.search_editor.to_draft(),
            level_choice=level_choice,
            documents=self.documents_editor.to_draft(),
        )
