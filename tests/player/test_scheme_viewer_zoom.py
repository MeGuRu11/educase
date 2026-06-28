"""Тесты зума и панорамы Player-вьюера схемы (R3): clamp масштаба и сохранность hit-test."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import QGraphicsScene
from pytestqt.qtbot import QtBot

from epicase_core.domain.scheme import Hotspot, HotspotShape
from epicase_player.ui.scheme_viewer import _ZOOM_MAX, _SchemeGraphicsView

_PX_W = 80
_PX_H = 60


def _noop(hotspot: Hotspot) -> None:
    """Колбэк-заглушка для тестов, не интересующихся попаданиями."""


def _make_view(
    qtbot: QtBot,
    hotspots: tuple[Hotspot, ...] = (),
    on_hotspot: Callable[[Hotspot], None] | None = None,
) -> _SchemeGraphicsView:
    """Собрать вью с фоновым pixmap _PX_W×_PX_H и (опционально) хотспотами/колбэком."""
    scene = QGraphicsScene()
    scene.addPixmap(QPixmap(_PX_W, _PX_H))
    view = _SchemeGraphicsView(
        scene, _PX_W, _PX_H, hotspots, on_hotspot if on_hotspot is not None else _noop
    )
    qtbot.addWidget(view)
    return view


def test_current_zoom_is_one_after_creation(qtbot: QtBot) -> None:
    """Сразу после создания масштаб базовый 1:1."""
    view = _make_view(qtbot)
    assert view.current_zoom() == 1.0


def test_zoom_in_increases_zoom_and_transform(qtbot: QtBot) -> None:
    """zoom_in() поднимает уровень масштаба и растягивает трансформацию (m11 > 1)."""
    view = _make_view(qtbot)
    view.zoom_in()
    assert view.current_zoom() > 1.0
    assert view.transform().m11() > 1.0


def test_repeated_zoom_in_clamped_at_max(qtbot: QtBot) -> None:
    """Многократный zoom_in() не превышает верхний предел масштаба."""
    view = _make_view(qtbot)
    for _ in range(50):
        view.zoom_in()
    assert view.current_zoom() == _ZOOM_MAX


def test_zoom_out_from_base_clamped_at_min(qtbot: QtBot) -> None:
    """zoom_out() из базового масштаба не уходит ниже 1.0 (clamp снизу)."""
    view = _make_view(qtbot)
    view.zoom_out()
    assert view.current_zoom() == 1.0


def test_reset_zoom_restores_identity(qtbot: QtBot) -> None:
    """zoom_in() затем reset_zoom() возвращает масштаб 1.0 и единичную трансформацию."""
    view = _make_view(qtbot)
    view.zoom_in()
    view.reset_zoom()
    assert view.current_zoom() == 1.0
    assert view.transform().m11() == 1.0


def test_hit_test_center_preserved_under_zoom(qtbot: QtBot) -> None:
    """Центральный хотспот ловится кликом в центр окна и до, и после зума.

    Hit-test идёт через ``mapToScene`` → доли → ``HotspotShape.contains``; ``mapToScene``
    учитывает текущую трансформацию, поэтому попадание не зависит от уровня масштаба.
    """
    hotspot = Hotspot(id="center", shape=HotspotShape(x=0.25, y=0.25, w=0.5, h=0.5))
    calls: list[Hotspot] = []
    view = _make_view(qtbot, (hotspot,), calls.append)

    center = QPoint(_PX_W // 2, _PX_H // 2)  # геометрический центр окна вьюера

    # До зума: центр окна в долях лежит внутри центрального хотспота.
    before = view.mapToScene(center)
    assert hotspot.shape.contains(before.x() / _PX_W, before.y() / _PX_H)

    view.zoom_in()

    # После зума: центр окна по-прежнему в долях внутри хотспота (масштаб не влияет).
    after = view.mapToScene(center)
    assert hotspot.shape.contains(after.x() / _PX_W, after.y() / _PX_H)

    # И полный путь mousePressEvent на зум-уровне всё ещё активирует хотспот.
    event = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(center),
        QPointF(center),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    view.mousePressEvent(event)
    assert calls == [hotspot]
