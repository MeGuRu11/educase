"""Allowlist инфраструктурных иконок хотспотов."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

DEFAULT_HOTSPOT_ICON_KEY = "inspect"
_PIN_COLOR = QColor("#0F766E")


@dataclass(frozen=True)
class HotspotIconSpec:
    """Стабильный ключ и русская подпись одной package-иконки."""

    key: str
    label: str


_SPECS = (
    HotspotIconSpec("inspect", "Объект осмотра"),
    HotspotIconSpec("barracks", "Казарма / жилое помещение"),
    HotspotIconSpec("canteen", "Столовая / пищеблок"),
    HotspotIconSpec("medical", "Медпункт / изолятор"),
    HotspotIconSpec("water", "Водоснабжение"),
    HotspotIconSpec("sanitary", "Санитарный узел"),
    HotspotIconSpec("storage", "Склад"),
    HotspotIconSpec("cold_storage", "Холодильная камера"),
    HotspotIconSpec("waste", "Отходы"),
    HotspotIconSpec("entrance", "Вход / КПП"),
)
_BY_KEY = {spec.key: spec for spec in _SPECS}


def hotspot_icon_specs() -> tuple[HotspotIconSpec, ...]:
    """Вернуть каталог иконок в порядке показа в Constructor."""
    return _SPECS


def hotspot_icon_spec(key: str) -> HotspotIconSpec:
    """Разрешить ключ через allowlist с fallback на универсальный осмотр."""
    return _BY_KEY.get(key, _BY_KEY[DEFAULT_HOTSPOT_ICON_KEY])


def hotspot_icon_svg_bytes(key: str) -> bytes:
    """Вернуть байты безопасно разрешённого package SVG."""
    spec = hotspot_icon_spec(key)
    resource = files("epicase_ui").joinpath(
        "resources", "hotspots", f"{spec.key}.svg"
    )
    try:
        data = resource.read_bytes()
    except OSError:
        if spec.key == DEFAULT_HOTSPOT_ICON_KEY:
            raise
        return hotspot_icon_svg_bytes(DEFAULT_HOTSPOT_ICON_KEY)
    if QSvgRenderer(QByteArray(data)).isValid():
        return data
    if spec.key == DEFAULT_HOTSPOT_ICON_KEY:
        raise ValueError("Некорректный SVG универсальной иконки хотспота")
    return hotspot_icon_svg_bytes(DEFAULT_HOTSPOT_ICON_KEY)


def hotspot_icon_qicon(key: str) -> QIcon:
    """Собрать компактный QIcon для списка Constructor."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_PIN_COLOR)
    painter.drawRoundedRect(QRectF(0.0, 0.0, 32.0, 32.0), 7.0, 7.0)
    renderer = QSvgRenderer(QByteArray(hotspot_icon_svg_bytes(key)))
    renderer.render(painter, QRectF(6.0, 6.0, 20.0, 20.0))
    painter.end()
    return QIcon(pixmap)


__all__ = [
    "DEFAULT_HOTSPOT_ICON_KEY",
    "HotspotIconSpec",
    "hotspot_icon_qicon",
    "hotspot_icon_spec",
    "hotspot_icon_specs",
    "hotspot_icon_svg_bytes",
]
