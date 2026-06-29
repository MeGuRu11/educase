"""Tests for the shared animated start-screen shell."""

from inspect import signature

import pytest
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPixmap, QRegion
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from pytestqt.qtbot import QtBot

import epicase_ui
from epicase_ui.animated_start import (
    AnimatedStartBackground,
    AnimatedStartWidget,
    StartVariant,
)
from epicase_ui.brand_mark import BrandMarkWidget
from epicase_ui.branding import BrandAsset


def _render_transparent(widget: QWidget) -> QPixmap:
    """Render a widget onto a transparent pixmap."""
    pixmap = QPixmap(widget.size())
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    try:
        widget.render(
            painter,
            QPoint(),
            QRegion(),
            QWidget.RenderFlag.DrawChildren,
        )
    finally:
        painter.end()
    return pixmap


def _emit_application_state(state: Qt.ApplicationState) -> None:
    """Emit an application state transition from the current Qt application."""
    application = QGuiApplication.instance()
    assert isinstance(application, QGuiApplication)
    application.applicationStateChanged.emit(state)


@pytest.mark.parametrize(
    ("variant", "object_name"),
    [
        (StartVariant.CONSTRUCTOR, "constructorStartBackground"),
        (StartVariant.PLAYER, "playerStartBackground"),
    ],
)
def test_background_exposes_variant_specific_identity(
    qtbot: QtBot,
    variant: StartVariant,
    object_name: str,
) -> None:
    """Each application gets a stable public variant and object name."""
    background = AnimatedStartBackground(variant)
    qtbot.addWidget(background)

    assert background.variant is variant
    assert background.objectName() == object_name
    assert epicase_ui.StartVariant is StartVariant
    assert epicase_ui.AnimatedStartBackground is AnimatedStartBackground


def test_start_animation_uses_approved_default_intro_duration(qtbot: QtBot) -> None:
    """Both shared start widgets default to the approved 1.4-second intro."""
    del qtbot

    background_default = signature(AnimatedStartBackground).parameters[
        "intro_duration_ms"
    ].default
    shell_default = signature(AnimatedStartWidget).parameters[
        "intro_duration_ms"
    ].default

    assert background_default == 1_400
    assert shell_default == 1_400


def test_start_animation_uses_smooth_default_frame_cadence(qtbot: QtBot) -> None:
    """The shared animation uses a precise 30 FPS timer in both public widgets."""
    background = AnimatedStartBackground(StartVariant.PLAYER)
    qtbot.addWidget(background)
    timer = background.findChild(QTimer)

    assert timer is not None
    assert timer.interval() == 33
    assert timer.timerType() is Qt.TimerType.PreciseTimer
    assert (
        signature(AnimatedStartBackground).parameters["frame_interval_ms"].default
        == 33
    )
    assert (
        signature(AnimatedStartWidget).parameters["frame_interval_ms"].default == 33
    )


def test_intro_finishes_once_and_does_not_replay_after_hide_show(qtbot: QtBot) -> None:
    """A start background emits one completion signal over its whole lifetime."""
    background = AnimatedStartBackground(
        StartVariant.CONSTRUCTOR,
        intro_duration_ms=10,
        frame_interval_ms=5,
    )
    qtbot.addWidget(background)
    completions: list[bool] = []
    progress: list[float] = []
    background.intro_finished.connect(lambda: completions.append(True))
    background.intro_progress_changed.connect(progress.append)

    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    background.show()
    qtbot.waitUntil(lambda: background.intro_complete, timeout=500)

    assert background.intro_progress == 1.0
    assert completions == [True]
    assert progress
    assert progress[-1] == 1.0

    background.hide()
    background.show()
    qtbot.wait(30)

    assert background.intro_complete is True
    assert background.intro_progress == 1.0
    assert completions == [True]


def test_page_leave_finishes_intro_once_and_reshow_keeps_background_running(
    qtbot: QtBot,
) -> None:
    """Leaving a visible start page completes intro without stopping later drift."""
    host = QFrame()
    background = AnimatedStartBackground(
        StartVariant.PLAYER,
        host,
        intro_duration_ms=1_000,
        frame_interval_ms=5,
    )
    host_layout = QVBoxLayout(host)
    host_layout.addWidget(background)
    qtbot.addWidget(host)
    completions: list[bool] = []
    progress: list[float] = []
    background.intro_finished.connect(lambda: completions.append(True))
    background.intro_progress_changed.connect(progress.append)

    assert background.timer_active is False
    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    host.show()
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.waitUntil(lambda: background.intro_progress > 0.0, timeout=250)
    assert background.intro_complete is False

    background.hide()

    assert background.timer_active is False
    assert background.intro_complete is True
    assert background.intro_progress == 1.0
    assert progress[-1] == 1.0
    assert completions == [True]

    background.show()
    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.wait(25)

    assert background.timer_active is True
    assert background.intro_complete is True
    assert background.intro_progress == 1.0
    assert completions == [True]


def test_application_inactive_pauses_incomplete_intro_without_reset(
    qtbot: QtBot,
) -> None:
    """Application inactivity pauses and resumes the same incomplete intro."""
    background = AnimatedStartBackground(
        StartVariant.CONSTRUCTOR,
        intro_duration_ms=1_000,
        frame_interval_ms=5,
    )
    qtbot.addWidget(background)
    completions: list[bool] = []
    background.intro_finished.connect(lambda: completions.append(True))
    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    background.show()
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.waitUntil(lambda: background.intro_progress > 0.0, timeout=250)

    _emit_application_state(Qt.ApplicationState.ApplicationInactive)
    paused_progress = background.intro_progress
    assert background.timer_active is False
    assert background.intro_complete is False
    qtbot.wait(30)
    assert background.intro_progress == paused_progress
    assert completions == []

    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.waitUntil(lambda: background.intro_progress > paused_progress, timeout=250)

    assert background.intro_complete is False
    assert completions == []


def test_minimize_restore_pauses_incomplete_intro_without_reset(
    qtbot: QtBot,
) -> None:
    """Minimizing a real host pauses and resumes the same incomplete intro."""
    host = QFrame()
    background = AnimatedStartBackground(
        StartVariant.PLAYER,
        host,
        intro_duration_ms=1_000,
        frame_interval_ms=5,
    )
    host_layout = QVBoxLayout(host)
    host_layout.addWidget(background)
    qtbot.addWidget(host)
    completions: list[bool] = []
    background.intro_finished.connect(lambda: completions.append(True))

    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    host.show()
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.waitUntil(lambda: background.intro_progress > 0.0, timeout=250)

    host.setWindowState(Qt.WindowState.WindowMinimized)
    qtbot.waitUntil(lambda: not background.timer_active, timeout=250)
    paused_progress = background.intro_progress
    assert background.intro_complete is False
    qtbot.wait(30)
    assert background.intro_progress == paused_progress
    assert completions == []

    host.setWindowState(Qt.WindowState.WindowNoState)
    host.showNormal()
    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.waitUntil(lambda: background.intro_progress > paused_progress, timeout=250)

    assert background.intro_complete is False
    assert completions == []


def test_start_widget_connects_progress_without_blocking_actions(qtbot: QtBot) -> None:
    """The foreground card stays enabled and clickable throughout a long intro."""
    content = QFrame()
    mark = BrandMarkWidget(BrandAsset.PLAYER)
    button = QPushButton("Продолжить")
    content_layout = QVBoxLayout(content)
    content_layout.addWidget(mark)
    content_layout.addWidget(button)
    clicks: list[bool] = []
    button.clicked.connect(lambda: clicks.append(True))

    start = AnimatedStartWidget(
        StartVariant.PLAYER,
        content,
        mark,
        intro_duration_ms=10_000,
        frame_interval_ms=5,
    )
    qtbot.addWidget(start)
    start.resize(640, 420)

    effect = content.graphicsEffect()
    assert isinstance(effect, QGraphicsOpacityEffect)
    assert content.objectName() == "startActionCard"
    assert effect.opacity() == pytest.approx(0.72)
    assert start.background.variant is StartVariant.PLAYER
    assert epicase_ui.AnimatedStartWidget is AnimatedStartWidget

    start.background.intro_progress_changed.emit(0.5)
    assert mark.intro_progress == 0.5
    assert effect.opacity() == pytest.approx(0.86)

    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    start.show()
    qtbot.waitUntil(lambda: start.background.timer_active, timeout=250)
    assert button.isEnabled()
    qtbot.mouseClick(  # type: ignore[no-untyped-call]  # pytest-qt has no type hints.
        button,
        Qt.MouseButton.LeftButton,
    )
    assert clicks == [True]
    assert start.background.intro_complete is False


@pytest.mark.parametrize(
    ("variant", "primary_color", "accent_color"),
    [
        (
            StartVariant.CONSTRUCTOR,
            QColor("#17393A"),
            QColor("#B49A56"),
        ),
        (
            StartVariant.PLAYER,
            QColor("#0F766E"),
            QColor("#D9EEEB"),
        ),
    ],
)
def test_background_render_paints_field_and_network_after_resize(
    qtbot: QtBot,
    variant: StartVariant,
    primary_color: QColor,
    accent_color: QColor,
) -> None:
    """Raster output contains actual field and network pixels at varied sizes."""
    background = AnimatedStartBackground(
        variant,
        intro_duration_ms=1,
        frame_interval_ms=1,
    )
    qtbot.addWidget(background)
    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    background.show()
    qtbot.waitUntil(lambda: background.intro_complete, timeout=250)

    for width, height in [(320, 180), (641, 397)]:
        background.resize(width, height)
        pixmap = _render_transparent(background)
        image = pixmap.toImage()
        colors = {
            image.pixelColor(x, y).name()
            for y in range(height)
            for x in range(width)
        }

        assert QColor("#EDF0F3").name() in colors
        assert primary_color.name() in colors
        assert accent_color.name() in colors
        assert len(colors) > 2
        assert image.pixelColor(width // 2, height // 2).alpha() > 0


def test_destroyed_background_ignores_later_application_state_changes(
    qtbot: QtBot,
) -> None:
    """The application-state connection cannot call a destroyed background."""
    owner = QWidget()
    qtbot.addWidget(owner)
    background = AnimatedStartBackground(StartVariant.CONSTRUCTOR, owner)
    owner.show()
    background.show()
    background.deleteLater()
    qtbot.waitUntil(lambda: owner.findChild(AnimatedStartBackground) is None)

    _emit_application_state(Qt.ApplicationState.ApplicationInactive)
    _emit_application_state(Qt.ApplicationState.ApplicationActive)


def test_background_reparents_after_previous_host_is_destroyed(qtbot: QtBot) -> None:
    """A deleted former host cannot poison later window tracking."""
    host_a = QFrame()
    host_b = QFrame()
    qtbot.addWidget(host_b)
    layout_a = QVBoxLayout(host_a)
    layout_b = QVBoxLayout(host_b)
    background = AnimatedStartBackground(
        StartVariant.CONSTRUCTOR,
        host_a,
        intro_duration_ms=10,
        frame_interval_ms=5,
    )
    layout_a.addWidget(background)
    completions: list[bool] = []
    host_a_destroyed: list[bool] = []
    background.intro_finished.connect(lambda: completions.append(True))
    host_a.destroyed.connect(lambda: host_a_destroyed.append(True))

    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    host_a.show()
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.waitUntil(lambda: background.intro_complete, timeout=500)

    background.setParent(host_b)
    assert background.timer_active is False
    host_a.deleteLater()
    qtbot.waitUntil(lambda: host_a_destroyed == [True], timeout=250)

    layout_b.addWidget(background)
    host_b.show()
    _emit_application_state(Qt.ApplicationState.ApplicationActive)
    background.show()
    qtbot.waitUntil(lambda: background.timer_active, timeout=250)
    qtbot.wait(25)

    assert background.intro_complete is True
    assert completions == [True]
