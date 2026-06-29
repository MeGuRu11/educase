"""Shared animated start-screen background and foreground shell."""

from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QEvent, QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QHideEvent,
    QPainter,
    QPaintEvent,
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
from epicase_ui.investigation_map import (
    InvestigationMapRenderer,
)
from epicase_ui.investigation_map import (
    StartVariant as StartVariant,
)

_FIELD_COLOR = QColor("#EDF0F3")
_FRAME_INTERVAL_MS = 33


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
        self._map_renderer = InvestigationMapRenderer(self._variant)

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

    @property
    def map_layers(self) -> tuple[str, ...]:
        """Return the stable investigation-map layer order."""
        return self._map_renderer.layer_names

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
        """Paint the field and balanced investigation-map animation."""
        del event
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.fillRect(self.rect(), _FIELD_COLOR)
            self._map_renderer.paint(
                painter,
                self.rect(),
                elapsed_ms=self._active_milliseconds(),
                intro_progress=self._intro_progress,
            )
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
