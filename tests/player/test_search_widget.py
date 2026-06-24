"""Тесты виджета строгого поиска по ключевым словам (ADR-006)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from epicase_core.domain.search import KeywordSearch, SearchEntry, SynonymSet
from epicase_player.ui.search_widget import SearchWidget


def _make_search() -> KeywordSearch:
    return KeywordSearch(
        entries=(
            SearchEntry(
                id="e1",
                triggers=SynonymSet(canonical="сальмонеллёз", synonyms=("salmonella",)),
                reveal_text="Сальмонеллёз: информация о заболевании.",
            ),
            SearchEntry(
                id="e2",
                triggers=SynonymSet(canonical="тиф", synonyms=("typhoid",)),
                reveal_text="Брюшной тиф: информация.",
                reveal_assets=("asset_map_01", "asset_photo_02"),
            ),
        )
    )


def test_exact_canonical_found(qtbot: QtBot) -> None:
    """Канонический термин → last_entry не None, reveal_text в result."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("сальмонеллёз")
    widget.btn_search.click()

    assert widget.last_entry is not None
    assert widget.last_entry.id == "e1"
    assert "Сальмонеллёз: информация о заболевании." in widget.result.text()


def test_exact_synonym_different_case(qtbot: QtBot) -> None:
    """Синоним с другим регистром и пробелами → находит запись."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("  Salmonella  ")
    widget.btn_search.click()

    assert widget.last_entry is not None
    assert widget.last_entry.id == "e1"


def test_partial_match_not_found(qtbot: QtBot) -> None:
    """Частичное совпадение не срабатывает — строгий поиск (ADR-006)."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("сальм")
    widget.btn_search.click()

    assert widget.last_entry is None
    assert widget.result.text() == "Ничего не найдено"


def test_typo_not_found(qtbot: QtBot) -> None:
    """Опечатка не срабатывает — fuzzy-матчинга нет (ADR-006)."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("сальмонелёз")
    widget.btn_search.click()

    assert widget.last_entry is None
    assert widget.result.text() == "Ничего не найдено"


def test_empty_query_calm_message(qtbot: QtBot) -> None:
    """Пустой запрос — спокойное сообщение, без падения."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("")
    widget.btn_search.click()

    assert widget.result.text() == "Введите запрос"
    assert widget.last_entry is None


def test_whitespace_only_query(qtbot: QtBot) -> None:
    """Запрос из одних пробелов обрабатывается как пустой."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("   ")
    widget.btn_search.click()

    assert widget.result.text() == "Введите запрос"
    assert widget.last_entry is None


def test_reveal_assets_shown_as_id_list(qtbot: QtBot) -> None:
    """reveal_assets отображаются как список id в result (заглушка)."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("тиф")
    widget.btn_search.click()

    assert widget.last_entry is not None
    assert widget.last_entry.id == "e2"
    result_text = widget.result.text()
    assert "Брюшной тиф: информация." in result_text
    assert "asset_map_01" in result_text
    assert "asset_photo_02" in result_text


def test_no_assets_no_materiali_line(qtbot: QtBot) -> None:
    """Запись без reveal_assets — строка «Материалы:» не появляется."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("сальмонеллёз")
    widget.btn_search.click()

    assert "Материалы:" not in widget.result.text()


def test_return_pressed_same_as_button(qtbot: QtBot) -> None:
    """Enter в поле ввода даёт тот же результат, что нажатие кнопки."""
    widget = SearchWidget(_make_search())
    qtbot.addWidget(widget)

    widget.input.setText("сальмонеллёз")
    qtbot.keyClick(widget.input, Qt.Key.Key_Return)  # type: ignore[no-untyped-call]  # pytest-qt без стабов

    assert widget.last_entry is not None
    assert widget.last_entry.id == "e1"
