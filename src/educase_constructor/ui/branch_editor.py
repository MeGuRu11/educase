"""Редактор точки ветвления «Вариант B» (Constructor): формулировка + опции выбора.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода, список редакторов опций и кнопки — точки доступа для тестов. Сборка значений в драфт —
через ``to_draft``.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_core.application.case_builder import BranchDraft, BranchOptionDraft


class BranchOptionEditor(QWidget):
    """Редактор одной опции развилки: подпись + флаг верного выбора."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.label_edit = QLineEdit(self)
        self.correct_checkbox = QCheckBox("Верный вариант", self)

        layout = QHBoxLayout(self)
        layout.addWidget(self.label_edit)
        layout.addWidget(self.correct_checkbox)

    def to_draft(self) -> BranchOptionDraft:
        """Собрать ``BranchOptionDraft`` из текущих значений виджетов."""
        return BranchOptionDraft(
            label=self.label_edit.text(),
            is_correct=self.correct_checkbox.isChecked(),
        )


class BranchEditor(QWidget):
    """Редактор развилки: формулировка вопроса + список редакторов опций."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.prompt_edit = QLineEdit(self)

        self.option_editors: list[BranchOptionEditor] = []

        self.add_option_button = QPushButton("Добавить вариант", self)
        self.remove_option_button = QPushButton("Удалить последний", self)
        self.add_option_button.clicked.connect(self.add_option)
        self.remove_option_button.clicked.connect(self.remove_last_option)

        option_buttons = QHBoxLayout()
        option_buttons.addWidget(self.add_option_button)
        option_buttons.addWidget(self.remove_option_button)

        self._options_layout = QVBoxLayout()

        options_box = QGroupBox("Варианты выбора")
        options_box_layout = QVBoxLayout(options_box)
        options_box_layout.addWidget(self.prompt_edit)
        options_box_layout.addLayout(option_buttons)
        options_box_layout.addLayout(self._options_layout)

        layout = QVBoxLayout(self)
        layout.addWidget(options_box)

    def add_option(self) -> None:
        """Добавить редактор новой опции в конец списка."""
        editor = BranchOptionEditor(self)
        self.option_editors.append(editor)
        self._options_layout.addWidget(editor)

    def remove_last_option(self) -> None:
        """Удалить последний редактор опции (если он есть)."""
        if not self.option_editors:
            return
        editor = self.option_editors.pop()
        self._options_layout.removeWidget(editor)
        editor.deleteLater()

    def to_draft(self) -> BranchDraft:
        """Собрать ``BranchDraft`` из формулировки и всех редакторов опций."""
        return BranchDraft(
            prompt=self.prompt_edit.text(),
            options=tuple(editor.to_draft() for editor in self.option_editors),
        )
