"""Тесты AssetImageWidget: реальный рендер + инвариант висячей ссылки (плейсхолдер, не падение)."""
from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QLabel
from pytestqt.qtbot import QtBot

from epicase_player.ui.asset_image_widget import AssetImageWidget


def test_valid_png_renders_image(qtbot: QtBot, png_bytes: Callable[..., bytes]) -> None:
    """Валидные PNG-байты по asset_id → ``has_image()`` True."""
    data = png_bytes()
    widget = AssetImageWidget("img-1", {"img-1": data})
    qtbot.addWidget(widget)
    assert widget.has_image() is True


def test_missing_asset_id_shows_placeholder(qtbot: QtBot) -> None:
    """asset_id отсутствует в assets → ``has_image()`` False, без исключения (плейсхолдер)."""
    widget = AssetImageWidget("ghost", {})
    qtbot.addWidget(widget)
    assert widget.has_image() is False
    texts = [lbl.text() for lbl in widget.findChildren(QLabel)]
    assert any("недоступно" in t for t in texts)


def test_garbage_bytes_show_placeholder(qtbot: QtBot) -> None:
    """Мусорные (не изображение) байты → ``has_image()`` False, без исключения."""
    widget = AssetImageWidget("broken", {"broken": b"not an image"})
    qtbot.addWidget(widget)
    assert widget.has_image() is False
    texts = [lbl.text() for lbl in widget.findChildren(QLabel)]
    assert any("Не удалось загрузить" in t for t in texts)


def test_caption_shown_above_image(qtbot: QtBot, png_bytes: Callable[..., bytes]) -> None:
    """Непустой caption выводится отдельной меткой над изображением."""
    widget = AssetImageWidget("img-1", {"img-1": png_bytes()}, caption="Схема")
    qtbot.addWidget(widget)
    texts = [lbl.text() for lbl in widget.findChildren(QLabel)]
    assert "Схема" in texts


def _rendered_pixmap_width(widget: AssetImageWidget) -> int:
    """Ширина отрисованного pixmap: единственная метка виджета, несущая непустой pixmap."""
    with_pixmap = [
        lbl for lbl in widget.findChildren(QLabel) if not lbl.pixmap().isNull()
    ]
    assert len(with_pixmap) == 1
    return with_pixmap[0].pixmap().width()


def test_wide_image_scaled_to_max_width(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Широкое изображение (> 600px) масштабируется до 600px (сохранение валидности и ширины)."""
    data = png_bytes(width=900, height=300)
    widget = AssetImageWidget("wide", {"wide": data})
    qtbot.addWidget(widget)
    assert widget.has_image() is True
    assert _rendered_pixmap_width(widget) == 600


def test_narrow_image_not_scaled(
    qtbot: QtBot, png_bytes: Callable[..., bytes]
) -> None:
    """Изображение шириной ≤ 600px не масштабируется — исходная ширина сохраняется."""
    data = png_bytes(width=120, height=80)
    widget = AssetImageWidget("narrow", {"narrow": data})
    qtbot.addWidget(widget)
    assert widget.has_image() is True
    assert _rendered_pixmap_width(widget) == 120
