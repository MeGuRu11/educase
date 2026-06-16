"""Редактор этапа 6 «Окончательный эпидемиологический диагноз» (Constructor).

Вступление, контекстный поиск, задания по документам и таймлайны (сроки наблюдения за
очагом). Без визуальной полировки: только функциональные виджеты и layout-менеджеры.
Публичные поля ввода и вложенные редакторы — точки доступа для тестов. Сборка значений в
драфт — через ``to_draft``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.document_editor import DocumentListEditor
from educase_constructor.ui.search_editor import SearchEditor
from educase_constructor.ui.timeline_editor import TimelineListEditor
from educase_core.application.case_builder import FinalDraft


class FinalEditor(QWidget):
    """Редактор этапа «Окончательный диагноз»: вступление, поиск, документы, таймлайны."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.intro_edit.setPlaceholderText("Краткое введение к этапу, которое увидит курсант")
        self.search_editor = SearchEditor(self)
        self.documents_editor = DocumentListEditor(self)
        self.timelines_editor = TimelineListEditor(self)

        intro_form = QFormLayout()
        intro_form.addRow("Вступление", self.intro_edit)

        search_box = QGroupBox("Поиск")
        search_box_layout = QVBoxLayout(search_box)
        search_box_layout.addWidget(self.search_editor)

        documents_box = QGroupBox("Документы")
        documents_box_layout = QVBoxLayout(documents_box)
        documents_box_layout.addWidget(self.documents_editor)

        timelines_box = QGroupBox("Сроки наблюдения")
        timelines_box_layout = QVBoxLayout(timelines_box)
        timelines_box_layout.addWidget(self.timelines_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(intro_form)
        layout.addWidget(search_box)
        layout.addWidget(documents_box)
        layout.addWidget(timelines_box)

    def to_draft(self) -> FinalDraft:
        """Собрать ``FinalDraft`` из вступления, поиска, документов и таймлайнов."""
        return FinalDraft(
            intro=self.intro_edit.text(),
            search=self.search_editor.to_draft(),
            documents=self.documents_editor.to_draft(),
            timelines=self.timelines_editor.to_draft(),
        )
