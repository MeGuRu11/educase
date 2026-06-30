"""Контракты адаптивных исходников Windows-иконок."""
from __future__ import annotations

from importlib.resources import files

import pytest
from PySide6.QtCore import QByteArray
from PySide6.QtSvg import QSvgRenderer

_NAMES = (
    "epicase_constructor.svg",
    "epicase_constructor_small.svg",
    "epicase_player.svg",
    "epicase_player_small.svg",
)


def _icon_bytes(name: str) -> bytes:
    return (
        files("epicase_ui")
        .joinpath("resources", "app_icons", name)
        .read_bytes()
    )


@pytest.mark.parametrize("name", _NAMES)
def test_app_icon_svg_is_valid_square_artwork(name: str) -> None:
    """Каждый исходник — валидный квадратный SVG из проектной палитры."""
    data = _icon_bytes(name)
    renderer = QSvgRenderer(QByteArray(data))

    assert renderer.isValid()
    assert renderer.viewBoxF().width() == renderer.viewBoxF().height()
    assert b"#17393A" in data


def test_constructor_and_player_use_distinct_role_signs() -> None:
    """Полные версии различаются знаком проектирования и маршрутом."""
    constructor = _icon_bytes("epicase_constructor.svg")
    player = _icon_bytes("epicase_player.svg")

    assert constructor != player
    assert b"#B49A56" in constructor
    assert b"#0F766E" in player
    assert b'data-role="blueprint"' in constructor
    assert b'data-role="route"' in player


def test_small_sources_drop_fine_detail_and_keep_role_signs() -> None:
    """Оптические версии убирают сетку, но сохраняют различие ролей."""
    constructor = _icon_bytes("epicase_constructor_small.svg")
    player = _icon_bytes("epicase_player_small.svg")

    assert b'data-detail="grid"' not in constructor
    assert b'data-role="blueprint"' in constructor
    assert b'data-role="route"' in player
