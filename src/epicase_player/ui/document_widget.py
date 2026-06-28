"""Виджет задания выбора документа с обманками и заполнением полей (ADR-007/ADR-008)."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.documents import DocumentOption, DocumentTask, FillMode
from epicase_core.theme.file_labels import file_size_label, file_type_label
from epicase_player.ui.asset_image_widget import AssetImageWidget
from epicase_player.ui.document_field_widget import DocumentFieldWidget

_MAX_ATTACHMENTS = 10
_ATTACHMENT_LIMIT_MESSAGE = "Можно прикрепить не более 10 файлов"


@dataclass(frozen=True)
class DocumentResult:
    """Результат заполнения задания выбора документа (для финального отчёта)."""

    option_id: str | None
    option_correct: bool
    fields_ok: tuple[tuple[str, bool], ...]  # (field_id, прошло ли check)


class DocumentWidget(QWidget):
    """Задание: выбрать документ из списка с обманками и заполнить его поля.

    Сверка — только через DocumentOption.is_correct / DocumentField.check (ADR-006/007).
    Неверный выбор и заполнение не блокируют навигацию (ADR-008).
    Предварительные статусы машинной проверки в Player не показываются. Constructor
    даёт преподавателю подробную рекомендательную сверку, а окончательную оценку
    принимает преподаватель (ADR-016).
    """

    def __init__(
        self,
        task: DocumentTask,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._task = task
        self._assets: Mapping[str, bytes] = assets if assets is not None else {}
        self._result: DocumentResult | None = None
        self._field_widgets: list[DocumentFieldWidget] = []
        self._attachments: list[tuple[str, str]] = []
        self._attach_bytes: dict[str, bytes] = {}
        self._attach_cards_layout: QVBoxLayout | None = None
        self._attach_header: QLabel | None = None
        self._attach_empty: QLabel | None = None
        self._attach_button: QPushButton | None = None

        layout = QVBoxLayout(self)

        prompt_label = QLabel(task.prompt)
        prompt_label.setWordWrap(True)
        layout.addWidget(prompt_label)

        if task.reference_assets:
            ref_header = QLabel("Справочные документы")
            ref_header.setObjectName("mutedHint")
            layout.addWidget(ref_header)
            for asset_id in task.reference_assets:
                layout.addWidget(AssetImageWidget(asset_id, self._assets, caption="Справка"))

        self.options_combo = QComboBox()
        self.options_combo.setPlaceholderText("— выберите документ —")
        for opt in task.options:
            self.options_combo.addItem(opt.title)
        self.options_combo.setCurrentIndex(-1)
        layout.addWidget(self.options_combo)

        self.form_area = QWidget()
        self._form_layout = QVBoxLayout(self.form_area)
        self._form_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.form_area)

        self.btn_submit = QPushButton("Готово")
        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_submit)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._status_label = QLabel()
        self._status_label.setObjectName("mutedHint")
        layout.addWidget(self._status_label)

        self.options_combo.currentIndexChanged.connect(self._rebuild_form)
        self.btn_submit.clicked.connect(self.on_submit)

    @property
    def result(self) -> DocumentResult | None:
        """Результат последнего on_submit; None до нажатия «Готово»."""
        return self._result

    def selected_option(self) -> DocumentOption | None:
        """Выбранный DocumentOption; None при плейсхолдере (currentIndex < 0)."""
        idx = self.options_combo.currentIndex()
        if idx < 0:
            return None
        return self._task.options[idx]

    def current_field_widgets(self) -> list[DocumentFieldWidget]:
        """Текущие виджеты полей (пусто, если обманка или документ не выбран)."""
        return list(self._field_widgets)

    def attachments(self) -> tuple[tuple[str, str], ...]:
        """Пары (asset_id, имя_файла) в режиме ATTACHMENT; пусто иначе."""
        return tuple(self._attachments)

    def attachment_bytes(self) -> dict[str, bytes]:
        """Байты вложений по asset_id в режиме ATTACHMENT; пусто иначе."""
        return dict(self._attach_bytes)

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Выберите файл(ы)")
        if not paths:
            return
        available = _MAX_ATTACHMENTS - len(self._attachments)
        self._status_label.setText(
            _ATTACHMENT_LIMIT_MESSAGE if len(paths) > available else ""
        )
        for p in paths[:available]:
            data = Path(p).read_bytes()
            name = Path(p).name
            asset_id = "att-" + uuid4().hex + Path(p).suffix
            self._attach_bytes[asset_id] = data
            self._attachments.append((asset_id, name))
        self._refresh_attach_list()

    def _remove_attachment(self, asset_id: str) -> None:
        self._attachments = [
            attachment for attachment in self._attachments if attachment[0] != asset_id
        ]
        self._attach_bytes.pop(asset_id, None)
        self._refresh_attach_list()

    def _refresh_attach_list(self) -> None:
        if self._attach_cards_layout is None:
            return
        while self._attach_cards_layout.count():
            item = self._attach_cards_layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        for asset_id, filename in self._attachments:
            self._attach_cards_layout.addWidget(self._attachment_card(asset_id, filename))

        count = len(self._attachments)
        if self._attach_header is not None:
            self._attach_header.setText(
                f"Прикреплённые файлы · {count} / {_MAX_ATTACHMENTS}"
            )
        if self._attach_empty is not None:
            self._attach_empty.setVisible(count == 0)
        if self._attach_button is not None:
            self._attach_button.setEnabled(count < _MAX_ATTACHMENTS)

    def _attachment_card(self, asset_id: str, filename: str) -> QFrame:
        card = QFrame(self.form_area)
        card.setObjectName("attachmentCard")
        card_layout = QHBoxLayout(card)

        type_badge = QLabel(file_type_label(filename), card)
        type_badge.setObjectName("attachmentTypeBadge")
        card_layout.addWidget(type_badge)

        text_column = QWidget(card)
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(filename, text_column)
        name_label.setObjectName("attachmentName")
        name_label.setWordWrap(True)
        text_layout.addWidget(name_label)
        meta_label = QLabel(
            file_size_label(len(self._attach_bytes.get(asset_id, b""))),
            text_column,
        )
        meta_label.setObjectName("attachmentMeta")
        text_layout.addWidget(meta_label)
        card_layout.addWidget(text_column, 1)

        remove_button = QPushButton("Удалить", card)
        remove_button.setObjectName("attachmentRemoveButton")
        remove_button.clicked.connect(
            lambda _checked=False, aid=asset_id: self._remove_attachment(aid)
        )
        card_layout.addWidget(remove_button)
        return card

    def _rebuild_form(self) -> None:
        """Перестроить form_area при смене выбора в combo; снять подсветку ошибки."""
        self._status_label.clear()
        self.options_combo.setProperty("invalid", False)
        self.options_combo.style().unpolish(self.options_combo)
        self.options_combo.style().polish(self.options_combo)
        while self._form_layout.count():
            item = self._form_layout.takeAt(0)
            if item is not None:
                wid = item.widget()
                if wid is not None:
                    wid.deleteLater()
        self._field_widgets.clear()
        self._attachments = []
        self._attach_bytes = {}
        self._attach_cards_layout = None
        self._attach_header = None
        self._attach_empty = None
        self._attach_button = None

        option = self.selected_option()
        if option is None:
            return

        if option.template is None:
            no_fields = QLabel("Для этого документа нет полей для заполнения")
            no_fields.setEnabled(False)
            self._form_layout.addWidget(no_fields)
            return

        if option.template.fill_mode == FillMode.ATTACHMENT:
            attach_btn = QPushButton("Прикрепить файлы")
            attach_btn.setObjectName("attachButton")
            self._attach_button = attach_btn
            self._form_layout.addWidget(attach_btn)

            attach_panel = QFrame()
            attach_panel.setObjectName("attachmentListPanel")
            attach_panel_layout = QVBoxLayout(attach_panel)
            attach_header = QLabel()
            attach_header.setObjectName("attachmentSectionTitle")
            self._attach_header = attach_header
            attach_panel_layout.addWidget(attach_header)

            attach_empty = QLabel("Файлы ещё не прикреплены")
            attach_empty.setObjectName("attachmentEmpty")
            self._attach_empty = attach_empty
            attach_panel_layout.addWidget(attach_empty)

            attach_cards_layout = QVBoxLayout()
            self._attach_cards_layout = attach_cards_layout
            attach_panel_layout.addLayout(attach_cards_layout)
            self._form_layout.addWidget(attach_panel)

            attach_btn.clicked.connect(self._pick_files)
            self._refresh_attach_list()
        else:
            for field in option.template.fields:
                fw = DocumentFieldWidget(field, self.form_area)
                self._form_layout.addWidget(fw)
                self._field_widgets.append(fw)

    def on_submit(self) -> None:
        """Сохранить результат; мягкая подсказка если не выбрано (ADR-005/ADR-008)."""
        option = self.selected_option()
        if option is None:
            self.options_combo.setProperty("invalid", True)
            self.options_combo.style().unpolish(self.options_combo)
            self.options_combo.style().polish(self.options_combo)
            self._status_label.setText("Выберите документ перед сохранением")
        else:
            self._status_label.setText("Ответ сохранён")
        option_id = option.id if option is not None else None
        option_correct = option is not None and option.is_correct
        pairs: list[tuple[str, bool]]
        if option is not None and option.template is not None:
            pairs = [(fw.field.id, fw.check()) for fw in self._field_widgets]
        else:
            pairs = []
        self._result = DocumentResult(
            option_id=option_id,
            option_correct=option_correct,
            fields_ok=tuple(pairs),
        )
