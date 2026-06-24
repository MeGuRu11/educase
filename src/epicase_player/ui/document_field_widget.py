"""Виджет одного поля документа: метка + поле ввода по типу (ADR-006/007)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

from epicase_core.domain.documents import DocumentField, FieldType


class DocumentFieldWidget(QWidget):
    """Строка «метка + поле ввода» для одного DocumentField.

    TEXT / NUMBER / DATE → QLineEdit; CHOICE → QComboBox с опциями поля.
    Сверка правильности делегируется в DocumentField.check без логики в UI (ADR-006/007).
    """

    def __init__(self, field: DocumentField, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.field = field

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel(field.label))

        if field.type == FieldType.CHOICE:
            combo = QComboBox()
            combo.setPlaceholderText("— выберите —")
            for opt in field.options:
                combo.addItem(opt)
            combo.setCurrentIndex(-1)
            self.input: QLineEdit | QComboBox = combo
        else:
            self.input = QLineEdit()
            if field.type == FieldType.NUMBER:
                self.input.setPlaceholderText("Например: 25")
            elif field.type == FieldType.DATE:
                self.input.setPlaceholderText("ДД.ММ.ГГГГ")
            else:
                self.input.setPlaceholderText("Введите ответ")

        layout.addWidget(self.input)

    def answer(self) -> str:
        """Текущее значение; для QComboBox — пусто при плейсхолдере (currentIndex < 0)."""
        if isinstance(self.input, QComboBox):
            return "" if self.input.currentIndex() < 0 else self.input.currentText()
        return self.input.text()

    def check(self) -> bool:
        """Сверить текущий ответ с правилом поля (делегирует в DocumentField.check)."""
        return self.field.check(self.answer())
