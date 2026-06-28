"""Тесты TimelineWidget: отображение событий таймлайна."""
from __future__ import annotations

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_core.domain.stages import Timeline
from epicase_player.ui.timeline_widget import TimelineWidget


def test_events_displayed(qtbot: QtBot) -> None:
    """События таймлайна отображаются построчно «дата — событие»."""
    timeline = Timeline(
        id="tl1",
        title="Сроки наблюдения",
        events=(
            ("01.01.2024", "Начало наблюдения"),
            ("15.01.2024", "Плановая проверка"),
        ),
    )
    w = TimelineWidget(timeline)
    qtbot.addWidget(w)

    texts = [lbl.text() for lbl in w.findChildren(QLabel)]
    assert any("01.01.2024" in t and "Начало наблюдения" in t for t in texts)
    assert any("15.01.2024" in t and "Плановая проверка" in t for t in texts)


def test_empty_events_no_crash(qtbot: QtBot) -> None:
    """Таймлайн без событий — виджет создаётся без ошибок."""
    timeline = Timeline(id="tl2", title="Пустой таймлайн", events=())
    w = TimelineWidget(timeline)
    qtbot.addWidget(w)
