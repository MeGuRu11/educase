"""Read-only просмотр предварительной машинной проверки результата (Constructor).

Секции по этапам в порядке отчёта; в каждой — приглушённый нейтральный контекст (что
курсант искал/писал), строки по ``Finding`` (верно, неверно, не отвечено) и блок
вложенных документов курсанта с возможностью открыть/сохранить.
На этапе 6 дополнительно показываются ``TimelineComparison`` — эталон кейса рядом с вводом
курсанта, БЕЗ пометок верно/неверно. БЕЗ итогов, баллов, процентов и вердикта pass/fail —
окончательное решение принимает преподаватель (ADR-016). Только виджеты и
layout-менеджеры, без inline-стиля (статусы — через objectName + QSS).
"""
from __future__ import annotations

import tempfile
from collections.abc import Mapping
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from epicase_core.domain.report import (
    CaseReport,
    Finding,
    StageReport,
    TimelineComparison,
)
from epicase_core.domain.stages import StageKind
from epicase_core.theme.file_labels import file_size_label, file_type_label

_STAGE_TITLES: dict[StageKind, str] = {
    StageKind.PATIENTS: "Пациенты",
    StageKind.CLINICAL: "Клинико-эпидемиологический диагноз",
    StageKind.CONTACTS: "Обследование контактных лиц",
    StageKind.ENVIRONMENT: "Обследование объектов внешней среды",
    StageKind.SES: "Оценка СЭС",
    StageKind.FINAL: "Окончательный эпидемиологический диагноз",
}

_TIMELINES_HEADER = "Эпидемиологические таймлайны"
_AUTHORED_CAPTION = "Эталон"
_CADET_CAPTION = "Введено курсантом"
_EMPTY_COLUMN = "не заполнено"
_ATTACHMENTS_HEADER = "Вложенные документы"
_MISSING_ASSET = "(файл отсутствует в архиве)"


class ReportView(QWidget):
    """Просмотр отчёта: по секции (``QGroupBox``) на этап, по строке на проверяемый элемент.

    ``assets`` — байты архива результата (имя ассета → байты); нужны, чтобы открыть вложение
    курсанта во внешней программе или сохранить его на диск.
    """

    def __init__(
        self,
        report: CaseReport,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._assets: Mapping[str, bytes] = assets or {}

        layout = QVBoxLayout(self)
        for stage in report.stages:
            layout.addWidget(self._stage_box(stage))
        layout.addStretch(1)

    def _stage_box(self, stage: StageReport) -> QGroupBox:
        """Секция этапа: заметки + строки findings + вложения + (для этапа 6) таймлайны."""
        box = QGroupBox(_STAGE_TITLES.get(stage.kind, stage.kind.value))
        box_layout = QVBoxLayout(box)
        if (
            not stage.findings
            and not stage.timelines
            and not stage.notes
            and not stage.attachments
        ):
            box_layout.addWidget(QLabel("— нет проверяемых элементов —"))
            return box
        for label, value in stage.notes:
            note = QLabel(f"{label}: {value}")
            note.setObjectName("mutedHint")
            note.setWordWrap(True)
            box_layout.addWidget(note)
        for finding in stage.findings:
            box_layout.addWidget(self._finding_label(finding))
        if stage.attachments:
            box_layout.addWidget(self._attachments_section(stage.attachments))
        if stage.timelines:
            box_layout.addWidget(self._timelines_section(stage.timelines))
        return box

    @staticmethod
    def _finding_label(finding: Finding) -> QLabel:
        """Строка элемента: текст со статусом + цвет статуса через objectName (QSS)."""
        label = QLabel(ReportView._finding_text(finding))
        if finding.correct:
            name = "findingOk"
        elif finding.answered:
            name = "findingBad"
        else:
            name = "findingSkip"
        label.setObjectName(name)
        label.setWordWrap(True)
        return label

    # --- Вложения курсанта: строка с именем + кнопки «Открыть» / «Сохранить как…» ---

    def _attachments_section(
        self, attachments: tuple[tuple[str, str], ...]
    ) -> QWidget:
        """Блок вложенных документов курсанта: заголовок + строка на каждое вложение."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel(f"{_ATTACHMENTS_HEADER} · {len(attachments)}")
        header.setObjectName("attachmentSectionTitle")
        section_layout.addWidget(header)
        for asset_id, filename in attachments:
            section_layout.addWidget(self._attachment_row(asset_id, filename))
        return section

    def _attachment_row(self, asset_id: str, filename: str) -> QFrame:
        """Карточка вложения; при отсутствии байтов действия отключены."""
        data = self._assets.get(asset_id)
        present = data is not None
        row = QFrame()
        row.setObjectName("attachmentCard")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)

        type_badge = QLabel(file_type_label(filename), row)
        type_badge.setObjectName("attachmentTypeBadge")
        row_layout.addWidget(type_badge)

        text_column = QWidget(row)
        text_layout = QVBoxLayout(text_column)
        text_layout.setContentsMargins(0, 0, 0, 0)
        name_label = QLabel(filename, text_column)
        name_label.setObjectName("attachmentName")
        name_label.setWordWrap(True)
        text_layout.addWidget(name_label)
        if data is not None:
            meta_label = QLabel(file_size_label(len(data)), text_column)
            meta_label.setObjectName("attachmentMeta")
            text_layout.addWidget(meta_label)
        else:
            warning_label = QLabel(_MISSING_ASSET, text_column)
            warning_label.setObjectName("attachmentWarning")
            text_layout.addWidget(warning_label)
        row_layout.addWidget(text_column, 1)

        open_button = QPushButton("Открыть")
        open_button.setObjectName("attachmentOpenButton")
        open_button.setEnabled(present)
        save_button = QPushButton("Сохранить как…")
        save_button.setObjectName("attachmentSaveButton")
        save_button.setEnabled(present)
        if present:
            open_button.clicked.connect(
                lambda *_, aid=asset_id, name=filename: self._open_attachment(aid, name)
            )
            save_button.clicked.connect(
                lambda *_, aid=asset_id, name=filename: self._save_attachment(aid, name)
            )
        row_layout.addWidget(open_button)
        row_layout.addWidget(save_button)
        return row

    def _open_attachment(self, asset_id: str, filename: str) -> None:
        """Записать вложение во временный файл с исходным именем и открыть внешней программой."""
        data = self._assets.get(asset_id)
        if data is None:
            return
        path = Path(tempfile.mkdtemp(prefix="epicase_att_")) / filename
        path.write_bytes(data)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _save_attachment(self, asset_id: str, filename: str) -> None:
        """Сохранить вложение на диск по выбору преподавателя (имя по умолчанию — исходное)."""
        data = self._assets.get(asset_id)
        if data is None:
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Сохранить вложение", filename)
        if not destination:
            return
        Path(destination).write_bytes(data)

    # --- Таймлайны этапа 6 (нейтральное сопоставление, без вердикта) ---

    def _timelines_section(self, timelines: tuple[TimelineComparison, ...]) -> QWidget:
        """Секция таймлайнов этапа 6: заголовок + карточка на каждое сопоставление."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        header = QLabel(_TIMELINES_HEADER)
        header.setObjectName("schemeTitle")
        section_layout.addWidget(header)
        for comparison in timelines:
            section_layout.addWidget(self._timeline_card(comparison))
        return section

    def _timeline_card(self, comparison: TimelineComparison) -> QGroupBox:
        """Карточка таймлайна: заголовок + две колонки «Эталон» | «Введено курсантом».

        Колонки выводятся построчно «дата — событие», без пометок верно/неверно: это
        нейтральное сопоставление, вердикт остаётся за преподавателем.
        """
        card = QGroupBox(comparison.title or comparison.timeline_id)
        columns = QHBoxLayout(card)
        columns.addLayout(self._timeline_column(_AUTHORED_CAPTION, comparison.authored), 1)
        columns.addLayout(self._timeline_column(_CADET_CAPTION, comparison.cadet), 1)
        return card

    @staticmethod
    def _timeline_column(
        caption: str, entries: tuple[tuple[str, str], ...]
    ) -> QVBoxLayout:
        """Колонка таймлайна: подпись + строки «дата — событие» (или «не заполнено», если пусто)."""
        column = QVBoxLayout()
        title = QLabel(caption)
        title.setObjectName("schemeCaption")
        column.addWidget(title)
        if not entries:
            placeholder = QLabel(_EMPTY_COLUMN)
            placeholder.setObjectName("mutedHint")
            column.addWidget(placeholder)
        else:
            for date, event in entries:
                column.addWidget(QLabel(f"{date} — {event}"))
        column.addStretch(1)
        return column

    @staticmethod
    def _finding_text(finding: Finding) -> str:
        """Строка элемента: статус + подпись (или id) + приглушённый контекст (если есть)."""
        if finding.correct:
            status = "верно"
        elif finding.answered:
            status = "неверно"
        else:
            status = "не отвечено"
        name = finding.label or finding.element_id
        text = f"[{status}] {name}"
        if finding.detail and finding.answered:
            text += f" — {finding.detail}"
        return text
