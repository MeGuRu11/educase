"""Редактор этапа 2 «Клинико-эпидемиологический диагноз» (Constructor).

Поиск, развилка и задания по документам. Без визуальной полировки: только функциональные
виджеты и layout-менеджеры. Публичные поля ввода и вложенные редакторы — точки доступа для
тестов. Сборка значений в драфт — через ``to_draft``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.branch_editor import BranchEditor
from educase_constructor.ui.document_editor import DocumentListEditor
from educase_constructor.ui.search_editor import SearchEditor
from educase_core.application.case_builder import ClinicalDraft


class ClinicalEditor(QWidget):
    """Редактор этапа «Клинический»: вступление, контекстный поиск и точка ветвления."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.intro_edit.setPlaceholderText("Краткое введение к этапу, которое увидит курсант")
        self.search_editor = SearchEditor(self)
        self.branch_editor = BranchEditor(self)
        self.documents_editor = DocumentListEditor(self)

        intro_form = QFormLayout()
        intro_form.addRow("Вступление", self.intro_edit)

        search_box = QGroupBox("Поиск")
        search_box_layout = QVBoxLayout(search_box)
        search_box_layout.addWidget(self.search_editor)

        branch_box = QGroupBox("Развилка")
        branch_box_layout = QVBoxLayout(branch_box)
        branch_box_layout.addWidget(self.branch_editor)

        documents_box = QGroupBox("Документы")
        documents_box_layout = QVBoxLayout(documents_box)
        documents_box_layout.addWidget(self.documents_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(intro_form)
        layout.addWidget(search_box)
        layout.addWidget(branch_box)
        layout.addWidget(documents_box)

    def load(self, draft: ClinicalDraft) -> None:
        """Заполнить редактор значениями ``ClinicalDraft`` (открытие кейса на правку)."""
        self.intro_edit.setText(draft.intro)
        self.search_editor.load(draft.search)
        self.branch_editor.load(draft.branch)
        self.documents_editor.load(draft.documents)

    def to_draft(self) -> ClinicalDraft:
        """Собрать ``ClinicalDraft`` из вступления, поиска, развилки и документов."""
        return ClinicalDraft(
            intro=self.intro_edit.text(),
            search=self.search_editor.to_draft(),
            branch=self.branch_editor.to_draft(),
            documents=self.documents_editor.to_draft(),
        )
