"""Виджеты выбора файлов-ассетов (Constructor): Проводник → стабильные id-ссылки.

Вариант B: ``asset_id`` стабилен (``uuid4`` + исходное расширение), исходное имя файла
хранится только для показа. ``AssetPicker`` — один файл (схема этапа), ``AssetListPicker`` —
несколько (фото среды, ассеты карточки, изображения точки поиска). Без визуальной полировки:
только функциональные виджеты и layout-менеджеры. Кнопки открывают ``QFileDialog``; тестируемые
швы ``set_file``/``add_file`` делают ту же работу без диалога.
"""
from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_core.application.case_builder import AssetRef

_PLACEHOLDER = "файл не выбран"
_IMAGE_FILTER = "Изображения (*.png *.jpg *.jpeg *.bmp *.gif)"


def _make_ref(path: str) -> AssetRef:
    """Собрать ``AssetRef`` из пути: стабильный id (``uuid4`` + расширение) + имя для показа."""
    source = Path(path)
    return AssetRef(
        asset_id=f"{uuid4().hex}{source.suffix}",
        source_path=path,
        display_name=source.name,
    )


class AssetPicker(QWidget):
    """Выбор файла-ассета: метка имени + кнопки «Обзор…»/«Очистить»; стабильный id-ссылка."""

    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._ref: AssetRef | None = None

        self.name_label = QLabel(_PLACEHOLDER, self)
        self.browse_button = QPushButton("Обзор…", self)
        self.clear_button = QPushButton("Очистить", self)
        self.browse_button.clicked.connect(self._browse)
        self.clear_button.clicked.connect(self.clear)

        layout = QHBoxLayout(self)
        layout.addWidget(self.name_label)
        layout.addWidget(self.browse_button)
        layout.addWidget(self.clear_button)

    def _browse(self) -> None:
        """Открыть Проводник и, если файл выбран, передать путь в ``set_file``."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", _IMAGE_FILTER
        )
        if path:
            self.set_file(path)

    def set_file(self, path: str) -> None:
        """Зафиксировать выбранный файл: сгенерировать стабильный id, обновить метку.

        Тестируемый шов: делает то же, что колбэк диалога, но без ``QFileDialog``.
        ``asset_id`` — ``uuid4`` + исходное расширение; имя файла хранится лишь для показа.
        """
        self._ref = _make_ref(path)
        self.name_label.setText(self._ref.display_name)
        self.changed.emit()

    def set_ref(self, ref: AssetRef) -> None:
        """Восстановить готовую ссылку на ассет без файла/диалога (открытие кейса на правку).

        Имя исходного файла при загрузке утрачено — показываем ``display_name`` (= ``asset_id``)
        или запасное «вложение», если он пуст.
        """
        self._ref = ref
        self.name_label.setText(ref.display_name or "вложение")
        self.changed.emit()

    def clear(self) -> None:
        """Сбросить выбор: ссылка → ``None``, метка → плейсхолдер."""
        self._ref = None
        self.name_label.setText(_PLACEHOLDER)
        self.changed.emit()

    def value(self) -> AssetRef | None:
        """Вернуть ``AssetRef`` выбранного файла или ``None``, если файл не выбран."""
        return self._ref


class AssetListPicker(QWidget):
    """Выбор нескольких файлов-ассетов: список имён + кнопки добавления/удаления последнего."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._refs: list[AssetRef] = []

        self.files_list = QListWidget(self)
        self.add_button = QPushButton("Добавить файл…", self)
        self.remove_button = QPushButton("Удалить последний", self)
        self.add_button.clicked.connect(self._browse)
        self.remove_button.clicked.connect(self.remove_last)

        buttons = QHBoxLayout()
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.files_list)
        layout.addLayout(buttons)

    def _browse(self) -> None:
        """Открыть Проводник и, если файл выбран, добавить его через ``add_file``."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "", _IMAGE_FILTER
        )
        if path:
            self.add_file(path)

    def add_file(self, path: str) -> None:
        """Добавить выбранный файл в конец списка: стабильный ``AssetRef`` + строка имени.

        Тестируемый шов: делает то же, что колбэк диалога, но без ``QFileDialog``.
        """
        ref = _make_ref(path)
        self._refs.append(ref)
        self.files_list.addItem(ref.display_name)

    def load(self, refs: Sequence[AssetRef]) -> None:
        """Восстановить список готовых ссылок на ассеты без файлов/диалога (открытие на правку).

        Сбрасывает текущий выбор и заполняет список из ``refs``; имя строки — ``display_name``
        (= ``asset_id``) или запасное «вложение».
        """
        self.clear()
        for ref in refs:
            self._refs.append(ref)
            self.files_list.addItem(ref.display_name or "вложение")

    def remove_last(self) -> None:
        """Удалить последний выбранный файл (если он есть)."""
        if not self._refs:
            return
        self._refs.pop()
        self.files_list.takeItem(self.files_list.count() - 1)

    def clear(self) -> None:
        """Сбросить список выбранных файлов."""
        self._refs.clear()
        self.files_list.clear()

    def value(self) -> tuple[AssetRef, ...]:
        """Вернуть кортеж ``AssetRef`` всех выбранных файлов (в порядке добавления)."""
        return tuple(self._refs)
