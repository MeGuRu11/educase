"""Виджет показа изображения-ассета Player: реальный PNG/JPG из ``{asset_id: bytes}``.

Read-only: ассеты только рисуются, в ответ ``Attempt`` не входят (ADR-008). На «висячую
ссылку» (нет байт в ``assets`` или байты не декодируются как изображение) показывается
заглушка-плейсхолдер, а не исключение — Player не должен падать на битом/неполном архиве.
"""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

_MAX_WIDTH = 600


class AssetImageWidget(QWidget):
    """Показ изображения ассета по id; при недоступности/ошибке декодирования — плейсхолдер."""

    def __init__(
        self,
        asset_id: str,
        assets: Mapping[str, bytes],
        caption: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._has_image = False

        layout = QVBoxLayout(self)
        if caption:
            layout.addWidget(QLabel(caption))

        image_label = QLabel()
        layout.addWidget(image_label)

        data = assets.get(asset_id)
        if data is None:
            image_label.setText("Изображение недоступно")
            image_label.setEnabled(False)
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            image_label.setText("Не удалось загрузить изображение")
            image_label.setEnabled(False)
            return

        if pixmap.width() > _MAX_WIDTH:
            pixmap = pixmap.scaledToWidth(
                _MAX_WIDTH, Qt.TransformationMode.SmoothTransformation
            )
        image_label.setPixmap(pixmap)
        self._has_image = True

    def has_image(self) -> bool:
        """``True``, только если pixmap успешно загружен (для тестов и инварианта)."""
        return self._has_image
