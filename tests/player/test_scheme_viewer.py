"""Тесты Player-просмотрщика схемы (ADR-013): фон, вложенная навигация, раскрытие."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtGui import QColor, QFontMetricsF
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsItem,
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsView,
)
from pytestqt.qtbot import QtBot

from epicase_core.domain.scheme import Hotspot, HotspotShape, SchemeDocument, SchemeView
from epicase_player.ui.scheme_viewer import SchemeViewerWidget


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


def test_viewer_hotspot_label_has_contrast_background_and_wraps(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Подпись хотспота контрастная, жирная и переносится внутри ширины зоны."""
    label = "Водонапорная башня с длинным названием"
    scheme = SchemeDocument(
        root=SchemeView(
            background="bg",
            hotspots=(
                Hotspot(
                    id="tower",
                    shape=HotspotShape(x=0.1, y=0.1, w=0.35, h=0.4),
                    label=label,
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

    zones = [
        item
        for item in scene.items()
        if isinstance(item, QGraphicsRectItem) and item.parentItem() is None
    ]
    assert len(zones) == 1
    zone = zones[0]
    assert zone.toolTip() == label
    assert (
        zone.flags() & QGraphicsItem.GraphicsItemFlag.ItemClipsChildrenToShape
    )

    text_items = [
        item for item in scene.items() if isinstance(item, QGraphicsTextItem)
    ]
    assert len(text_items) == 1
    text_item = text_items[0]
    assert text_item.toPlainText() == label
    assert text_item.defaultTextColor() == QColor("#FFFFFF")
    assert text_item.font().bold() is True
    assert 0 < text_item.textWidth() <= 105
    font_metrics = QFontMetricsF(text_item.font())
    assert text_item.boundingRect().height() > 2 * font_metrics.lineSpacing()

    background_items = [
        item for item in scene.items() if isinstance(item, QGraphicsPathItem)
    ]
    assert len(background_items) == 1
    background = background_items[0]
    assert background.brush().color().alpha() >= 230
    assert background.brush().color() == QColor(20, 49, 48, 240)
    assert zone.rect().contains(background.boundingRect())


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
