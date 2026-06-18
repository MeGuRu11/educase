"""Типизированные виды этапов: индивидуальная сборка + сбор сырого ответа (ADR-004/008).

Каждый этап — свой ``StageView``-подкласс: строит тот же прокручиваемый контент, что и
раньше, но СОХРАНЯЕТ пары «конфиг-элемент → виджет», чтобы собрать слот ответа ``Attempt``.
``to_response`` копит СЫРЫЕ данные курсанта (queries/выбранные id/тексты) без сверки — оценка
живёт в ``domain.report`` (ADR-008). Read-only элементы (карточки пациентов, таймлайны,
изображения схем/фото) в ответ не входят. Байты ассетов (``assets``) приходят сверху и идут
ТОЛЬКО в рендер изображений.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import assert_never

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from educase_core.domain.attempt import (
    AttemptClinical,
    AttemptContacts,
    AttemptEnvironment,
    AttemptFinal,
    AttemptPatients,
    AttemptSes,
    AttemptStage,
    BranchResponse,
    ChoiceResponse,
    DocumentResponse,
    InspectionResponse,
    SearchLog,
)
from educase_core.domain.documents import DocumentField, DocumentTask
from educase_core.domain.stages import (
    BranchPoint,
    Stage,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StagePatients,
    StageSes,
)
from educase_player.ui.asset_image_widget import AssetImageWidget
from educase_player.ui.branch_widget import BranchWidget
from educase_player.ui.document_field_widget import DocumentFieldWidget
from educase_player.ui.document_widget import DocumentWidget
from educase_player.ui.flow_layout import FlowLayout
from educase_player.ui.inspection_widget import InspectionWidget
from educase_player.ui.patient_card_widget import PatientCardWidget
from educase_player.ui.scheme_viewer import SchemeViewerWidget
from educase_player.ui.search_widget import SearchWidget
from educase_player.ui.timeline_widget import TimelineWidget


class StageView(QWidget):
    """Базовый прокручиваемый вид этапа: общий каркас + сбор сырого ответа.

    Каркас (прокрутка, заголовок, intro) строится здесь; содержимое — в подклассе,
    который добавляет виджеты в ``self._layout`` и сохраняет ссылки для ``to_response``.
    Навигация не блокируется ответами (ADR-005/008).
    """

    def __init__(
        self,
        stage: Stage,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._assets: Mapping[str, bytes] = assets if assets is not None else {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)

        inner = QWidget()
        inner_row = QHBoxLayout(inner)
        inner_row.setContentsMargins(0, 0, 0, 0)

        content = QWidget()
        content.setMaximumWidth(960)
        inner_row.addStretch(1)
        inner_row.addWidget(content)
        inner_row.addStretch(1)

        self._content = content
        self._inner_row = inner_row
        self._layout = QVBoxLayout(content)
        scroll.setWidget(inner)

        title_label = QLabel(stage.title)
        title_label.setObjectName("stageTitle")
        self._layout.addWidget(title_label)

        if stage.intro:
            intro_label = QLabel(stage.intro)
            intro_label.setObjectName("stageIntro")
            intro_label.setWordWrap(True)
            self._layout.addWidget(intro_label)

    def _stretch_content(self) -> None:
        """Растянуть колонку контента до maxWidth (центрированно) — для этапов с широкой сеткой."""
        self._content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        idx = self._inner_row.indexOf(self._content)
        if idx != -1:
            self._inner_row.setStretch(idx, 1)

    def _finish(self, has_content: bool) -> None:
        """Дозаполнить каркас: заглушка пустого этапа + растяжка снизу."""
        if not has_content:
            empty = QLabel("Нет заданий на этом этапе")
            empty.setObjectName("mutedHint")
            self._layout.addWidget(empty)
        self._layout.addStretch()

    def to_response(self) -> AttemptStage:
        """Собрать слот ответа этапа из накопленных виджетов (сырые данные, ADR-008)."""
        raise NotImplementedError


class PatientsStageView(StageView):
    """Этап 1 «Пациенты»: контекстный поиск + read-only карточки пациентов."""

    def __init__(
        self,
        stage: StagePatients,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(stage, assets, parent)
        self._search: SearchWidget | None = None

        has_content = False
        if stage.search is not None and stage.search.entries:
            self._search = SearchWidget(stage.search)
            self._layout.addWidget(self._search)
            has_content = True
        if stage.patients:
            flow_container = QWidget()
            flow_container.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
            )
            flow = FlowLayout(flow_container, h_spacing=12, v_spacing=12)
            for card in stage.patients:
                card_widget = PatientCardWidget(card)
                card_widget.setMaximumWidth(340)
                flow.addWidget(card_widget)
            self._layout.addWidget(flow_container)
            has_content = True
            self._stretch_content()
        self._finish(has_content)

    def to_response(self) -> AttemptPatients:
        return AttemptPatients(search=_search_log(self._search))


class ClinicalStageView(StageView):
    """Этап 2 «Клинико-эпидемиологический диагноз»: поиск, ветвление, документы."""

    def __init__(
        self,
        stage: StageClinical,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(stage, assets, parent)
        self._search: SearchWidget | None = None
        self._branch: tuple[BranchPoint, BranchWidget] | None = None
        self._docs: list[tuple[DocumentTask, DocumentWidget]] = []

        has_content = False
        if stage.search is not None and stage.search.entries:
            self._search = SearchWidget(stage.search)
            self._layout.addWidget(self._search)
            has_content = True
        if stage.branch is not None:
            branch_widget = BranchWidget(stage.branch)
            self._branch = (stage.branch, branch_widget)
            self._layout.addWidget(branch_widget)
            has_content = True
        for task in stage.documents:
            doc_widget = DocumentWidget(task)
            self._docs.append((task, doc_widget))
            self._layout.addWidget(doc_widget)
            has_content = True
        self._finish(has_content)

    def to_response(self) -> AttemptClinical:
        return AttemptClinical(
            search=_search_log(self._search),
            branch=_branch_resp(self._branch),
            documents=tuple(_doc_resp(task, widget) for task, widget in self._docs),
        )


class ContactsStageView(StageView):
    """Этап 3 «Обследование контактных лиц»: изображение схемы + свободный осмотр."""

    def __init__(
        self,
        stage: StageContacts,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(stage, assets, parent)
        self._inspection: InspectionWidget | None = None

        has_content = False
        if stage.scheme is not None:
            self._layout.addWidget(SchemeViewerWidget(stage.scheme, self._assets))
            has_content = True
        if stage.inspection is not None:
            self._inspection = InspectionWidget(stage.inspection)
            self._layout.addWidget(self._inspection)
            has_content = True
        self._finish(has_content)

    def to_response(self) -> AttemptContacts:
        return AttemptContacts(inspection=_insp_resp(self._inspection))


class EnvironmentStageView(StageView):
    """Этап 4 «Объекты внешней среды»: изображения схемы/фото, документы, осмотр."""

    def __init__(
        self,
        stage: StageEnvironment,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(stage, assets, parent)
        self._docs: list[tuple[DocumentTask, DocumentWidget]] = []
        self._inspection: InspectionWidget | None = None

        has_content = False
        if stage.scheme is not None:
            self._layout.addWidget(SchemeViewerWidget(stage.scheme, self._assets))
            has_content = True
        for photo_id in stage.photos:
            self._layout.addWidget(
                AssetImageWidget(photo_id, self._assets, caption="Фото")
            )
            has_content = True
        for task in stage.documents:
            doc_widget = DocumentWidget(task)
            self._docs.append((task, doc_widget))
            self._layout.addWidget(doc_widget)
            has_content = True
        if stage.inspection is not None:
            self._inspection = InspectionWidget(stage.inspection)
            self._layout.addWidget(self._inspection)
            has_content = True
        self._finish(has_content)

    def to_response(self) -> AttemptEnvironment:
        return AttemptEnvironment(
            documents=tuple(_doc_resp(task, widget) for task, widget in self._docs),
            inspection=_insp_resp(self._inspection),
        )


class SesStageView(StageView):
    """Этап 5 «Оценка СЭС»: поиск, выбор уровня СЭС, документы."""

    def __init__(
        self,
        stage: StageSes,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(stage, assets, parent)
        self._search: SearchWidget | None = None
        self._level: tuple[DocumentField, DocumentFieldWidget] | None = None
        self._docs: list[tuple[DocumentTask, DocumentWidget]] = []

        has_content = False
        if stage.search is not None and stage.search.entries:
            self._search = SearchWidget(stage.search)
            self._layout.addWidget(self._search)
            has_content = True
        if stage.level_choice is not None:
            level_widget = DocumentFieldWidget(stage.level_choice)
            self._level = (stage.level_choice, level_widget)
            self._layout.addWidget(level_widget)
            has_content = True
        for task in stage.documents:
            doc_widget = DocumentWidget(task)
            self._docs.append((task, doc_widget))
            self._layout.addWidget(doc_widget)
            has_content = True
        self._finish(has_content)

    def to_response(self) -> AttemptSes:
        return AttemptSes(
            search=_search_log(self._search),
            level_choice=_choice_resp(self._level),
            documents=tuple(_doc_resp(task, widget) for task, widget in self._docs),
        )


class FinalStageView(StageView):
    """Этап 6 «Окончательный диагноз»: поиск, документы, read-only таймлайны."""

    def __init__(
        self,
        stage: StageFinal,
        assets: Mapping[str, bytes] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(stage, assets, parent)
        self._search: SearchWidget | None = None
        self._docs: list[tuple[DocumentTask, DocumentWidget]] = []

        has_content = False
        if stage.search is not None and stage.search.entries:
            self._search = SearchWidget(stage.search)
            self._layout.addWidget(self._search)
            has_content = True
        for task in stage.documents:
            doc_widget = DocumentWidget(task)
            self._docs.append((task, doc_widget))
            self._layout.addWidget(doc_widget)
            has_content = True
        for tl in stage.timelines:
            self._layout.addWidget(TimelineWidget(tl))
            has_content = True
        self._finish(has_content)

    def to_response(self) -> AttemptFinal:
        return AttemptFinal(
            search=_search_log(self._search),
            documents=tuple(_doc_resp(task, widget) for task, widget in self._docs),
        )


# --- Приватные хелперы сборки ответа (id берём из конфиг-элемента, не из виджета) ---


def _search_log(widget: SearchWidget | None) -> SearchLog:
    """Журнал поиска из накопленных запросов виджета; пустой если поиска не было."""
    return SearchLog(queries=widget.queries()) if widget is not None else SearchLog()


def _branch_resp(pair: tuple[BranchPoint, BranchWidget] | None) -> BranchResponse | None:
    """Ответ ветвления: id точки из конфига + id выбранной опции («» если не выбрана)."""
    if pair is None:
        return None
    branch, widget = pair
    option = widget.selected_option()
    return BranchResponse(
        point_id=branch.id,
        chosen_option_id=option.id if option is not None else "",
    )


def _doc_resp(task: DocumentTask, widget: DocumentWidget) -> DocumentResponse:
    """Ответ задания-документа: id задания + выбранная опция + сырые пары «поле → ответ»."""
    option = widget.selected_option()
    return DocumentResponse(
        task_id=task.id,
        chosen_option_id=option.id if option is not None else "",
        field_answers=tuple(
            (fw.field.id, fw.answer()) for fw in widget.current_field_widgets()
        ),
    )


def _insp_resp(widget: InspectionWidget | None) -> InspectionResponse | None:
    """Ответ осмотра: сырой текст вывода; None если осмотра на этапе нет."""
    if widget is None:
        return None
    return InspectionResponse(text=widget.text())


def _choice_resp(
    pair: tuple[DocumentField, DocumentFieldWidget] | None,
) -> ChoiceResponse | None:
    """Сырой ответ-выбор (уровень СЭС); None если выбора на этапе нет."""
    if pair is None:
        return None
    _, widget = pair
    return ChoiceResponse(answer=widget.answer())


def build_stage_view(
    stage: Stage, assets: Mapping[str, bytes] | None = None
) -> StageView:
    """Создать типизированный вид по типу этапа (шесть фиксированных, ADR-004).

    ``assets`` (байты ассетов архива) пробрасываются в вид для рендера изображений схем/фото.
    """
    if isinstance(stage, StagePatients):
        return PatientsStageView(stage, assets)
    if isinstance(stage, StageClinical):
        return ClinicalStageView(stage, assets)
    if isinstance(stage, StageContacts):
        return ContactsStageView(stage, assets)
    if isinstance(stage, StageEnvironment):
        return EnvironmentStageView(stage, assets)
    if isinstance(stage, StageSes):
        return SesStageView(stage, assets)
    if isinstance(stage, StageFinal):
        return FinalStageView(stage, assets)
    assert_never(stage)
