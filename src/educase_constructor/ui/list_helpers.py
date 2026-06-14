"""Общие хелперы пустого состояния для списочных редакторов Constructor.

Подсказка-плейсхолдер показывается, пока список пуст, и скрывается, как только в нём
появляется хотя бы один элемент. Без QSS: приглушённый вид даёт ``setEnabled(False)``.
"""
from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget


def wrap_in_card(content: QWidget, title: str) -> QGroupBox:
    """Обернуть виджет в QGroupBox с заголовком-номером для карточного вида списка."""
    card = QGroupBox(title)
    layout = QVBoxLayout(card)
    layout.addWidget(content)
    return card


def make_placeholder(text: str) -> QLabel:
    """Создать приглушённую подсказку пустого состояния (без стилевого слоя)."""
    label = QLabel(text)
    label.setEnabled(False)
    return label


def refresh_placeholder(placeholder: QLabel, is_empty: bool) -> None:
    """Показать подсказку, когда список пуст, и скрыть, когда в нём есть элементы."""
    placeholder.setVisible(is_empty)
