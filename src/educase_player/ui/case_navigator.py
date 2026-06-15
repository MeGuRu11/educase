"""Виджет навигации по шести фиксированным этапам кейса."""
from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.attempt import (
    Attempt,
    AttemptClinical,
    AttemptContacts,
    AttemptEnvironment,
    AttemptFinal,
    AttemptMeta,
    AttemptPatients,
    AttemptSes,
)
from educase_core.domain.case import Case
from educase_player.ui.stage_views import (
    ClinicalStageView,
    ContactsStageView,
    EnvironmentStageView,
    FinalStageView,
    PatientsStageView,
    SesStageView,
    StageView,
    build_stage_view,
)


class CaseNavigator(QWidget):
    """Навигатор по этапам: стек страниц + строка позиции + кнопки Назад/Далее.

    Навигация не блокируется ответами курсанта (ADR-005/008): свободный переход
    вперёд/назад по всем шести этапам независимо от введённых данных.
    """

    def __init__(
        self,
        case: Case,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._assets: Mapping[str, bytes] = assets if assets is not None else {}
        stages = case.ordered()

        layout = QVBoxLayout(self)

        self._position_label = QLabel()
        self._position_label.setObjectName("stagePosition")
        layout.addWidget(self._position_label)

        self.stack = QStackedWidget()
        views = tuple(build_stage_view(stage, self._assets) for stage in stages)
        self._views: tuple[StageView, ...] = views
        for view in views:
            self.stack.addWidget(view)
        layout.addWidget(self.stack, 1)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("Назад")
        self.btn_next = QPushButton("Далее")
        nav_layout.addWidget(self.btn_prev)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_next)
        layout.addLayout(nav_layout)

        self.btn_prev.clicked.connect(self._go_prev)
        self.btn_next.clicked.connect(self._go_next)

        self._refresh()

    @property
    def current_index(self) -> int:
        """Текущий индекс активного этапа (0-based)."""
        return self.stack.currentIndex()

    def collect_attempt(self, meta: AttemptMeta) -> Attempt:
        """Собрать прохождение из накопленных видов этапов (сырые ответы, ADR-008).

        Каждый вид даёт свой слот ответа; ``meta`` (с ``case_id``) приходит снаружи.
        Слоты отсутствующих видов заполняются дефолтными пустыми ответами.
        """
        patients: AttemptPatients | None = None
        clinical: AttemptClinical | None = None
        contacts: AttemptContacts | None = None
        environment: AttemptEnvironment | None = None
        ses: AttemptSes | None = None
        final: AttemptFinal | None = None

        for view in self._views:
            if isinstance(view, PatientsStageView):
                patients = view.to_response()
            elif isinstance(view, ClinicalStageView):
                clinical = view.to_response()
            elif isinstance(view, ContactsStageView):
                contacts = view.to_response()
            elif isinstance(view, EnvironmentStageView):
                environment = view.to_response()
            elif isinstance(view, SesStageView):
                ses = view.to_response()
            elif isinstance(view, FinalStageView):
                final = view.to_response()

        return Attempt(
            meta=meta,
            patients=patients or AttemptPatients(),
            clinical=clinical or AttemptClinical(),
            contacts=contacts or AttemptContacts(),
            environment=environment or AttemptEnvironment(),
            ses=ses or AttemptSes(),
            final=final or AttemptFinal(),
        )

    def _refresh(self) -> None:
        idx = self.stack.currentIndex()
        count = self.stack.count()
        self._position_label.setText(f"Этап {idx + 1} из {count}")
        self.btn_prev.setEnabled(idx > 0)
        self.btn_next.setEnabled(idx < count - 1)

    def _go_prev(self) -> None:
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._refresh()

    def _go_next(self) -> None:
        idx = self.stack.currentIndex()
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
            self._refresh()
