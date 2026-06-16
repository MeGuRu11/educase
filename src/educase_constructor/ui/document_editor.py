"""Редакторы заданий по документам (Constructor): вариант, задание и список заданий.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода, списки вложенных редакторов и кнопки — точки доступа для тестов. Сборка значений в
драфты — через ``to_draft``; шаблон обманки отбрасывается на сборке (``template=None``).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.icons import load_icon
from educase_constructor.ui.list_helpers import (
    make_placeholder,
    refresh_placeholder,
    wrap_in_card,
)
from educase_constructor.ui.template_editor import TemplateEditor
from educase_core.application.case_builder import (
    DocumentOptionDraft,
    DocumentTaskDraft,
)


class DocumentOptionEditor(QWidget):
    """Редактор варианта документа: заголовок, флаг верного выбора и встроенный шаблон.

    Шаблон заполняется только для верного варианта; для обманки сборка этапа ставит
    ``template=None`` независимо от содержимого редактора шаблона.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.title_edit = QLineEdit(self)
        self.correct_checkbox = QCheckBox("Верный документ", self)
        self.correct_checkbox.setObjectName("criticalToggle")
        self.template_editor = TemplateEditor(self)
        self.template_editor.setVisible(False)
        self.correct_checkbox.toggled.connect(self.template_editor.setVisible)

        title_form = QFormLayout()
        title_form.addRow("Название документа", self.title_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(title_form)
        layout.addWidget(self.correct_checkbox)
        layout.addWidget(self.template_editor)

    def to_draft(self) -> DocumentOptionDraft:
        """Собрать ``DocumentOptionDraft`` из заголовка, флага и редактора шаблона."""
        return DocumentOptionDraft(
            title=self.title_edit.text(),
            is_correct=self.correct_checkbox.isChecked(),
            template=self.template_editor.to_draft(),
        )


class DocumentTaskEditor(QWidget):
    """Редактор задания по документу: формулировка + список редакторов вариантов."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.prompt_edit = QLineEdit(self)

        self.option_editors: list[DocumentOptionEditor] = []
        self._option_cards: list[QGroupBox] = []

        self.add_option_button = QPushButton("Добавить", self)
        self.add_option_button.setIcon(load_icon("add"))
        self.remove_option_button = QPushButton("Удалить", self)
        self.remove_option_button.setIcon(load_icon("delete"))
        self.add_option_button.clicked.connect(self.add_option)
        self.remove_option_button.clicked.connect(self.remove_last_option)

        option_buttons = QHBoxLayout()
        option_buttons.addWidget(self.add_option_button)
        option_buttons.addWidget(self.remove_option_button)
        option_buttons.addStretch(1)

        self._options_layout = QVBoxLayout()

        prompt_form = QFormLayout()
        prompt_form.addRow("Формулировка задания", self.prompt_edit)

        layout = QVBoxLayout(self)
        layout.addLayout(prompt_form)
        layout.addLayout(option_buttons)
        layout.addLayout(self._options_layout)

    def add_option(self) -> None:
        """Добавить редактор нового варианта документа в конец списка."""
        editor = DocumentOptionEditor(self)
        card = wrap_in_card(editor, f"Документ {len(self.option_editors) + 1}")
        self.option_editors.append(editor)
        self._option_cards.append(card)
        self._options_layout.addWidget(card)

    def remove_last_option(self) -> None:
        """Удалить последний редактор варианта (если он есть)."""
        if not self.option_editors:
            return
        self.option_editors.pop()
        card = self._option_cards.pop()
        self._options_layout.removeWidget(card)
        card.deleteLater()

    def to_draft(self) -> DocumentTaskDraft:
        """Собрать ``DocumentTaskDraft`` из формулировки и всех редакторов вариантов."""
        return DocumentTaskDraft(
            prompt=self.prompt_edit.text(),
            options=tuple(editor.to_draft() for editor in self.option_editors),
        )


class DocumentListEditor(QWidget):
    """Редактор списка заданий по документам этапа."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.task_editors: list[DocumentTaskEditor] = []
        self._task_cards: list[QGroupBox] = []

        self.add_task_button = QPushButton("Добавить", self)
        self.add_task_button.setIcon(load_icon("add"))
        self.remove_task_button = QPushButton("Удалить", self)
        self.remove_task_button.setIcon(load_icon("delete"))
        self.add_task_button.clicked.connect(self.add_task)
        self.remove_task_button.clicked.connect(self.remove_last_task)

        task_buttons = QHBoxLayout()
        task_buttons.addWidget(self.add_task_button)
        task_buttons.addWidget(self.remove_task_button)
        task_buttons.addStretch(1)

        self._empty_label = make_placeholder("Пока не добавлено ни одного задания")

        self._tasks_layout = QVBoxLayout()

        layout = QVBoxLayout(self)
        layout.addLayout(task_buttons)
        layout.addWidget(self._empty_label)
        layout.addLayout(self._tasks_layout)

        self._refresh_empty()

    def add_task(self) -> None:
        """Добавить редактор нового задания в конец списка."""
        editor = DocumentTaskEditor(self)
        card = wrap_in_card(editor, f"Задание {len(self.task_editors) + 1}")
        self.task_editors.append(editor)
        self._task_cards.append(card)
        self._tasks_layout.addWidget(card)
        self._refresh_empty()

    def remove_last_task(self) -> None:
        """Удалить последний редактор задания (если он есть)."""
        if not self.task_editors:
            return
        self.task_editors.pop()
        card = self._task_cards.pop()
        self._tasks_layout.removeWidget(card)
        card.deleteLater()
        self._refresh_empty()

    def _refresh_empty(self) -> None:
        """Обновить видимость подсказки пустого состояния списка заданий."""
        refresh_placeholder(self._empty_label, is_empty=len(self.task_editors) == 0)

    def to_draft(self) -> tuple[DocumentTaskDraft, ...]:
        """Собрать драфты всех заданий по документам."""
        return tuple(editor.to_draft() for editor in self.task_editors)
