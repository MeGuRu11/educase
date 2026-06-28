"""Модальный диалог предварительной машинной проверки результата (Constructor).

Прокручиваемый ``ReportView`` + кнопка «Закрыть». Read-only: отчёт только показывается,
ничего не редактируется и не сохраняется; итоговое решение остаётся за преподавателем.
Только виджеты и layout-менеджеры, без inline-стиля.
"""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from epicase_constructor.ui.report_view import ReportView
from epicase_core.domain.report import CaseReport


class ReportDialog(QDialog):
    """Диалог результата прохождения: ``ReportView`` в прокрутке + кнопка «Закрыть».

    Открывается развёрнутым на весь экран (детальный отчёт длинный); ``assets`` — байты
    архива результата, нужные ``ReportView`` для открытия/сохранения вложений курсанта.
    """

    def __init__(
        self,
        report: CaseReport,
        trainee_label: str = "",
        rank: str = "",
        study_group: str = "",
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Результат — {trainee_label or '(без подписи)'}")
        self._assets: Mapping[str, bytes] = assets or {}
        # Restored-размер для возврата из maximized; стартуем развёрнутыми на весь экран.
        self.resize(1200, 800)
        self.setWindowState(Qt.WindowState.WindowMaximized)

        identity_parts = [trainee_label or "(без подписи)"]
        if rank:
            identity_parts.append(rank)
        if study_group:
            identity_parts.append(f"группа {study_group}")
        self.identity_label = QLabel("Курсант: " + ", ".join(identity_parts), self)
        self.identity_label.setObjectName("schemeRevealTitle")
        self.identity_label.setWordWrap(True)

        self.report_view = ReportView(report, self._assets, self)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.report_view)

        self.close_button = QPushButton("Закрыть", self)
        self.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.identity_label)
        layout.addWidget(scroll)
        layout.addWidget(self.close_button)
