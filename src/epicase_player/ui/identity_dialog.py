"""Темизированный диалог личности курсанта при сохранении результата.

Заменяет сырой ``QInputDialog``: собирает ФИО (обязательно), звание и учебную
группу с живой сводкой. Обязательность ФИО — забота UI (включение кнопки
«Сохранить»); на уровне модели поля остаются необязательными (см. AttemptMeta).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class IdentityDialog(QDialog):
    """Модальная форма данных курсанта: ФИО / звание / учебная группа."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("schemeReveal")
        self.setWindowTitle("Данные курсанта")
        self.setMinimumWidth(420)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(10)

        title_label = QLabel("Данные курсанта")
        title_label.setObjectName("schemeRevealTitle")
        title_label.setWordWrap(True)
        outer.addWidget(title_label)

        card_frame = QFrame()
        card_frame.setObjectName("schemeRevealCard")
        form = QFormLayout(card_frame)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(8)

        self._fio = QLineEdit()
        self._rank = QLineEdit()
        self._group = QLineEdit()
        form.addRow("ФИО", self._fio)
        form.addRow("Звание", self._rank)
        form.addRow("Учебная группа", self._group)
        outer.addWidget(card_frame)

        self._summary = QLabel()
        self._summary.setObjectName("mutedHint")
        self._summary.setWordWrap(True)
        outer.addWidget(self._summary)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("startSecondaryButton")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self._save_btn = QPushButton("Сохранить")
        self._save_btn.setObjectName("schemeRevealClose")
        self._save_btn.setDefault(True)
        self._save_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._save_btn)
        outer.addLayout(btn_row)

        self._fio.textChanged.connect(self._update_summary)
        self._rank.textChanged.connect(self._update_summary)
        self._group.textChanged.connect(self._update_summary)
        self._fio.textChanged.connect(self._update_save_enabled)

        self._update_summary()
        self._update_save_enabled()

    def _update_summary(self) -> None:
        """Обновить строку-сводку по текущим значениям полей."""
        fio = self._fio.text().strip()
        if not fio:
            self._summary.setText("Укажите ФИО, чтобы сохранить")
            return
        parts = [fio]
        rank = self._rank.text().strip()
        if rank:
            parts.append(rank)
        group = self._group.text().strip()
        if group:
            parts.append(group)
        self._summary.setText("Вы: " + ", ".join(parts))

    def _update_save_enabled(self) -> None:
        """Кнопка «Сохранить» активна только при непустом ФИО (после strip)."""
        self._save_btn.setEnabled(bool(self._fio.text().strip()))

    def full_name(self) -> str:
        """ФИО курсанта (обрезанное)."""
        return self._fio.text().strip()

    def rank(self) -> str:
        """Звание курсанта (обрезанное)."""
        return self._rank.text().strip()

    def study_group(self) -> str:
        """Учебная группа курсанта (обрезанная)."""
        return self._group.text().strip()
