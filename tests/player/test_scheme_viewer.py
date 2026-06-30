"""Тесты Player-просмотрщика схемы (ADR-013): фон, вложенная навигация, раскрытие."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsView,
)
from pytestqt.qtbot import QtBot

from epicase_core.domain.scheme import Hotspot, HotspotShape, SchemeDocument, SchemeView
from epicase_player.ui.scheme_viewer import SchemeViewerWidget
from epicase_ui.hotspot_marker import HotspotMarkerItem


def _scheme_with_child_and_reveal() -> SchemeDocument:
    """Корневой вид: один хотспот с вложенным интерьером, один — с раскрытием текста."""
    return SchemeDocument(
        title="Схема казармы",
        root=SchemeView(
            background="bg-root",
            hotspots=(
                Hotspot(
                    id="hs-child",
                    shape=HotspotShape(x=0.1, y=0.1, w=0.3, h=0.3),
                    label="Вход",
                    child=SchemeView(
                        background="bg-interior",
                        hotspots=(
                            Hotspot(
                                id="hs-inner",
                                shape=HotspotShape(x=0.5, y=0.5, w=0.2, h=0.2),
                                label="Объект",
                                reveal_text="Деталь интерьера.",
                            ),
                        ),
                    ),
                ),
                Hotspot(
                    id="hs-reveal",
                    shape=HotspotShape(x=0.6, y=0.6, w=0.2, h=0.2),
                    label="Окно",
                    reveal_text="Окно не открывается.",
                ),
            ),
        ),
    )


def test_viewer_renders_background(qtbot: QtBot, png_bytes: Callable[..., bytes]) -> None:
    """Фон присутствует в assets → has_background() == True."""
    viewer = SchemeViewerWidget(
        _scheme_with_child_and_reveal(), {"bg-root": png_bytes(120, 120)}
    )
    qtbot.addWidget(viewer)
    assert viewer.has_background() is True


def test_viewer_renders_marker_and_hides_default_hit_area(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Player показывает пин, а прямоугольник оставляет невидимым hit-area."""
    label = "Водонапорная башня с длинным названием"
    scheme = SchemeDocument(
        root=SchemeView(
            background="bg",
            hotspots=(
                Hotspot(
                    id="tower",
                    shape=HotspotShape(x=0.1, y=0.1, w=0.35, h=0.4),
                    label=label,
                    icon="water",
                ),
            ),
        )
    )
    viewer = SchemeViewerWidget(scheme, {"bg": png_bytes(300, 200)})
    qtbot.addWidget(viewer)

    graphics_view = viewer.findChild(QGraphicsView)
    assert graphics_view is not None
    scene = graphics_view.scene()
    assert scene is not None

    markers = [
        item for item in scene.items() if isinstance(item, HotspotMarkerItem)
    ]
    hit_areas = [
        item
        for item in scene.items()
        if isinstance(item, QGraphicsRectItem) and item.parentItem() is None
    ]
    assert len(markers) == 1
    marker = markers[0]
    assert marker.icon_key == "water"
    assert marker.toolTip() == label
    assert len(marker.label_lines) == 2
    assert (
        marker.flags()
        & QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations
    )
    assert len(hit_areas) == 1
    hit_area = hit_areas[0]
    assert hit_area.pen().style() == Qt.PenStyle.NoPen
    assert hit_area.brush().style() == Qt.BrushStyle.NoBrush
    assert marker.pos() == hit_area.rect().center()


def test_viewer_unknown_icon_uses_inspect_marker(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Legacy/unknown ключ не ломает Player и показывает универсальный inspect."""
    scheme = SchemeDocument(
        root=SchemeView(
            background="bg",
            hotspots=(
                Hotspot(
                    id="legacy",
                    shape=HotspotShape(0.2, 0.2, 0.2, 0.2),
                    icon="zoom",
                ),
            ),
        )
    )
    viewer = SchemeViewerWidget(scheme, {"bg": png_bytes(120, 120)})
    qtbot.addWidget(viewer)
    graphics_view = viewer.findChild(QGraphicsView)
    assert graphics_view is not None
    scene = graphics_view.scene()
    assert scene is not None

    markers = [
        item for item in scene.items() if isinstance(item, HotspotMarkerItem)
    ]
    assert len(markers) == 1
    assert markers[0].icon_key == "inspect"


def test_viewer_missing_background_shows_placeholder(qtbot: QtBot) -> None:
    """Нет байт фона → плейсхолдер, has_background() == False, без падения."""
    viewer = SchemeViewerWidget(SchemeDocument(root=SchemeView(background="ghost")), {})
    qtbot.addWidget(viewer)
    assert viewer.has_background() is False


def test_viewer_child_hotspot_pushes_and_back(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Клик по хотспоту с child открывает вложенный вид; «Назад» возвращает к корню."""
    scheme = _scheme_with_child_and_reveal()
    assets = {"bg-root": png_bytes(120, 120), "bg-interior": png_bytes(120, 120)}
    viewer = SchemeViewerWidget(scheme, assets)
    qtbot.addWidget(viewer)

    # На корне — одна страница, кнопка «Назад» скрыта.
    assert viewer._stack.count() == 1
    assert viewer._back.isHidden() is True

    viewer._activate_hotspot(scheme.root.hotspots[0])  # хотспот с child
    assert viewer._stack.count() == 2
    assert viewer._back.isHidden() is False

    viewer._go_back()
    assert viewer._stack.count() == 1
    assert viewer._back.isHidden() is True


def test_viewer_reveal_dialog_does_not_accumulate(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Повторные раскрытия не накапливают диалоги — одновременно открыт максимум один."""
    scheme = _scheme_with_child_and_reveal()
    viewer = SchemeViewerWidget(scheme, {"bg-root": png_bytes(120, 120)})
    qtbot.addWidget(viewer)

    reveal_hotspot = scheme.root.hotspots[1]  # хотспот с reveal_text
    viewer._activate_hotspot(reveal_hotspot)
    viewer._activate_hotspot(reveal_hotspot)
    # Принудительно обработать отложенное удаление прошлого диалога.
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)

    assert len(viewer.findChildren(QDialog)) == 1
