"""Тесты EditableTimelineWidget: заголовок-задание, скрытый эталон, добавление/удаление
строк, сбор заполненных записей через entries()."""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QTableWidgetItem
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import Timeline
from epicase_player.ui.editable_timeline_widget import EditableTimelineWidget


def _timeline_with_events() -> Timeline:
    return Timeline(
        id="tl1",
        title="Сроки наблюдения за очагом",
        events=(("01.01.2024", "Изоляция"), ("05.01.2024", "Снятие карантина")),
    )


def test_title_displayed(qtbot: QtBot) -> None:
    """Заголовок-задание (timeline.title) показывается в QGroupBox."""
    tl = _timeline_with_events()
    widget = EditableTimelineWidget(tl)
    qtbot.addWidget(widget)

    groups: list[QGroupBox] = widget.findChildren(QGroupBox)
    assert any(g.title() == tl.title for g in groups)


def test_reference_events_not_shown(qtbot: QtBot) -> None:
    """Эталонные события (timeline.events) НЕ присутствуют в виджете."""
    tl = _timeline_with_events()
    widget = EditableTimelineWidget(tl)
    qtbot.addWidget(widget)

    table = widget._table
    cell_texts = [
        widget._cell_text(r, c)
        for r in range(table.rowCount())
        for c in range(table.columnCount())
    ]
    label_texts = [lbl.text() for lbl in widget.findChildren(QLabel)]
    haystack = cell_texts + label_texts
    for date, event in tl.events:
        assert date not in haystack
        assert event not in haystack


def test_add_row_increases_row_count(qtbot: QtBot) -> None:
    """«Добавить строку» увеличивает rowCount."""
    widget = EditableTimelineWidget(_timeline_with_events())
    qtbot.addWidget(widget)

    before = widget._table.rowCount()
    widget.btn_add.click()
    assert widget._table.rowCount() == before + 1


def test_remove_row_decreases_row_count(qtbot: QtBot) -> None:
    """«Удалить строку» уменьшает rowCount."""
    widget = EditableTimelineWidget(_timeline_with_events())
    qtbot.addWidget(widget)

    before = widget._table.rowCount()
    widget.btn_remove.click()
    assert widget._table.rowCount() == before - 1


def test_entries_returns_filled_rows_and_skips_empty(qtbot: QtBot) -> None:
    """entries() возвращает заполненные строки и пропускает полностью пустые."""
    widget = EditableTimelineWidget(_timeline_with_events())
    qtbot.addWidget(widget)

    table = widget._table
    # Строка 0: только дата; строка 1: пустая (пропускается); строка 2: дата + событие.
    table.setItem(0, 0, QTableWidgetItem("01.01.2024"))
    table.setItem(2, 0, QTableWidgetItem("10.01.2024"))
    table.setItem(2, 1, QTableWidgetItem("Вспышка"))

    assert widget.entries() == (
        ("01.01.2024", ""),
        ("10.01.2024", "Вспышка"),
    )
    assert widget.timeline_id == "tl1"
