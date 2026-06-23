"""Модальный диалог нейтрального отчёта сверки результата (Constructor).

Прокручиваемый ``ReportView`` + кнопка «Закрыть». Read-only: отчёт только показывается,
ничего не редактируется и не сохраняется. Только виджеты и layout-менеджеры, без inline-стиля.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from educase_constructor.ui.report_view import ReportView
from educase_core.domain.report import CaseReport


class ReportDialog(QDialog):
    """Диалог результата прохождения: ``ReportView`` в прокрутке + кнопка «Закрыть»."""

    def __init__(
        self,
        report: CaseReport,
        trainee_label: str = "",
        rank: str = "",
        study_group: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Результат — {trainee_label or '(без подписи)'}")
        self.resize(800, 600)

        identity_parts = [trainee_label or "(без подписи)"]
        if rank:
            identity_parts.append(rank)
        if study_group:
            identity_parts.append(f"группа {study_group}")
        self.identity_label = QLabel("Курсант: " + ", ".join(identity_parts), self)
        self.identity_label.setObjectName("schemeRevealTitle")
        self.identity_label.setWordWrap(True)

        self.report_view = ReportView(report, self)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.report_view)

        self.close_button = QPushButton("Закрыть", self)
        self.close_button.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self.identity_label)
        layout.addWidget(scroll)
        layout.addWidget(self.close_button)
