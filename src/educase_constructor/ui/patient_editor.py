"""Редактор одной карточки пациента (Constructor, этап «Пациенты»).

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода и кнопки — точки доступа для тестов. Сборка значений в домен — через ``to_draft``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.asset_picker import AssetListPicker
from educase_constructor.ui.list_helpers import make_placeholder
from educase_core.application.case_builder import PatientDraft


class PatientEditor(QWidget):
    """Редактор карточки пациента: заголовок, таблица «поле/значение», строка ассетов.

    Технический id карточки преподавателем не вводится — его генерирует ``build_case``.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("ФИО или краткое обозначение пациента")
        self.assets_picker = AssetListPicker(self)

        self.fields_table = QTableWidget(0, 2, self)
        self.fields_table.setHorizontalHeaderLabels(["Поле", "Значение"])
        self.fields_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.fields_table.setMinimumHeight(140)

        self.fields_hint = make_placeholder(
            "Характеристики пациента (строки «Поле/Значение»): "
            "например, возраст, жалобы, диагноз, температура."
        )

        self.add_row_button = QPushButton("+ строка", self)
        self.remove_row_button = QPushButton("− строка", self)
        self.add_row_button.clicked.connect(self.add_field_row)
        self.remove_row_button.clicked.connect(self.remove_last_field_row)

        form = QFormLayout()
        form.addRow("Заголовок", self.title_edit)
        form.addRow("Изображения карточки", self.assets_picker)

        row_buttons = QHBoxLayout()
        row_buttons.addWidget(self.add_row_button)
        row_buttons.addWidget(self.remove_row_button)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.fields_hint)
        layout.addWidget(self.fields_table)
        layout.addLayout(row_buttons)

    def add_field_row(self) -> None:
        """Добавить пустую строку «поле/значение»."""
        self.fields_table.insertRow(self.fields_table.rowCount())

    def remove_last_field_row(self) -> None:
        """Удалить последнюю строку таблицы полей (если она есть)."""
        count = self.fields_table.rowCount()
        if count:
            self.fields_table.removeRow(count - 1)

    def _collect_fields(self) -> tuple[tuple[str, str], ...]:
        rows: list[tuple[str, str]] = []
        for row in range(self.fields_table.rowCount()):
            key_item = self.fields_table.item(row, 0)
            value_item = self.fields_table.item(row, 1)
            key = key_item.text() if key_item is not None else ""
            value = value_item.text() if value_item is not None else ""
            rows.append((key, value))
        return tuple(rows)

    def load(self, draft: PatientDraft) -> None:
        """Заполнить редактор значениями ``PatientDraft`` (открытие кейса на правку).

        Таблица полей полностью пересобирается; ассеты восстанавливаются из памяти через
        ``AssetListPicker.load`` (байты из архива, имена = ``asset_id``).
        """
        self.title_edit.setText(draft.title)
        self.fields_table.setRowCount(0)
        for key, value in draft.fields:
            row = self.fields_table.rowCount()
            self.fields_table.insertRow(row)
            self.fields_table.setItem(row, 0, QTableWidgetItem(key))
            self.fields_table.setItem(row, 1, QTableWidgetItem(value))
        self.assets_picker.load(draft.assets)

    def to_draft(self) -> PatientDraft:
        """Собрать ``PatientDraft`` из текущих значений виджетов."""
        return PatientDraft(
            title=self.title_edit.text(),
            fields=self._collect_fields(),
            assets=self.assets_picker.value(),
        )
