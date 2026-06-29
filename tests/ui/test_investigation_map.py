"""Tests for the deterministic investigation-map animation renderer."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QImage, QPainter

from epicase_ui.investigation_map import (
    _VARIANT_SPECS,
    InvestigationMapRenderer,
    StartVariant,
    _cubic_point,
    _CubicRoute,
)

_FIELD_COLOR = QColor("#EDF0F3")


def _render_map(
    renderer: InvestigationMapRenderer,
    *,
    elapsed_ms: int,
    intro_progress: float,
) -> QImage:
    """Render one deterministic map frame into an off-screen image."""
    image = QImage(480, 300, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(_FIELD_COLOR)
    painter = QPainter(image)
    try:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.paint(
            painter,
            QRect(0, 0, image.width(), image.height()),
            elapsed_ms=elapsed_ms,
            intro_progress=intro_progress,
        )
    finally:
        painter.end()
    return image


def test_cubic_point_returns_route_endpoints() -> None:
    """Cubic route evaluation preserves its declared start and end points."""
    route = _CubicRoute(
        points=((0.0, 0.2), (0.2, 0.0), (0.8, 1.0), (1.0, 0.8)),
        accent=False,
        signal_period_ms=5_000,
        signal_phase=0.0,
    )

    assert _cubic_point(route, 0.0) == pytest.approx((0.0, 0.2))
    assert _cubic_point(route, 1.0) == pytest.approx((1.0, 0.8))


def test_variants_define_distinct_balanced_maps() -> None:
    """Constructor and Player share map language without sharing geometry."""
    constructor = _VARIANT_SPECS[StartVariant.CONSTRUCTOR]
    player = _VARIANT_SPECS[StartVariant.PLAYER]

    assert len(constructor.routes) == 4
    assert len(player.routes) == 4
    assert len(constructor.hotspots) == 3
    assert len(player.hotspots) == 3
    assert constructor.routes != player.routes
    assert constructor.primary.name() == "#17393a"
    assert constructor.accent.name() == "#b49a56"
    assert player.primary.name() == "#0f766e"
    assert player.accent.name() == "#d9eeeb"


@pytest.mark.parametrize("variant", tuple(StartVariant))
def test_renderer_paints_four_layers_and_moves_after_intro(
    variant: StartVariant,
) -> None:
    """A completed investigation map contains its palette and keeps moving."""
    renderer = InvestigationMapRenderer(variant)
    spec = _VARIANT_SPECS[variant]

    early_intro = _render_map(renderer, elapsed_ms=200, intro_progress=0.15)
    completed = _render_map(renderer, elapsed_ms=2_000, intro_progress=1.0)
    later_motion = _render_map(renderer, elapsed_ms=3_000, intro_progress=1.0)
    completed_colors = {
        completed.pixelColor(x, y).name()
        for y in range(completed.height())
        for x in range(completed.width())
    }

    assert renderer.layer_names == ("grid", "routes", "hotspots", "signals")
    assert _FIELD_COLOR.name() in completed_colors
    assert spec.primary.name() in completed_colors
    assert spec.accent.name() in completed_colors
    assert completed != early_intro
    assert completed != later_motion
