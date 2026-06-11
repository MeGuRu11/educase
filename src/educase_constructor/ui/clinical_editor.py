"""Редактор этапа 2 «Клинико-эпидемиологический диагноз» (Constructor): поиск + развилка.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода и вложенные редакторы — точки доступа для тестов. Сборка значений в драфт — через
``to_draft``. Документы — слот под отдельный заход; здесь не добавляются.
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
from educase_constructor.ui.search_editor import SearchEditor
from educase_core.application.case_builder import ClinicalDraft


class ClinicalEditor(QWidget):
    """Редактор этапа «Клинический»: вступление, контекстный поиск и точка ветвления."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.search_editor = SearchEditor(self)
        self.branch_editor = BranchEditor(self)

        intro_form = QFormLayout()
        intro_form.addRow("Вступление", self.intro_edit)

        search_box = QGroupBox("Поиск")
        search_box_layout = QVBoxLayout(search_box)
        search_box_layout.addWidget(self.search_editor)

        branch_box = QGroupBox("Развилка")
        branch_box_layout = QVBoxLayout(branch_box)
        branch_box_layout.addWidget(self.branch_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(intro_form)
        layout.addWidget(search_box)
        layout.addWidget(branch_box)

    def to_draft(self) -> ClinicalDraft:
        """Собрать ``ClinicalDraft`` из вступления, поиска и развилки."""
        return ClinicalDraft(
            intro=self.intro_edit.text(),
            search=self.search_editor.to_draft(),
            branch=self.branch_editor.to_draft(),
        )
