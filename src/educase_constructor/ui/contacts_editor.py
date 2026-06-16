"""Редактор этапа 3 «Обследование контактных лиц» (Constructor).

Вступление, ссылка на схему (ассет по id) и сверка осмотра. Без визуальной полировки:
только функциональные виджеты и layout-менеджеры. Публичные поля ввода и вложенный редактор
осмотра — точки доступа для тестов. Сборка значений в драфт — через ``to_draft``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.asset_picker import AssetPicker
from educase_constructor.ui.inspection_editor import InspectionEditor
from educase_core.application.case_builder import ContactsDraft


class ContactsEditor(QWidget):
    """Редактор этапа «Обследование контактных лиц»: вступление, схема, осмотр."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.intro_edit.setPlaceholderText("Краткое введение к этапу, которое увидит курсант")
        self.scheme_picker = AssetPicker(self)
        self.inspection_editor = InspectionEditor(self)

        form = QFormLayout()
        form.addRow("Вступление", self.intro_edit)
        form.addRow("Схема (изображение)", self.scheme_picker)

        inspection_box = QGroupBox("Осмотр")
        inspection_box_layout = QVBoxLayout(inspection_box)
        inspection_box_layout.addWidget(self.inspection_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(inspection_box)

    def to_draft(self) -> ContactsDraft:
        """Собрать ``ContactsDraft`` из вступления, схемы и осмотра."""
        return ContactsDraft(
            intro=self.intro_edit.text(),
            scheme=self.scheme_picker.value(),
            inspection=self.inspection_editor.to_draft(),
        )
