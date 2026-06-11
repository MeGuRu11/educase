"""Виджет строгого поиска по ключевым словам (ADR-006)."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.search import KeywordSearch, SearchEntry


class SearchWidget(QWidget):
    """Виджет поиска: поле ввода, кнопка «Найти», область результата.

    Поиск строгий — делегирует KeywordSearch.find без собственной фильтрации (ADR-006).
    Ошибочный или пустой запрос не блокирует работу (ADR-008).
    """

    def __init__(self, search: KeywordSearch, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._search = search
        self._last_entry: SearchEntry | None = None

        layout = QVBoxLayout(self)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.btn_search = QPushButton("Найти")
        input_row.addWidget(self.input)
        input_row.addWidget(self.btn_search)
        layout.addLayout(input_row)

        self.result = QLabel()
        self.result.setWordWrap(True)
        layout.addWidget(self.result)

        self.btn_search.clicked.connect(self.on_search)
        self.input.returnPressed.connect(self.on_search)

    @property
    def search(self) -> KeywordSearch:
        """Модель поиска, переданная при создании."""
        return self._search

    @property
    def last_entry(self) -> SearchEntry | None:
        """Последний найденный SearchEntry; None если запрос пустой или не найден."""
        return self._last_entry

    def on_search(self) -> None:
        """Выполнить поиск по тексту поля ввода."""
        q = self.input.text()
        if not q.strip():
            self.result.setText("Введите запрос")
            self._last_entry = None
            return
        entry = self._search.find(q)
        if entry is None:
            self.result.setText("Ничего не найдено")
            self._last_entry = None
            return
        self._last_entry = entry
        text = entry.reveal_text
        if entry.reveal_assets:
            # TODO: рендер ассетов — показываем id как заглушку
            asset_ids = ", ".join(entry.reveal_assets)
            text = f"{text}\n\nМатериалы: {asset_ids}"
        self.result.setText(text)
