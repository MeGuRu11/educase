from collections.abc import Callable
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """Изолируем каталог данных, чтобы тесты не писали в %LOCALAPPDATA%."""
    monkeypatch.setenv("EPICASE_DATA_DIR", str(tmp_path))


@pytest.fixture
def png_bytes() -> Callable[..., bytes]:
    """Фабрика валидных PNG-байтов через Qt (требует QApplication — заказывать с ``qtbot``).

    Импорт PySide6 ленивый (внутри фабрики), чтобы не тянуть Qt в не-Qt тесты ядра.
    """

    def _make(width: int = 8, height: int = 8) -> bytes:
        from PySide6.QtCore import QBuffer, QByteArray
        from PySide6.QtGui import QColor, QPixmap

        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("red"))
        buffer = QByteArray()
        device = QBuffer(buffer)
        device.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.save(device, "PNG")
        device.close()
        return bytes(buffer.data())

    return _make