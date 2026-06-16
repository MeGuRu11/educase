"""Редактор группы синонимов (Constructor): канонический термин + синонимы через запятую.

Без визуальной полировки: только функциональные виджеты и layout-менеджеры. Публичные поля
ввода — точки доступа для тестов. Сборка значений в драфт — через ``to_draft``.
Переиспользуется и в поиске (триггеры точки поиска), и в других местах с синонимами.
"""
from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from educase_core.application.case_builder import SynonymSetDraft


class SynonymSetEditor(QWidget):
    """Редактор группы синонимов: канонический термин и список синонимов через запятую."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.canonical_edit = QLineEdit(self)
        self.canonical_edit.setPlaceholderText("Основное ключевое слово")
        self.synonyms_edit = QLineEdit(self)
        self.synonyms_edit.setPlaceholderText("Синонимы через запятую")

        form = QFormLayout(self)
        form.addRow("Основной термин", self.canonical_edit)
        form.addRow("Синонимы (через запятую)", self.synonyms_edit)

    def _collect_synonyms(self) -> tuple[str, ...]:
        parts = (chunk.strip() for chunk in self.synonyms_edit.text().split(","))
        return tuple(part for part in parts if part)

    def to_draft(self) -> SynonymSetDraft:
        """Собрать ``SynonymSetDraft`` из текущих значений виджетов."""
        return SynonymSetDraft(
            canonical=self.canonical_edit.text(),
            synonyms=self._collect_synonyms(),
        )
