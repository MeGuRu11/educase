"""Редактор шаблона документа (Constructor): заголовок + список полей.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода, список редакторов полей и кнопки — точки доступа для тестов. Сборка значений в драфт —
через ``to_draft``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.field_editor import FieldEditor
from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import wrap_in_card
from educase_core.application.case_builder import TemplateDraft


class TemplateEditor(QWidget):
    """Редактор шаблона документа: заголовок + список редакторов полей."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Название документа")

        self.field_editors: list[FieldEditor] = []
        self._field_cards: list[QGroupBox] = []

        self.add_field_button = QPushButton("Добавить", self)
        self.add_field_button.setIcon(load_icon("add"))
        self.remove_field_button = QPushButton("Удалить", self)
        self.remove_field_button.setIcon(load_icon("delete"))
        self.add_field_button.clicked.connect(self.add_field)
        self.remove_field_button.clicked.connect(self.remove_last_field)

        field_buttons = QHBoxLayout()
        field_buttons.addWidget(self.add_field_button)
        field_buttons.addWidget(self.remove_field_button)
        field_buttons.addStretch(1)

        self._fields_layout = QVBoxLayout()

        title_form = QFormLayout()
        title_form.addRow("Заголовок шаблона", self.title_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(title_form)
        layout.addLayout(field_buttons)
        layout.addLayout(self._fields_layout)

    def add_field(self) -> None:
        """Добавить редактор нового поля в конец списка."""
        editor = FieldEditor(self)
        card = wrap_in_card(editor, f"Поле {len(self.field_editors) + 1}")
        self.field_editors.append(editor)
        self._field_cards.append(card)
        self._fields_layout.addWidget(card)

    def remove_last_field(self) -> None:
        """Удалить последний редактор поля (если он есть)."""
        if not self.field_editors:
            return
        self.field_editors.pop()
        card = self._field_cards.pop()
        self._fields_layout.removeWidget(card)
        card.deleteLater()

    def load(self, draft: TemplateDraft) -> None:
        """Заполнить редактор значениями ``TemplateDraft`` (открытие кейса на правку).

        Текущие поля удаляются и пересобираются из ``draft.fields`` (симметрично ``to_draft``).
        """
        self.title_edit.setText(draft.title)
        while self.field_editors:
            self.remove_last_field()
        for field in draft.fields:
            self.add_field()
            self.field_editors[-1].load(field)

    def to_draft(self) -> TemplateDraft:
        """Собрать ``TemplateDraft`` из заголовка и всех редакторов полей."""
        return TemplateDraft(
            title=self.title_edit.text(),
            fields=tuple(editor.to_draft() for editor in self.field_editors),
        )
