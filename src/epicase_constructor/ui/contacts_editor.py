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

from epicase_constructor.ui.asset_picker import AssetPicker
from epicase_constructor.ui.inspection_editor import InspectionEditor
from epicase_constructor.ui.scheme_zone_editor import SchemeZoneEditor
from epicase_core.application.case_builder import ContactsDraft


class ContactsEditor(QWidget):
    """Редактор этапа «Обследование контактных лиц»: вступление, схема, осмотр."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.intro_edit = QLineEdit(self)
        self.intro_edit.setPlaceholderText("Краткое введение к этапу, которое увидит курсант")
        self.scheme_picker = AssetPicker(self)
        self.zone_editor = SchemeZoneEditor(self)
        self.inspection_editor = InspectionEditor(self)

        self.scheme_picker.changed.connect(
            lambda: self.zone_editor.set_background(self.scheme_picker.value())
        )

        form = QFormLayout()
        form.addRow("Вступление", self.intro_edit)
        form.addRow("Схема (изображение)", self.scheme_picker)

        zones_box = QGroupBox("Зоны схемы")
        zones_box_layout = QVBoxLayout(zones_box)
        zones_box_layout.addWidget(self.zone_editor)

        inspection_box = QGroupBox("Осмотр")
        inspection_box_layout = QVBoxLayout(inspection_box)
        inspection_box_layout.addWidget(self.inspection_editor)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(zones_box)
        layout.addWidget(inspection_box)

    def load(self, draft: ContactsDraft) -> None:
        """Заполнить редактор значениями ``ContactsDraft`` (открытие кейса на правку).

        Фон схемы ставится ПЕРВЫМ (``set_ref``/``clear`` → сигнал ``changed`` →
        ``zone_editor.set_background``), и только потом восстанавливаются зоны: без фона холст
        не примет зоны.
        """
        self.intro_edit.setText(draft.intro)
        if draft.scheme is not None:
            self.scheme_picker.set_ref(draft.scheme)
        else:
            self.scheme_picker.clear()
        self.zone_editor.load_hotspots(draft.hotspots)
        self.inspection_editor.load(draft.inspection)

    def to_draft(self) -> ContactsDraft:
        """Собрать ``ContactsDraft`` из вступления, схемы и осмотра."""
        return ContactsDraft(
            intro=self.intro_edit.text(),
            scheme=self.scheme_picker.value(),
            hotspots=self.zone_editor.to_hotspots(),
            inspection=self.inspection_editor.to_draft(),
        )
