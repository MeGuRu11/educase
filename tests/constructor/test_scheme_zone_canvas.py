"""Тесты графического ядра редактора зон схемы (Constructor, R2-B.1).

Реальные виджеты (pytest-qt): фон из временного PNG, проверка долей, клампа перемещения и
resize-шва ``set_scene_rect``, удаления зон. UI-обёртка и интеграция в этапы — R2-B.2.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QGraphicsTextItem
from pytestqt.qtbot import QtBot

from epicase_constructor.ui.scheme_zone_canvas import SchemeZoneCanvas
from epicase_core.application.case_builder import AssetRef

# Фон 40×30: меньше _MAX_WIDTH, без масштабирования; минимум зоны 2*_HANDLE = 16 px.
_BG_W = 40
_BG_H = 30


def _make_background(
    tmp_path: Path, name: str = "bg.png", width: int = _BG_W, height: int = _BG_H
) -> AssetRef:
    """Сохранить валидный PNG на диск (по умолчанию 40×30) и вернуть ссылку на него."""
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("white"))
    path = tmp_path / name
    assert pixmap.save(str(path))
    return AssetRef(asset_id=name, source_path=str(path), display_name=name)


def test_set_background_toggles_has_background_and_placeholder(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """Фон → ``has_background`` True; сброс в ``None`` → False и текст-плейсхолдер."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    assert canvas.has_background() is False  # стартовый плейсхолдер

    canvas.set_background(_make_background(tmp_path))
    assert canvas.has_background() is True

    canvas.set_background(None)
    assert canvas.has_background() is False
    scene = canvas.scene()
    assert scene is not None
    assert any(isinstance(item, QGraphicsTextItem) for item in scene.items())


def test_changing_background_clears_zones(qtbot: QtBot, tmp_path: Path) -> None:
    """Смена фона инвалидирует ранее добавленные зоны (доли привязаны к конкретному фону)."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path, "a.png"))
    canvas.add_zone(0.1, 0.1, 0.4, 0.4)
    assert len(canvas.normalized_zones()) == 1

    canvas.set_background(_make_background(tmp_path, "b.png"))
    assert canvas.normalized_zones() == []


def test_add_zone_round_trips_fractions(qtbot: QtBot, tmp_path: Path) -> None:
    """``add_zone`` из долей → ``normalized_zones`` возвращает те же доли (±округление пикселей).

    Фон 80×60: доли 0.25/0.5 дают >= 16 px по обеим осям, поэтому минимум зоны не вмешивается.
    """
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path, width=80, height=60))

    zone = canvas.add_zone(0.25, 0.25, 0.5, 0.5)
    assert zone is not None
    nx, ny, nw, nh = canvas.normalized_zones()[0]
    assert nx == pytest.approx(0.25, abs=0.02)
    assert ny == pytest.approx(0.25, abs=0.02)
    assert nw == pytest.approx(0.5, abs=0.02)
    assert nh == pytest.approx(0.5, abs=0.02)


def test_zone_marker_follows_resize(qtbot: QtBot, tmp_path: Path) -> None:
    """Пин остаётся в центре редактируемого прямоугольника после resize."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path))
    zone = canvas.add_zone(0.1, 0.1, 0.2, 0.2)
    assert zone is not None
    before = zone.marker.scenePos()

    zone.set_scene_rect(QRectF(24.0, 14.0, 16.0, 16.0))

    assert zone.marker.scenePos() != before
    assert zone.marker.pos() == zone.rect().center()
    assert canvas._zone_for_item(zone.marker) is zone


def test_add_zone_without_background_returns_none(qtbot: QtBot) -> None:
    """Без фона рисование невозможно: ``add_zone`` возвращает ``None`` и зон не появляется."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    assert canvas.add_zone(0.1, 0.1, 0.2, 0.2) is None
    assert canvas.normalized_zones() == []


def test_moving_zone_past_edge_stays_in_bounds(qtbot: QtBot, tmp_path: Path) -> None:
    """``setPos`` далеко за границу фона → доли остаются в [0..1] (кламп в ``itemChange``)."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path))
    zone = canvas.add_zone(0.1, 0.1, 0.3, 0.3)
    assert zone is not None

    zone.setPos(1000.0, 1000.0)
    nx, ny, nw, nh = canvas.normalized_zones()[0]
    assert 0.0 <= nx <= 1.0
    assert 0.0 <= ny <= 1.0
    assert nx + nw <= 1.0 + 1e-6
    assert ny + nh <= 1.0 + 1e-6


def test_set_scene_rect_larger_than_background_is_clamped(
    qtbot: QtBot, tmp_path: Path
) -> None:
    """resize-шов с прямоугольником больше фона → доли клампятся в [0..1] (вся схема)."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path))
    zone = canvas.add_zone(0.1, 0.1, 0.2, 0.2)
    assert zone is not None

    zone.set_scene_rect(QRectF(-50.0, -50.0, 500.0, 500.0))
    nx, ny, nw, nh = zone.normalized(float(_BG_W), float(_BG_H))
    assert nx == pytest.approx(0.0, abs=1e-6)
    assert ny == pytest.approx(0.0, abs=1e-6)
    assert nw == pytest.approx(1.0, abs=1e-6)
    assert nh == pytest.approx(1.0, abs=1e-6)


def test_set_scene_rect_enforces_minimum_size(qtbot: QtBot, tmp_path: Path) -> None:
    """resize-шов с крошечным прямоугольником → соблюдён минимум 2*_HANDLE (доли w/h > 0)."""
    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path))
    zone = canvas.add_zone(0.1, 0.1, 0.2, 0.2)
    assert zone is not None

    zone.set_scene_rect(QRectF(5.0, 5.0, 1.0, 1.0))
    _nx, _ny, nw, nh = zone.normalized(float(_BG_W), float(_BG_H))
    assert nw > 0.0
    assert nh > 0.0
    # Минимум 16 px по обеим осям: 16/40 по ширине и 16/30 по высоте.
    assert nw == pytest.approx(16.0 / _BG_W, abs=0.02)
    assert nh == pytest.approx(16.0 / _BG_H, abs=0.02)


def test_remove_selected_and_clear_zones(qtbot: QtBot, tmp_path: Path) -> None:
    """``remove_selected`` убирает выделенную зону и уведомляет; ``clear_zones`` — все зоны."""
    calls: list[int] = []
    canvas = SchemeZoneCanvas(on_zones_changed=lambda: calls.append(1))
    qtbot.addWidget(canvas)
    canvas.set_background(_make_background(tmp_path))

    first = canvas.add_zone(0.1, 0.1, 0.3, 0.3)
    second = canvas.add_zone(0.5, 0.5, 0.3, 0.3)
    assert first is not None
    assert second is not None

    first.setSelected(True)
    before = len(calls)
    canvas.remove_selected()
    assert len(canvas.normalized_zones()) == 1
    assert len(calls) > before  # уведомление об изменении набора зон

    canvas.clear_zones()
    assert canvas.normalized_zones() == []


def test_renumber_assigns_1based_indices(qtbot: QtBot, tmp_path: Path) -> None:
    """``_renumber`` нумерует зоны 1-based в порядке списка; после удаления индексы сжимаются."""
    from PySide6.QtCore import QRectF

    from epicase_constructor.ui.scheme_zone_canvas import ZoneItem

    canvas = SchemeZoneCanvas()
    qtbot.addWidget(canvas)

    zone_a = ZoneItem(QRectF(0, 0, 20, 20))
    zone_b = ZoneItem(QRectF(0, 0, 20, 20))
    zone_c = ZoneItem(QRectF(0, 0, 20, 20))
    canvas._zones.extend([zone_a, zone_b, zone_c])

    canvas._renumber()
    assert [z._index for z in canvas._zones] == [1, 2, 3]

    canvas._zones.remove(zone_b)
    canvas._renumber()
    assert [z._index for z in canvas._zones] == [1, 2]
