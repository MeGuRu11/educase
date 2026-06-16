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
        self._queries: list[str] = []

        layout = QVBoxLayout(self)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ключевое слово или фраза")
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

    def queries(self) -> tuple[str, ...]:
        """Накопленные непустые запросы в порядке ввода (для SearchLog прохождения)."""
        return tuple(self._queries)

    def _show_result(self, text: str, *, muted: bool) -> None:
        """Показать результат, применив или сняв стиль mutedHint."""
        self.result.setObjectName("mutedHint" if muted else "")
        self.result.setText(text)
        self.result.style().unpolish(self.result)
        self.result.style().polish(self.result)

    def on_search(self) -> None:
        """Выполнить поиск по тексту поля ввода."""
        q = self.input.text()
        if not q.strip():
            self._show_result("Введите запрос", muted=True)
            self._last_entry = None
            return
        self._queries.append(q.strip())
        entry = self._search.find(q)
        if entry is None:
            self._show_result("Ничего не найдено", muted=True)
            self._last_entry = None
            return
        self._last_entry = entry
        text = entry.reveal_text
        if entry.reveal_assets:
            # TODO: рендер ассетов — показываем id как заглушку
            asset_ids = ", ".join(entry.reveal_assets)
            text = f"{text}\n\nМатериалы: {asset_ids}"
        self._show_result(text, muted=False)
