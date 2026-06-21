"""Редактор этапа 4 «Обследование объектов внешней среды» (Constructor).

Вступление, ссылка на схему (ассет по id), фото (id через запятую), задания по документам и
сверка осмотра. Без визуальной полировки: только функциональные виджеты и layout-менеджеры.
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

from educase_constructor.ui.asset_picker import AssetListPicker, AssetPicker
from educase_constructor.ui.document_editor import DocumentListEditor
from educase_constructor.ui.inspection_editor import InspectionEditor
from educase_constructor.ui.scheme_zone_editor import SchemeZoneEditor
from educase_core.application.case_builder import EnvironmentDraft


class EnvironmentEditor(QWidget):
    """Редактор этапа «Обследование объектов внешней среды»: схема, фото, документы, осмотр."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.intro_edit.setPlaceholderText("Краткое введение к этапу, которое увидит курсант")
        self.scheme_picker = AssetPicker(self)
        self.zone_editor = SchemeZoneEditor(self)
        self.photos_picker = AssetListPicker(self)
        self.documents_editor = DocumentListEditor(self)
        self.inspection_editor = InspectionEditor(self)

        self.scheme_picker.changed.connect(
            lambda: self.zone_editor.set_background(self.scheme_picker.value())
        )

        form = QFormLayout()
        form.addRow("Вступление", self.intro_edit)
        form.addRow("Схема (изображение)", self.scheme_picker)
        form.addRow("Фото (изображения)", self.photos_picker)

        zones_box = QGroupBox("Зоны схемы")
        zones_box_layout = QVBoxLayout(zones_box)
        zones_box_layout.addWidget(self.zone_editor)

        documents_box = QGroupBox("Документы")
        documents_box_layout = QVBoxLayout(documents_box)
        documents_box_layout.addWidget(self.documents_editor)

        inspection_box = QGroupBox("Осмотр")
        inspection_box_layout = QVBoxLayout(inspection_box)
        inspection_box_layout.addWidget(self.inspection_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(zones_box)
        layout.addWidget(documents_box)
        layout.addWidget(inspection_box)

    def load(self, draft: EnvironmentDraft) -> None:
        """Заполнить редактор значениями ``EnvironmentDraft`` (открытие кейса на правку).

        Фон схемы ставится ПЕРВЫМ (``set_ref``/``clear`` → сигнал ``changed`` →
        ``zone_editor.set_background``), и только потом восстанавливаются зоны: без фона холст
        не примет зоны. Фото/документы/осмотр заполняются симметрично ``to_draft``.
        """
        self.intro_edit.setText(draft.intro)
        if draft.scheme is not None:
            self.scheme_picker.set_ref(draft.scheme)
        else:
            self.scheme_picker.clear()
        self.zone_editor.load_hotspots(draft.hotspots)
        self.photos_picker.load(draft.photos)
        self.documents_editor.load(draft.documents)
        self.inspection_editor.load(draft.inspection)

    def to_draft(self) -> EnvironmentDraft:
        """Собрать ``EnvironmentDraft`` из вступления, схемы, фото, документов и осмотра."""
        return EnvironmentDraft(
            intro=self.intro_edit.text(),
            scheme=self.scheme_picker.value(),
            hotspots=self.zone_editor.to_hotspots(),
            photos=self.photos_picker.value(),
            documents=self.documents_editor.to_draft(),
            inspection=self.inspection_editor.to_draft(),
        )
