"""Собрать многокадровые Windows ICO из адаптивных SVG EpiCase."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QImage, QImageWriter, QPainter
from PySide6.QtSvg import QSvgRenderer

ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
_SMALL_MAX_SIZE = 24
_PIXELS_PER_METER_96_DPI = 3780
_APP_NAMES = ("constructor", "player")
_RESOURCE_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "epicase_ui"
    / "resources"
    / "app_icons"
)


@dataclass(frozen=True)
class IconSource:
    """Полный и оптически упрощённый SVG одного приложения."""

    full_svg: bytes
    small_svg: bytes


def _render_png(svg: bytes, size: int) -> bytes:
    """Отрисовать квадратный SVG в прозрачный PNG заданного размера."""
    renderer = QSvgRenderer(QByteArray(svg))
    if not renderer.isValid():
        raise ValueError("Некорректный SVG исходника иконки")

    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)
    image.setDotsPerMeterX(_PIXELS_PER_METER_96_DPI)
    image.setDotsPerMeterY(_PIXELS_PER_METER_96_DPI)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    renderer.render(painter, QRectF(0.0, 0.0, float(size), float(size)))
    painter.end()

    encoded = QByteArray()
    buffer = QBuffer(encoded)
    if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
        raise RuntimeError("Не удалось открыть буфер PNG")
    writer = QImageWriter(buffer, b"PNG")
    if not writer.write(image):
        buffer.close()
        raise RuntimeError(
            f"Не удалось закодировать PNG-кадр: {writer.errorString()}"
        )
    buffer.close()
    return bytes(encoded.data())


def build_ico(source: IconSource) -> bytes:
    """Собрать ICO с PNG-кадрами из full/small SVG."""
    frames = [
        (
            size,
            _render_png(
                source.small_svg if size <= _SMALL_MAX_SIZE else source.full_svg,
                size,
            ),
        )
        for size in ICON_SIZES
    ]
    header = struct.pack("<HHH", 0, 1, len(frames))
    offset = len(header) + len(frames) * 16
    entries: list[bytes] = []
    payloads: list[bytes] = []
    for size, payload in frames:
        encoded_size = size if size < 256 else 0
        entries.append(
            struct.pack(
                "<BBBBHHII",
                encoded_size,
                encoded_size,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        payloads.append(payload)
        offset += len(payload)
    return b"".join((header, *entries, *payloads))


def _read_source(resource_dir: Path, app_name: str) -> IconSource:
    """Прочитать пару SVG для имени из внутреннего allowlist."""
    if app_name not in _APP_NAMES:
        raise ValueError(f"Неизвестное приложение: {app_name}")
    return IconSource(
        full_svg=(resource_dir / f"epicase_{app_name}.svg").read_bytes(),
        small_svg=(resource_dir / f"epicase_{app_name}_small.svg").read_bytes(),
    )


def generate_all(resource_dir: Path = _RESOURCE_DIR) -> None:
    """Собрать оба ICO и заменить ресурсы только после успешного рендера."""
    generated = {
        app_name: build_ico(_read_source(resource_dir, app_name))
        for app_name in _APP_NAMES
    }
    temporary_paths: list[Path] = []
    try:
        for app_name, data in generated.items():
            temporary = resource_dir / f".epicase_{app_name}.ico.tmp"
            temporary.write_bytes(data)
            temporary_paths.append(temporary)
        for app_name, temporary in zip(
            _APP_NAMES, temporary_paths, strict=True
        ):
            temporary.replace(resource_dir / f"epicase_{app_name}.ico")
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)


def main() -> int:
    """Собрать package-ресурсы Constructor и Player."""
    generate_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
