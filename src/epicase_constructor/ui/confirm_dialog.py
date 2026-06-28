"""Переиспользуемый диалог подтверждения деструктивных действий в теме EpiCase."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_WARNING_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 72" width="72" height="72">'
    b'<path d="M36 8 L68 64 H4 Z" fill="#FBEEE6" stroke="#C0392B" stroke-width="3"'
    b' stroke-linejoin="round"/>'
    b'<rect x="33" y="28" width="6" height="20" rx="3" fill="#C0392B"/>'
    b'<circle cx="36" cy="54" r="3.5" fill="#C0392B"/>'
    b'</svg>'
)


def _warning_badge(size: int = 72) -> QLabel:
    renderer = QSvgRenderer(QByteArray(_WARNING_SVG))
    px = QPixmap(size * 2, size * 2)
    px.setDevicePixelRatio(2.0)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    renderer.render(painter, QRectF(0, 0, float(size), float(size)))
    painter.end()
    lbl = QLabel()
    lbl.setPixmap(px)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class ConfirmDialog(QDialog):
    """Модальный диалог подтверждения деструктивного действия в теме EpiCase.

    cancel — default-кнопка (Enter/Esc → безопасный отказ).
    """

    def __init__(
        self,
        *,
        title: str,
        message: str,
        confirm_label: str,
        cancel_label: str = "Отмена",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        outer = QVBoxLayout(self)
        outer.addStretch(1)

        card = QFrame()
        card.setObjectName("confirmCard")
        card.setMaximumWidth(460)
        inner = QVBoxLayout(card)
        inner.setSpacing(14)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        inner.addWidget(_warning_badge())

        title_lbl = QLabel(title)
        title_lbl.setObjectName("confirmTitle")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        inner.addWidget(title_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setObjectName("confirmText")
        msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        inner.addWidget(msg_lbl)

        btn_confirm = QPushButton(confirm_label)
        btn_confirm.setObjectName("confirmDiscardButton")
        btn_confirm.setAutoDefault(False)
        btn_confirm.clicked.connect(self.accept)

        btn_cancel = QPushButton(cancel_label)
        btn_cancel.setObjectName("confirmCancelButton")
        btn_cancel.setDefault(True)
        btn_cancel.clicked.connect(self.reject)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_confirm)
        btn_row.addStretch()
        inner.addLayout(btn_row)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch(1)
