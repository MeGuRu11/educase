"""Render-smoke картографического пина хотспота."""
from __future__ import annotations

from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem
from pytestqt.qtbot import QtBot

from epicase_ui.hotspot_marker import HotspotMarkerItem


def test_marker_fallback_label_and_fixed_scale(qtbot: QtBot) -> None:
    """Маркер ограничивает подпись, хранит tooltip и игнорирует zoom."""
    marker = HotspotMarkerItem(
        "../../unknown",
        "Очень длинная подпись объекта санитарно-эпидемиологического осмотра",
    )

    assert marker.icon_key == "inspect"
    assert marker.toolTip() == (
        "Очень длинная подпись объекта санитарно-эпидемиологического осмотра"
    )
    assert len(marker.label_lines) == 2
    assert marker.boundingRect().width() <= 160.0
    assert marker.flags() & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations


def test_marker_can_place_label_above(qtbot: QtBot) -> None:
    """У нижней границы схемы подпись переключается над пином."""
    marker = HotspotMarkerItem("water", "Водоснабжение", label_above=True)

    assert marker.label_above is True


def test_marker_render_smoke(qtbot: QtBot) -> None:
    """Пин и белая SVG-пиктограмма отрисовываются в QImage."""
    marker = HotspotMarkerItem("medical", "Медпункт")
    image = QImage(220, 140, QImage.Format.Format_ARGB32)
    image.fill(QColor("#EDF0F3"))
    painter = QPainter(image)
    painter.translate(110, 55)
    marker.paint(painter, QStyleOptionGraphicsItem())
    painter.end()

    assert image.pixelColor(110, 38) == QColor("#0F766E")
