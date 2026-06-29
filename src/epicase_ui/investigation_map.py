"""Deterministic geometry and painting for the investigation-map background."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QPointF, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF

_NormalizedPoint = tuple[float, float]


class StartVariant(StrEnum):
    """Visual variants shared by the Constructor and Player start screens."""

    CONSTRUCTOR = "constructor"
    PLAYER = "player"


@dataclass(frozen=True)
class _CubicRoute:
    """One normalized cubic route and its moving signal parameters."""

    points: tuple[_NormalizedPoint, _NormalizedPoint, _NormalizedPoint, _NormalizedPoint]
    accent: bool
    signal_period_ms: int
    signal_phase: float


@dataclass(frozen=True)
class _MapSpec:
    """Deterministic geometry and palette for one application."""

    routes: tuple[_CubicRoute, ...]
    hotspots: tuple[_NormalizedPoint, ...]
    primary: QColor
    accent: QColor
    grid_opacity: float


_VARIANT_SPECS: dict[StartVariant, _MapSpec] = {
    StartVariant.CONSTRUCTOR: _MapSpec(
        routes=(
            _CubicRoute(
                ((-0.05, 0.72), (0.20, 0.22), (0.58, 0.82), (1.05, 0.26)),
                False,
                5_200,
                0.02,
            ),
            _CubicRoute(
                ((0.02, 0.18), (0.30, 0.48), (0.64, 0.08), (0.98, 0.45)),
                True,
                6_400,
                0.34,
            ),
            _CubicRoute(
                ((0.08, 0.92), (0.25, 0.58), (0.70, 0.64), (0.94, 0.90)),
                False,
                7_100,
                0.61,
            ),
            _CubicRoute(
                ((0.12, -0.06), (0.34, 0.25), (0.68, 0.80), (0.90, 1.06)),
                True,
                7_800,
                0.82,
            ),
        ),
        hotspots=((0.14, 0.58), (0.80, 0.24), (0.72, 0.76)),
        primary=QColor("#17393A"),
        accent=QColor("#B49A56"),
        grid_opacity=0.30,
    ),
    StartVariant.PLAYER: _MapSpec(
        routes=(
            _CubicRoute(
                ((-0.06, 0.76), (0.13, 0.23), (0.48, 0.88), (1.06, 0.30)),
                False,
                5_600,
                0.08,
            ),
            _CubicRoute(
                ((0.02, 0.10), (0.27, 0.65), (0.63, -0.02), (1.02, 0.62)),
                True,
                6_800,
                0.29,
            ),
            _CubicRoute(
                ((0.04, 0.95), (0.32, 0.45), (0.76, 0.94), (0.96, 0.70)),
                False,
                7_300,
                0.57,
            ),
            _CubicRoute(
                ((0.18, -0.08), (0.08, 0.38), (0.86, 0.44), (0.82, 1.08)),
                False,
                8_000,
                0.86,
            ),
        ),
        hotspots=((0.12, 0.62), (0.82, 0.28), (0.68, 0.78)),
        primary=QColor("#0F766E"),
        accent=QColor("#D9EEEB"),
        grid_opacity=0.20,
    ),
}


def _cubic_point(route: _CubicRoute, progress: float) -> _NormalizedPoint:
    """Return a point on a normalized cubic Bézier route."""
    clamped = min(1.0, max(0.0, progress))
    inverse = 1.0 - clamped
    weights = (
        inverse**3,
        3.0 * inverse**2 * clamped,
        3.0 * inverse * clamped**2,
        clamped**3,
    )
    return (
        sum(
            point[0] * weight
            for point, weight in zip(route.points, weights, strict=True)
        ),
        sum(
            point[1] * weight
            for point, weight in zip(route.points, weights, strict=True)
        ),
    )


def _segment_progress(progress: float, start: float, end: float) -> float:
    """Map a unit progress value into one clamped animation segment."""
    if end <= start:
        return 1.0 if progress >= end else 0.0
    return min(1.0, max(0.0, (progress - start) / (end - start)))


class InvestigationMapRenderer:
    """Paint the approved balanced investigation-map animation."""

    layer_names = ("grid", "routes", "hotspots", "signals")

    def __init__(self, variant: StartVariant) -> None:
        """Select deterministic geometry and palette for one application."""
        self.variant = StartVariant(variant)
        self._spec = _VARIANT_SPECS[self.variant]

    def paint(
        self,
        painter: QPainter,
        rect: QRect,
        *,
        elapsed_ms: int,
        intro_progress: float,
    ) -> None:
        """Paint one frame from elapsed active time and one-shot intro progress."""
        grid_progress = _segment_progress(intro_progress, 0.0, 0.32)
        route_progress = _segment_progress(intro_progress, 0.18, 0.79)
        activity_progress = _segment_progress(intro_progress, 0.46, 1.0)
        self._paint_grid(painter, rect, elapsed_ms, grid_progress)
        self._paint_routes(painter, rect, elapsed_ms, route_progress)
        self._paint_hotspots(painter, rect, elapsed_ms, activity_progress)
        self._paint_signals(
            painter,
            rect,
            elapsed_ms,
            route_progress,
            activity_progress,
        )

    def _paint_grid(
        self,
        painter: QPainter,
        rect: QRect,
        elapsed_ms: int,
        progress: float,
    ) -> None:
        if progress <= 0.0:
            return
        painter.save()
        try:
            painter.setOpacity(self._spec.grid_opacity * progress)
            painter.setPen(QPen(self._spec.primary, 1.0))
            horizon_y = rect.top() + rect.height() * 0.16
            vanishing_x = rect.center().x()
            bottom_y = rect.bottom()
            horizontal_phase = (elapsed_ms % 12_000) / 12_000.0

            for index in range(12):
                depth = ((index + horizontal_phase) % 12) / 11.0
                y = horizon_y + (depth**1.65) * (bottom_y - horizon_y)
                painter.drawLine(
                    QPointF(rect.left(), y),
                    QPointF(rect.right(), y),
                )

            spacing = max(42, rect.width() // 12)
            lateral_shift = (elapsed_ms % 16_000) / 16_000.0 * spacing
            for x in range(rect.left() - spacing, rect.right() + spacing, spacing):
                bottom_x = x + lateral_shift
                top_x = vanishing_x + (bottom_x - vanishing_x) * 0.16
                painter.drawLine(
                    QPointF(bottom_x, bottom_y),
                    QPointF(top_x, horizon_y),
                )
        finally:
            painter.restore()

    def _paint_routes(
        self,
        painter: QPainter,
        rect: QRect,
        elapsed_ms: int,
        progress: float,
    ) -> None:
        if progress <= 0.0:
            return
        painter.save()
        try:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for index, route in enumerate(self._spec.routes):
                route_progress = _segment_progress(
                    progress,
                    index * 0.08,
                    0.76 + index * 0.08,
                )
                if route_progress <= 0.0:
                    continue
                color = self._spec.accent if route.accent else self._spec.primary
                pen = QPen(color, 2.0)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setDashPattern((4.0, 7.0))
                pen.setDashOffset(-(elapsed_ms / 120.0 + index * 3.0))
                painter.setPen(pen)
                painter.setOpacity(0.30 + 0.48 * route_progress)
                painter.drawPolyline(
                    self._route_polygon(route, rect, route_progress),
                )
        finally:
            painter.restore()

    def _paint_hotspots(
        self,
        painter: QPainter,
        rect: QRect,
        elapsed_ms: int,
        progress: float,
    ) -> None:
        if progress <= 0.0:
            return
        painter.save()
        try:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for index, hotspot in enumerate(self._spec.hotspots):
                center = self._to_point(hotspot, rect)
                period_ms = 2_800 + index * 450
                phase = ((elapsed_ms + index * 870) % period_ms) / period_ms
                radius = 7.0 + phase * min(rect.width(), rect.height()) * 0.10
                ring_color = QColor(
                    self._spec.accent if index == 1 else self._spec.primary
                )
                ring_color.setAlpha(round(125 * (1.0 - phase) * progress))
                painter.setPen(QPen(ring_color, 1.8))
                painter.drawEllipse(center, radius, radius)

            painter.setOpacity(progress)
            painter.setPen(Qt.PenStyle.NoPen)
            for index, hotspot in enumerate(self._spec.hotspots):
                painter.setBrush(
                    self._spec.accent if index == 1 else self._spec.primary
                )
                painter.drawEllipse(self._to_point(hotspot, rect), 4.5, 4.5)
        finally:
            painter.restore()

    def _paint_signals(
        self,
        painter: QPainter,
        rect: QRect,
        elapsed_ms: int,
        route_progress: float,
        activity_progress: float,
    ) -> None:
        if activity_progress <= 0.0:
            return
        painter.save()
        try:
            self._paint_scan_wave(painter, rect, elapsed_ms, activity_progress)
            painter.setPen(Qt.PenStyle.NoPen)
            for index, route in enumerate(self._spec.routes):
                phase = (
                    elapsed_ms / route.signal_period_ms + route.signal_phase
                ) % 1.0
                point = self._to_point(
                    _cubic_point(route, phase * route_progress),
                    rect,
                )
                color = self._spec.accent if route.accent else self._spec.primary
                halo_color = QColor(color)
                halo_color.setAlpha(round(55 * activity_progress))
                painter.setBrush(halo_color)
                painter.drawEllipse(point, 8.0, 8.0)
                painter.setOpacity(activity_progress)
                painter.setBrush(color)
                painter.drawEllipse(point, 3.5 + index % 2, 3.5 + index % 2)
                painter.setOpacity(1.0)
        finally:
            painter.restore()

    def _paint_scan_wave(
        self,
        painter: QPainter,
        rect: QRect,
        elapsed_ms: int,
        progress: float,
    ) -> None:
        center = QPointF(rect.center())
        radius = math.hypot(rect.width(), rect.height())
        angle = elapsed_ms / 10_000.0 * math.tau
        start = QPointF(
            center.x() + math.cos(angle - 0.20) * radius,
            center.y() + math.sin(angle - 0.20) * radius,
        )
        end = QPointF(
            center.x() + math.cos(angle + 0.03) * radius,
            center.y() + math.sin(angle + 0.03) * radius,
        )
        wave_color = QColor(self._spec.primary)
        wave_color.setAlpha(round(18 * progress))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(wave_color)
        painter.drawPolygon(QPolygonF((center, start, end)))

    @staticmethod
    def _to_point(point: _NormalizedPoint, rect: QRect) -> QPointF:
        return QPointF(
            rect.left() + point[0] * rect.width(),
            rect.top() + point[1] * rect.height(),
        )

    def _route_polygon(
        self,
        route: _CubicRoute,
        rect: QRect,
        progress: float,
    ) -> QPolygonF:
        sample_count = max(2, round(48 * progress))
        points = [
            self._to_point(
                _cubic_point(route, progress * index / (sample_count - 1)),
                rect,
            )
            for index in range(sample_count)
        ]
        return QPolygonF(points)
