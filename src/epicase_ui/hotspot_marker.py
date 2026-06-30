"""Общий картографический пин хотспота для Graphics View."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QGraphicsItem,
    QStyleOptionGraphicsItem,
    QWidget,
)

from epicase_ui.hotspot_icons import (
    hotspot_icon_spec,
    hotspot_icon_svg_bytes,
)

_PIN_COLOR = QColor("#0F766E")
_DEEP_TEAL = QColor("#17393A")
_WHITE = QColor("#FFFFFF")


class HotspotMarkerItem(QGraphicsItem):
    """Неизменяемый при зуме пин с инфраструктурной иконкой и подписью."""

    PIN_RADIUS = 22.0
    PIN_TIP_Y = 28.0
    LABEL_WIDTH = 160.0
    _LABEL_GAP = 6.0
    _LABEL_HORIZONTAL_PADDING = 7.0
    _LABEL_VERTICAL_PADDING = 4.0

    def __init__(
        self,
        icon_key: str,
        label: str = "",
        label_above: bool = False,
        parent: QGraphicsItem | None = None,
    ) -> None:
        super().__init__(parent)
        self._font = QFont("Segoe UI", 9)
        self._font.setBold(True)
        self._label = label.strip()
        self._label_above = label_above
        self._label_lines = self._wrap_label(self._label)
        self._label_rect = self._make_label_rect()
        self._icon_key = ""
        self._renderer = QSvgRenderer()
        self.set_icon_key(icon_key)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True
        )
        self.setToolTip(label)

    @property
    def icon_key(self) -> str:
        """Вернуть фактически отображаемый allowlist-ключ."""
        return self._icon_key

    @property
    def label(self) -> str:
        """Вернуть полную подпись маркера."""
        return self._label

    @property
    def label_lines(self) -> tuple[str, ...]:
        """Вернуть не более двух визуальных строк подписи."""
        return self._label_lines

    @property
    def label_above(self) -> bool:
        """Показывается ли подпись над пином."""
        return self._label_above

    def set_icon_key(self, key: str) -> None:
        """Сменить иконку через allowlist, сохраняя геометрию маркера."""
        resolved = hotspot_icon_spec(key).key
        if resolved == self._icon_key:
            return
        renderer = QSvgRenderer(QByteArray(hotspot_icon_svg_bytes(resolved)))
        if not renderer.isValid():
            resolved = hotspot_icon_spec("").key
            renderer = QSvgRenderer(
                QByteArray(hotspot_icon_svg_bytes(resolved))
            )
        self._icon_key = resolved
        self._renderer = renderer
        self.update()

    def _wrap_label(self, label: str) -> tuple[str, ...]:
        """Разбить подпись максимум на две строки с elide второй."""
        if not label:
            return ()
        metrics = QFontMetrics(self._font)
        content_width = int(
            self.LABEL_WIDTH - self._LABEL_HORIZONTAL_PADDING * 2
        )
        words = label.split()
        first_words: list[str] = []
        split_at = len(words)
        for index, word in enumerate(words):
            candidate = " ".join((*first_words, word))
            if first_words and metrics.horizontalAdvance(candidate) > content_width:
                split_at = index
                break
            if not first_words and metrics.horizontalAdvance(word) > content_width:
                first_words.append(
                    metrics.elidedText(
                        word, Qt.TextElideMode.ElideRight, content_width
                    )
                )
                split_at = index + 1
                break
            first_words.append(word)
        first_line = " ".join(first_words)
        if split_at >= len(words):
            return (first_line,)
        second_line = metrics.elidedText(
            " ".join(words[split_at:]),
            Qt.TextElideMode.ElideRight,
            content_width,
        )
        return (first_line, second_line)

    def _make_label_rect(self) -> QRectF:
        """Рассчитать карточку подписи относительно центра пина."""
        if not self._label_lines:
            return QRectF()
        metrics = QFontMetrics(self._font)
        text_width = max(
            metrics.horizontalAdvance(line) for line in self._label_lines
        )
        width = min(
            self.LABEL_WIDTH,
            text_width + self._LABEL_HORIZONTAL_PADDING * 2,
        )
        height = (
            metrics.lineSpacing() * len(self._label_lines)
            + self._LABEL_VERTICAL_PADDING * 2
        )
        if self._label_above:
            y = -self.PIN_RADIUS - self._LABEL_GAP - height
        else:
            y = self.PIN_TIP_Y + self._LABEL_GAP
        return QRectF(-width / 2.0, y, width, height)

    def boundingRect(self) -> QRectF:
        """Вернуть фиксированную экранную геометрию маркера."""
        pin = QRectF(
            -self.PIN_RADIUS - 2.0,
            -self.PIN_RADIUS - 2.0,
            self.PIN_RADIUS * 2 + 4.0,
            self.PIN_RADIUS + self.PIN_TIP_Y + 4.0,
        )
        return pin.united(self._label_rect)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ) -> None:
        """Нарисовать пин, пиктограмму и подпись."""
        del option, widget
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pointer = QPainterPath()
        pointer.moveTo(-9.0, 13.0)
        pointer.lineTo(9.0, 13.0)
        pointer.lineTo(0.0, self.PIN_TIP_Y)
        pointer.closeSubpath()
        painter.setPen(QPen(_WHITE, 3.0))
        painter.setBrush(QBrush(_PIN_COLOR))
        painter.drawPath(pointer)
        painter.drawEllipse(
            QRectF(
                -self.PIN_RADIUS,
                -self.PIN_RADIUS,
                self.PIN_RADIUS * 2,
                self.PIN_RADIUS * 2,
            )
        )
        self._renderer.render(painter, QRectF(-12.0, -12.0, 24.0, 24.0))

        if not self._label_lines:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(_DEEP_TEAL))
        painter.drawRoundedRect(self._label_rect, 6.0, 6.0)
        painter.setPen(QPen(_WHITE))
        painter.setFont(self._font)
        metrics = QFontMetrics(self._font)
        baseline = (
            self._label_rect.top()
            + self._LABEL_VERTICAL_PADDING
            + metrics.ascent()
        )
        for index, line in enumerate(self._label_lines):
            line_rect = QRectF(
                self._label_rect.left(),
                baseline - metrics.ascent() + index * metrics.lineSpacing(),
                self._label_rect.width(),
                metrics.lineSpacing(),
            )
            painter.drawText(
                line_rect,
                Qt.AlignmentFlag.AlignHCenter
                | Qt.AlignmentFlag.AlignVCenter,
                line,
            )


__all__ = ["HotspotMarkerItem"]
