"""Виджет задания выбора документа с обманками и заполнением полей (ADR-007/ADR-008)."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.documents import DocumentOption, DocumentTask, FillMode
from educase_player.ui.asset_image_widget import AssetImageWidget
from educase_player.ui.document_field_widget import DocumentFieldWidget


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
    Вердикт курсанту не показывается — только в финальном отчёте (ADR-005).
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
        self._free_text_edit: QPlainTextEdit | None = None

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

    def free_text(self) -> str:
        """Текст в режиме свободного заполнения; "" если режим полевой/не выбран."""
        return self._free_text_edit.toPlainText() if self._free_text_edit is not None else ""

    def _rebuild_form(self) -> None:
        """Перестроить form_area при смене выбора в combo; снять подсветку ошибки."""
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
        self._free_text_edit = None

        option = self.selected_option()
        if option is None:
            return

        if option.template is None:
            no_fields = QLabel("Для этого документа нет полей для заполнения")
            no_fields.setEnabled(False)
            self._form_layout.addWidget(no_fields)
            return

        if option.template.fill_mode == FillMode.FREE_TEXT:
            te = QPlainTextEdit()
            te.setPlaceholderText("Введите текст документа")
            self._free_text_edit = te
            self._form_layout.addWidget(te)
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
