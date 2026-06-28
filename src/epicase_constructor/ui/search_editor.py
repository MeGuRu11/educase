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

from epicase_constructor.ui.asset_picker import AssetListPicker
from epicase_constructor.ui.icons import load_icon
from epicase_constructor.ui.list_helpers import make_placeholder, refresh_placeholder, wrap_in_card
from epicase_constructor.ui.synonym_editor import SynonymSetEditor
from epicase_core.application.case_builder import SearchDraft, SearchEntryDraft


class SearchEntryEditor(QWidget):
    """Редактор одной точки поиска: триггеры (синонимы), вскрываемый текст и ассеты."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.triggers = SynonymSetEditor(self)
        self.reveal_text_edit = QLineEdit(self)
        self.reveal_text_edit.setPlaceholderText(
            "Текст, который откроется курсанту при совпадении ключа"
        )
        self.reveal_assets_picker = AssetListPicker(self)

        form = QFormLayout()
        form.addRow("Вскрываемый текст", self.reveal_text_edit)
        form.addRow("Изображения точки", self.reveal_assets_picker)

        layout = QVBoxLayout(self)
        layout.addWidget(self.triggers)
        layout.addLayout(form)

    def load(self, draft: SearchEntryDraft) -> None:
        """Заполнить виджеты значениями ``SearchEntryDraft`` (открытие кейса на правку)."""
        self.triggers.load(draft.triggers)
        self.reveal_text_edit.setText(draft.reveal_text)
        self.reveal_assets_picker.load(draft.reveal_assets)

    def to_draft(self) -> SearchEntryDraft:
        """Собрать ``SearchEntryDraft`` из текущих значений виджетов."""
        return SearchEntryDraft(
            triggers=self.triggers.to_draft(),
            reveal_text=self.reveal_text_edit.text(),
            reveal_assets=self.reveal_assets_picker.value(),
        )


class SearchEditor(QWidget):
    """Редактор поиска этапа: флаг необязательности + список редакторов точек поиска."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.optional_checkbox = QCheckBox("Поиск необязателен", self)

        self.entry_editors: list[SearchEntryEditor] = []
        self._entry_cards: list[QGroupBox] = []

        self.add_entry_button = QPushButton("Добавить", self)
        self.add_entry_button.setIcon(load_icon("add"))
        self.remove_entry_button = QPushButton("Удалить", self)
        self.remove_entry_button.setIcon(load_icon("delete"))
        self.add_entry_button.clicked.connect(self.add_entry)
        self.remove_entry_button.clicked.connect(self.remove_last_entry)

        entry_buttons = QHBoxLayout()
        entry_buttons.addWidget(self.add_entry_button)
        entry_buttons.addWidget(self.remove_entry_button)
        entry_buttons.addStretch(1)

        self._empty_label = make_placeholder("Пока не добавлено ни одной точки поиска")

        self._entries_layout = QVBoxLayout()

        entries_box = QGroupBox("Точки поиска")
        entries_box_layout = QVBoxLayout(entries_box)
        entries_box_layout.addLayout(entry_buttons)
        entries_box_layout.addWidget(self._empty_label)
        entries_box_layout.addLayout(self._entries_layout)

        layout = QVBoxLayout(self)
        layout.addWidget(self.optional_checkbox)
        layout.addWidget(entries_box)

        self._refresh_empty()

    def add_entry(self) -> None:
        """Добавить редактор новой точки поиска в конец списка."""
        editor = SearchEntryEditor(self)
        self.entry_editors.append(editor)
        card = wrap_in_card(editor, f"Точка поиска {len(self.entry_editors)}")
        self._entry_cards.append(card)
        self._entries_layout.addWidget(card)
        self._refresh_empty()

    def remove_last_entry(self) -> None:
        """Удалить последний редактор точки поиска (если он есть)."""
        if not self.entry_editors:
            return
        self.entry_editors.pop()
        card = self._entry_cards.pop()
        self._entries_layout.removeWidget(card)
        card.deleteLater()
        self._refresh_empty()

    def _refresh_empty(self) -> None:
        """Обновить видимость подсказки пустого состояния списка точек поиска."""
        refresh_placeholder(self._empty_label, is_empty=len(self.entry_editors) == 0)

    def load(self, draft: SearchDraft) -> None:
        """Заполнить редактор значениями ``SearchDraft`` (открытие кейса на правку).

        Текущие точки удаляются и пересобираются из ``draft.entries`` (симметрично ``to_draft``).
        """
        self.optional_checkbox.setChecked(draft.optional)
        while self.entry_editors:
            self.remove_last_entry()
        for entry in draft.entries:
            self.add_entry()
            self.entry_editors[-1].load(entry)
        self._refresh_empty()

    def to_draft(self) -> SearchDraft:
        """Собрать ``SearchDraft`` из флага и всех редакторов точек поиска."""
        return SearchDraft(
            entries=tuple(editor.to_draft() for editor in self.entry_editors),
            optional=self.optional_checkbox.isChecked(),
        )
