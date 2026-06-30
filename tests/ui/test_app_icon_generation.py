"""Структура и воспроизводимость Windows ICO."""
from __future__ import annotations

import struct
import tomllib
from importlib.resources import files
from pathlib import Path

import pytest
from PySide6.QtGui import QImage
from pytestqt.qtbot import QtBot
from tools.generate_app_icons import ICON_SIZES, IconSource, build_ico


def _resource(name: str) -> bytes:
    return (
        files("epicase_ui")
        .joinpath("resources", "app_icons", name)
        .read_bytes()
    )


def _frames(data: bytes) -> list[tuple[int, bytes]]:
    reserved, kind, count = struct.unpack_from("<HHH", data)
    assert (reserved, kind, count) == (0, 1, len(ICON_SIZES))
    directory_end = 6 + count * 16
    frames: list[tuple[int, bytes]] = []
    for index in range(count):
        width, height, colors, reserved_byte, planes, bpp, length, offset = (
            struct.unpack_from("<BBBBHHII", data, 6 + index * 16)
        )
        assert colors == 0
        assert reserved_byte == 0
        assert planes == 1
        assert bpp == 32
        assert offset >= directory_end
        assert offset + length <= len(data)
        size = width or 256
        assert (height or 256) == size
        frames.append((size, data[offset : offset + length]))
    return frames


@pytest.mark.parametrize("app", ("constructor", "player"))
def test_checked_in_ico_has_exact_png_frames(app: str) -> None:
    """ICO содержит полный упорядоченный набор валидных PNG-кадров."""
    frames = _frames(_resource(f"epicase_{app}.ico"))

    assert tuple(size for size, _ in frames) == ICON_SIZES
    for size, payload in frames:
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")
        image = QImage.fromData(payload)
        assert not image.isNull()
        assert (image.width(), image.height()) == (size, size)
        assert image.hasAlphaChannel()


@pytest.mark.parametrize("app", ("constructor", "player"))
def test_checked_in_ico_is_reproducible_with_qapplication(
    app: str, qtbot: QtBot
) -> None:
    """Checked-in ICO не зависит от инициализации QApplication в полном suite."""
    source = IconSource(
        full_svg=_resource(f"epicase_{app}.svg"),
        small_svg=_resource(f"epicase_{app}_small.svg"),
    )

    assert build_ico(source) == _resource(f"epicase_{app}.ico")


def test_build_ico_rejects_invalid_svg() -> None:
    """Невалидный full или small SVG останавливает сборку."""
    with pytest.raises(ValueError, match="Некорректный SVG"):
        build_ico(IconSource(full_svg=b"broken", small_svg=b"broken"))


def test_wheel_config_explicitly_includes_ico_resources() -> None:
    """Wheel-конфигурация явно сохраняет ICO как package artifacts."""
    pyproject_path = Path(__file__).parents[2] / "pyproject.toml"
    config = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    artifacts = config["tool"]["hatch"]["build"]["targets"]["wheel"][
        "artifacts"
    ]

    assert "src/epicase_ui/resources/**/*.ico" in artifacts
