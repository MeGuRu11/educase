"""Редактор контекстного поиска этапа (Constructor): точки вскрытия информации.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода, список редакторов точек и кнопки — точки доступа для тестов. Сборка значений в драфт —
через ``to_draft``.
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

from educase_constructor.ui.synonym_editor import SynonymSetEditor
from educase_core.application.case_builder import SearchDraft, SearchEntryDraft


class SearchEntryEditor(QWidget):
    """Редактор одной точки поиска: триггеры (синонимы), вскрываемый текст и ассеты."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.triggers = SynonymSetEditor(self)
        self.reveal_text_edit = QLineEdit(self)
        self.reveal_assets_edit = QLineEdit(self)

        form = QFormLayout()
        form.addRow("Вскрываемый текст", self.reveal_text_edit)
        form.addRow("Ассеты (id через запятую)", self.reveal_assets_edit)

        layout = QVBoxLayout(self)
        layout.addWidget(self.triggers)
        layout.addLayout(form)

    def _collect_reveal_assets(self) -> tuple[str, ...]:
        parts = (chunk.strip() for chunk in self.reveal_assets_edit.text().split(","))
        return tuple(part for part in parts if part)

    def to_draft(self) -> SearchEntryDraft:
        """Собрать ``SearchEntryDraft`` из текущих значений виджетов."""
        return SearchEntryDraft(
            triggers=self.triggers.to_draft(),
            reveal_text=self.reveal_text_edit.text(),
            reveal_assets=self._collect_reveal_assets(),
        )


class SearchEditor(QWidget):
    """Редактор поиска этапа: флаг необязательности + список редакторов точек поиска."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.optional_checkbox = QCheckBox("Поиск необязателен", self)

        self.entry_editors: list[SearchEntryEditor] = []

        self.add_entry_button = QPushButton("Добавить точку поиска", self)
        self.remove_entry_button = QPushButton("Удалить последнюю", self)
        self.add_entry_button.clicked.connect(self.add_entry)
        self.remove_entry_button.clicked.connect(self.remove_last_entry)

        entry_buttons = QHBoxLayout()
        entry_buttons.addWidget(self.add_entry_button)
        entry_buttons.addWidget(self.remove_entry_button)

        self._entries_layout = QVBoxLayout()

        entries_box = QGroupBox("Точки поиска")
        entries_box_layout = QVBoxLayout(entries_box)
        entries_box_layout.addLayout(entry_buttons)
        entries_box_layout.addLayout(self._entries_layout)

        layout = QVBoxLayout(self)
        layout.addWidget(self.optional_checkbox)
        layout.addWidget(entries_box)

    def add_entry(self) -> None:
        """Добавить редактор новой точки поиска в конец списка."""
        editor = SearchEntryEditor(self)
        self.entry_editors.append(editor)
        self._entries_layout.addWidget(editor)

    def remove_last_entry(self) -> None:
        """Удалить последний редактор точки поиска (если он есть)."""
        if not self.entry_editors:
            return
        editor = self.entry_editors.pop()
        self._entries_layout.removeWidget(editor)
        editor.deleteLater()

    def to_draft(self) -> SearchDraft:
        """Собрать ``SearchDraft`` из флага и всех редакторов точек поиска."""
        return SearchDraft(
            entries=tuple(editor.to_draft() for editor in self.entry_editors),
            optional=self.optional_checkbox.isChecked(),
        )
