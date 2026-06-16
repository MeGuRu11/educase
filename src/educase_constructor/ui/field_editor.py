"""Редактор поля документа (Constructor): подпись, тип, обязательность и правило сверки.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода — точки доступа для тестов. Под-форма правила переключается стеком по выбранному типу;
``to_draft`` собирает сырые значения всех под-форм — нужные выбирает ``_build_field``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QLineEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.synonym_editor import SynonymSetEditor
from educase_core.application.case_builder import FieldDraft
from educase_core.domain import FieldType

# Русские подписи типов поля для combo. Значение (англ. ``FieldType.value``) хранится в
# userData и идёт в драфт — домен и маппинг сборки видят прежние англ. значения.
_TYPE_LABELS: dict[FieldType, str] = {
    FieldType.TEXT: "Текст",
    FieldType.NUMBER: "Число",
    FieldType.DATE: "Дата",
    FieldType.CHOICE: "Выбор",
}


def _split_csv(text: str) -> tuple[str, ...]:
    parts = (chunk.strip() for chunk in text.split(","))
    return tuple(part for part in parts if part)


class FieldEditor(QWidget):
    """Редактор поля документа: тип определяет активную под-форму правила сверки."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.label_edit = QLineEdit(self)
        self.label_edit.setPlaceholderText("Подпись поля, например: Число заболевших")
        self.type_combo = QComboBox(self)
        for field_type in FieldType:
            self.type_combo.addItem(_TYPE_LABELS[field_type], field_type.value)
        self.required_checkbox = QCheckBox("Обязательное поле", self)
        self.required_checkbox.setObjectName("criticalToggle")
        self.required_checkbox.setChecked(True)

        # Страницы стека — в порядке элементов type_combo (порядок FieldType).
        self.keywords_editor = SynonymSetEditor(self)

        number_page = QWidget(self)
        self.number_value_edit = QLineEdit(number_page)
        self.number_value_edit.setPlaceholderText("Например: 25")
        self.tolerance_edit = QLineEdit(number_page)
        self.tolerance_edit.setPlaceholderText("Отклонение, например: 2")
        self.ndigits_edit = QLineEdit(number_page)
        self.ndigits_edit.setPlaceholderText("Знаков после запятой, например: 0")
        number_form = QFormLayout(number_page)
        number_form.addRow("Значение", self.number_value_edit)
        number_form.addRow("Допуск (необязательно)", self.tolerance_edit)
        number_form.addRow("Знаков округления (необязательно)", self.ndigits_edit)

        date_page = QWidget(self)
        self.date_value_edit = QLineEdit(date_page)
        self.date_value_edit.setPlaceholderText("ДД.ММ.ГГГГ")
        date_form = QFormLayout(date_page)
        date_form.addRow("Дата (ДД.ММ.ГГГГ)", self.date_value_edit)

        choice_page = QWidget(self)
        self.options_edit = QLineEdit(choice_page)
        self.options_edit.setPlaceholderText("Через запятую: вариант 1, вариант 2")
        self.correct_edit = QLineEdit(choice_page)
        self.correct_edit.setPlaceholderText("Через запятую: вариант 1")
        choice_form = QFormLayout(choice_page)
        choice_form.addRow("Варианты (через запятую)", self.options_edit)
        choice_form.addRow("Верные (через запятую)", self.correct_edit)

        self.rule_stack = QStackedWidget(self)
        self.rule_stack.addWidget(self.keywords_editor)
        self.rule_stack.addWidget(number_page)
        self.rule_stack.addWidget(date_page)
        self.rule_stack.addWidget(choice_page)
        self.type_combo.currentIndexChanged.connect(self.rule_stack.setCurrentIndex)

        form = QFormLayout()
        form.addRow("Подпись поля", self.label_edit)
        form.addRow("Тип поля", self.type_combo)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.required_checkbox)
        layout.addWidget(self.rule_stack)

    def to_draft(self) -> FieldDraft:
        """Собрать ``FieldDraft`` из текущих значений виджетов всех под-форм.

        Тип поля берётся из ``currentData()`` (англ. ``FieldType.value`` в userData), а не из
        видимой русской подписи — доменный маппинг ``_build_field`` получает прежнее значение.
        """
        return FieldDraft(
            label=self.label_edit.text(),
            field_type=str(self.type_combo.currentData()),
            required=self.required_checkbox.isChecked(),
            keywords=self.keywords_editor.to_draft(),
            number_value=self.number_value_edit.text(),
            number_tolerance=self.tolerance_edit.text(),
            number_ndigits=self.ndigits_edit.text(),
            date_value=self.date_value_edit.text(),
            choice_options=_split_csv(self.options_edit.text()),
            choice_correct=_split_csv(self.correct_edit.text()),
        )
