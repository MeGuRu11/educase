"""Shared animated start-screen background and foreground shell."""

from __future__ import annotations

import math
from enum import StrEnum

from PySide6.QtCore import QElapsedTimer, QEvent, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QHideEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QShowEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QWidget,
)
from shiboken6 import getCppPointer

from epicase_ui.brand_mark import BrandMarkWidget

_FIELD_COLOR = QColor("#EDF0F3")
_CONSTRUCTOR_TEAL = QColor("#17393A")
_CONSTRUCTOR_BRASS = QColor("#B49A56")
_PLAYER_TEAL = QColor("#0F766E")
_PLAYER_PALE = QColor("#D9EEEB")
_FRAME_INTERVAL_MS = 33

_NormalizedPoint = tuple[float, float]
_Edge = tuple[int, int]

_CONSTRUCTOR_NODES: tuple[_NormalizedPoint, ...] = (
    (0.10, 0.20),
    (0.30, 0.20),
    (0.50, 0.20),
    (0.70, 0.20),
    (0.90, 0.20),
    (0.10, 0.50),
    (0.30, 0.50),
    (0.50, 0.50),
    (0.70, 0.50),
    (0.90, 0.50),
    (0.10, 0.80),
    (0.30, 0.80),
    (0.50, 0.80),
    (0.70, 0.80),
    (0.90, 0.80),
)
_CONSTRUCTOR_EDGES: tuple[_Edge, ...] = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (5, 6),
    (6, 7),
    (7, 8),
    (8, 9),
    (10, 11),
    (11, 12),
    (12, 13),
    (13, 14),
    (0, 5),
    (5, 10),
    (1, 6),
    (6, 11),
    (2, 7),
    (7, 12),
    (3, 8),
    (8, 13),
    (4, 9),
    (9, 14),
)

_PLAYER_NODES: tuple[_NormalizedPoint, ...] = (
    (0.07, 0.38),
    (0.18, 0.16),
    (0.25, 0.62),
    (0.39, 0.29),
    (0.48, 0.73),
    (0.58, 0.12),
    (0.67, 0.48),
    (0.78, 0.25),
    (0.88, 0.66),
    (0.96, 0.36),
)
_PLAYER_EDGES: tuple[_Edge, ...] = (
    (0, 1),
    (0, 2),
    (1, 3),
    (2, 3),
    (2, 4),
    (3, 4),
    (3, 5),
    (3, 6),
    (4, 6),
    (5, 6),
    (5, 7),
    (6, 7),
    (6, 8),
    (7, 9),
    (8, 9),
)

_INTRO_PARTICLES: tuple[_NormalizedPoint, ...] = (
    (0.04, 0.08),
    (0.18, 0.92),
    (0.32, 0.04),
    (0.68, 0.94),
    (0.82, 0.10),
    (0.96, 0.78),
)


class StartVariant(StrEnum):
    """Visual variants shared by the Constructor and Player start screens."""

    CONSTRUCTOR = "constructor"
    PLAYER = "player"


class AnimatedStartBackground(QWidget):
    """Paint a lifecycle-aware vector field behind a start screen."""

    intro_finished = Signal()
    intro_progress_changed = Signal(float)

    def __init__(
        self,
        variant: StartVariant,
        parent: QWidget | None = None,
        *,
        intro_duration_ms: int = 1_400,
        frame_interval_ms: int = _FRAME_INTERVAL_MS,
    ) -> None:
        """Create a deterministic background for one application variant."""
        super().__init__(parent)
        self._variant = StartVariant(variant)
        self._intro_duration_ms = max(1, int(intro_duration_ms))
        self._intro_progress = 0.0
        self._intro_complete = False
        self._application_active = (
            QGuiApplication.applicationState()
            is Qt.ApplicationState.ApplicationActive
        )
        self._accumulated_active_ms = 0
        self._active_segment = QElapsedTimer()
        self._tracked_window: QWidget | None = None
        self._tracked_window_identity: int | None = None

        object_names = {
            StartVariant.CONSTRUCTOR: "constructorStartBackground",
            StartVariant.PLAYER: "playerStartBackground",
        }
        self.setObjectName(object_names[self._variant])
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)

        self._timer = QTimer(self)
        self._timer.setInterval(max(1, int(frame_interval_ms)))
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_frame)

        application = QGuiApplication.instance()
        if isinstance(application, QGuiApplication):
            application.applicationStateChanged.connect(
                self._on_application_state_changed
            )

    @property
    def variant(self) -> StartVariant:
        """Return the immutable Constructor or Player visual variant."""
        return self._variant

    @property
    def intro_complete(self) -> bool:
        """Return whether this instance has completed its one-shot intro."""
        return self._intro_complete

    @property
    def intro_progress(self) -> float:
        """Return current intro progress in the inclusive unit interval."""
        return self._intro_progress

    @property
    def timer_active(self) -> bool:
        """Return whether frame updates are currently scheduled."""
        return self._timer.isActive()

    def showEvent(self, event: QShowEvent) -> None:
        """Resume animation when this visible window may be animated."""
        super().showEvent(event)
        self._track_window()
        self._sync_timer()

    def hideEvent(self, event: QHideEvent) -> None:
        """Finish a left page, or only pause when the application is suspended."""
        if self._application_active and not self.window().isMinimized():
            self._finish_intro()
        self._stop_timer()
        super().hideEvent(event)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Synchronize animation with the containing window lifecycle."""
        if watched is self._tracked_window:
            if event.type() is QEvent.Type.Hide:
                self._stop_timer()
            elif event.type() in {
                QEvent.Type.Show,
                QEvent.Type.WindowStateChange,
            }:
                self._sync_timer()
        return super().eventFilter(watched, event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the field, drifting network, and converging intro particles."""
        del event
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), _FIELD_COLOR)
            if self._variant is StartVariant.CONSTRUCTOR:
                self._paint_constructor_grid(painter)
                self._paint_network(
                    painter,
                    _CONSTRUCTOR_NODES,
                    _CONSTRUCTOR_EDGES,
                    _CONSTRUCTOR_TEAL,
                    _CONSTRUCTOR_BRASS,
                )
            else:
                self._paint_network(
                    painter,
                    _PLAYER_NODES,
                    _PLAYER_EDGES,
                    _PLAYER_TEAL,
                    _PLAYER_PALE,
                )
            self._paint_intro_particles(painter)
        finally:
            painter.end()

    def _track_window(self) -> None:
        window = self.window()
        if window is self._tracked_window:
            return
        if self._tracked_window is not None:
            self._tracked_window.removeEventFilter(self)
            self._tracked_window.destroyed.disconnect(
                self._on_tracked_window_destroyed
            )
        self._tracked_window = window
        self._tracked_window_identity = getCppPointer(window)[0]
        window.installEventFilter(self)
        window.destroyed.connect(self._on_tracked_window_destroyed)

    @Slot(QObject)
    def _on_tracked_window_destroyed(self, destroyed: QObject) -> None:
        destroyed_identity = getCppPointer(destroyed)[0]
        if destroyed_identity != self._tracked_window_identity:
            return
        self._stop_timer()
        self._tracked_window = None
        self._tracked_window_identity = None

    def _on_application_state_changed(self, state: Qt.ApplicationState) -> None:
        self._application_active = state is Qt.ApplicationState.ApplicationActive
        self._sync_timer()

    def _sync_timer(self) -> None:
        window = self.window()
        should_run = (
            self.isVisible()
            and self._application_active
            and not window.isMinimized()
        )
        if should_run:
            self._start_timer()
        else:
            self._stop_timer()

    def _start_timer(self) -> None:
        if self._timer.isActive():
            return
        self._active_segment.start()
        self._timer.start()
        self.update()

    def _stop_timer(self) -> None:
        if self._active_segment.isValid():
            self._accumulated_active_ms += self._active_segment.elapsed()
            self._active_segment.invalidate()
        self._timer.stop()

    def _active_milliseconds(self) -> int:
        if self._active_segment.isValid():
            return self._accumulated_active_ms + self._active_segment.elapsed()
        return self._accumulated_active_ms

    def _finish_intro(self) -> None:
        if self._intro_complete:
            return
        progress_changed = self._intro_progress != 1.0
        self._intro_progress = 1.0
        self._intro_complete = True
        if progress_changed:
            self.intro_progress_changed.emit(1.0)
        self.intro_finished.emit()

    def _on_frame(self) -> None:
        if not self._intro_complete:
            elapsed_ms = self._active_milliseconds()
            progress = min(1.0, elapsed_ms / self._intro_duration_ms)
            if progress >= 1.0:
                self._finish_intro()
            elif progress != self._intro_progress:
                self._intro_progress = progress
                self.intro_progress_changed.emit(progress)
        self.update()

    def _node_position(
        self,
        nodes: tuple[_NormalizedPoint, ...],
        index: int,
        phase: float,
    ) -> tuple[int, int]:
        normalized_x, normalized_y = nodes[index]
        drift_x = math.sin(phase * 0.37 + index * 1.41) * 0.006
        drift_y = math.cos(phase * 0.29 + index * 1.17) * 0.008
        return (
            round((normalized_x + drift_x) * self.width()),
            round((normalized_y + drift_y) * self.height()),
        )

    def _paint_constructor_grid(self, painter: QPainter) -> None:
        painter.save()
        painter.setOpacity(0.56)
        painter.setPen(QPen(_CONSTRUCTOR_TEAL, 1.0))
        spacing = 48
        for x in range(0, self.width() + spacing, spacing):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height() + spacing, spacing):
            painter.drawLine(0, y, self.width(), y)
        painter.restore()

    def _paint_network(
        self,
        painter: QPainter,
        nodes: tuple[_NormalizedPoint, ...],
        edges: tuple[_Edge, ...],
        primary: QColor,
        secondary: QColor,
    ) -> None:
        phase = self._active_milliseconds() / 1_000.0
        appeared = 1.0 - (1.0 - self._intro_progress) ** 3
        painter.save()
        painter.setOpacity(0.12 + 0.88 * appeared)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for edge_index, (start, end) in enumerate(edges):
            painter.setPen(QPen(primary if edge_index % 4 else secondary, 2.0))
            start_x, start_y = self._node_position(nodes, start, phase)
            end_x, end_y = self._node_position(nodes, end, phase)
            painter.drawLine(start_x, start_y, end_x, end_y)

        painter.setPen(Qt.PenStyle.NoPen)
        for node_index in range(len(nodes)):
            painter.setBrush(primary if node_index % 4 else secondary)
            x, y = self._node_position(nodes, node_index, phase)
            painter.drawEllipse(x - 4, y - 4, 8, 8)
        painter.restore()

    def _paint_intro_particles(self, painter: QPainter) -> None:
        if self._intro_complete:
            return
        progress = self._intro_progress
        convergence = 1.0 - (1.0 - progress) ** 3
        painter.save()
        painter.setOpacity((1.0 - progress) * 0.72)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(
            _CONSTRUCTOR_BRASS
            if self._variant is StartVariant.CONSTRUCTOR
            else _PLAYER_PALE
        )
        center_x = self.width() * 0.5
        center_y = self.height() * 0.5
        for normalized_x, normalized_y in _INTRO_PARTICLES:
            start_x = normalized_x * self.width()
            start_y = normalized_y * self.height()
            x = round(start_x + (center_x - start_x) * convergence)
            y = round(start_y + (center_y - start_y) * convergence)
            painter.drawEllipse(x - 3, y - 3, 6, 6)
        painter.restore()


class AnimatedStartWidget(QWidget):
    """Overlay a centered interactive start card on an animated background."""

    def __init__(
        self,
        variant: StartVariant,
        content: QFrame,
        brand_mark: BrandMarkWidget,
        parent: QWidget | None = None,
        *,
        intro_duration_ms: int = 1_400,
        frame_interval_ms: int = _FRAME_INTERVAL_MS,
    ) -> None:
        """Create a start shell without disabling any foreground actions."""
        super().__init__(parent)
        self.background = AnimatedStartBackground(
            variant,
            self,
            intro_duration_ms=intro_duration_ms,
            frame_interval_ms=frame_interval_ms,
        )
        self._content = content
        self._brand_mark = brand_mark

        content.setObjectName("startActionCard")
        self._content_opacity = QGraphicsOpacityEffect(content)
        self._content_opacity.setOpacity(0.72)
        content.setGraphicsEffect(self._content_opacity)

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.background, 0, 0)
        layout.addWidget(content, 0, 0, Qt.AlignmentFlag.AlignCenter)
        self.background.lower()
        content.raise_()

        self.background.intro_progress_changed.connect(
            self._brand_mark.set_intro_progress
        )
        self.background.intro_progress_changed.connect(self._set_intro_progress)
        self._brand_mark.set_intro_progress(0.0)

    def _set_intro_progress(self, progress: float) -> None:
        clamped = min(1.0, max(0.0, progress))
        self._content_opacity.setOpacity(0.72 + 0.28 * clamped)
