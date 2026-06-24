"""Движок сверки прохождения с кейсом: чистая функция ``grade_case`` (ADR-008).

Поэлементное «верно/неверно» без весов, баллов и политики pass/fail — нейтральная
структура, поверх которой кафедральная модель оценивания (К2/К3) подключится позже.
Это слой, где вскрываются ошибки «Варианта B»: неверный выбор не блокирует прохождение
(ADR-005), а всплывает здесь как ``Finding`` с ``correct=False``.

Сопоставление НЕ реализуется заново — переиспользуются готовые методы домена:
``DocumentField.check``, ``DocumentOption.is_correct``, ``BranchOption.is_correct``,
``InspectionCheck.covered``. Отсутствующий/неотвеченный элемент даёт ``correct=False``,
никогда не исключение: грейдинг не падает на дефолтном ``Attempt``.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from epicase_core.domain._serde import (
    as_map,
    opt_bool,
    opt_str,
    req_str,
    seq,
)
from epicase_core.domain.attempt import (
    Attempt,
    AttemptClinical,
    AttemptContacts,
    AttemptEnvironment,
    AttemptFinal,
    AttemptPatients,
    AttemptSes,
    BranchResponse,
    ChoiceResponse,
    DocumentResponse,
    InspectionResponse,
)
from epicase_core.domain.case import Case
from epicase_core.domain.documents import DocumentField, DocumentTask
from epicase_core.domain.search import InspectionCheck
from epicase_core.domain.stages import (
    BranchPoint,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StageKind,
    StagePatients,
    StageSes,
)


class FindingKind(StrEnum):
    """Тип проверяемого элемента в отчёте сверки."""

    BRANCH = "branch"
    DOCUMENT_CHOICE = "document_choice"
    DOCUMENT_FIELD = "document_field"
    INSPECTION = "inspection"
    LEVEL_CHOICE = "level_choice"


@dataclass(frozen=True)
class Finding:
    """Результат сверки одного элемента: только сырой флаг ``correct`` и его id.

    ``element_id`` — id ветвления / задания / поля и т. п.; ``label`` — человекочитаемая
    подпись для отчёта; ``detail`` — нейтральный контекст (ответ курсанта / выбранная
    опция) БЕЗ вердикта. Весов и баллов здесь нет (ADR-008).
    """

    kind: FindingKind
    element_id: str
    correct: bool
    label: str = ""
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "element_id": self.element_id,
            "correct": self.correct,
            "label": self.label,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Finding:
        return cls(
            kind=FindingKind(req_str(data, "kind")),
            element_id=req_str(data, "element_id"),
            correct=opt_bool(data, "correct"),
            label=opt_str(data, "label"),
            detail=opt_str(data, "detail"),
        )


@dataclass(frozen=True)
class StageReport:
    """Сверка одного этапа: его ``kind`` и список найденных элементов."""

    kind: StageKind
    findings: tuple[Finding, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "findings": [f.to_dict() for f in self.findings],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StageReport:
        return cls(
            kind=StageKind(req_str(data, "kind")),
            findings=tuple(
                Finding.from_dict(as_map(item)) for item in seq(data, "findings")
            ),
        )


@dataclass(frozen=True)
class CaseReport:
    """Отчёт сверки кейса целиком: id кейса + шесть отчётов этапов в порядке ``Case.ordered``."""

    case_id: str
    stages: tuple[StageReport, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "stages": [s.to_dict() for s in self.stages],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CaseReport:
        return cls(
            case_id=req_str(data, "case_id"),
            stages=tuple(
                StageReport.from_dict(as_map(item)) for item in seq(data, "stages")
            ),
        )


def grade_case(case: Case, attempt: Attempt) -> CaseReport:
    """Сверить прохождение с кейсом поэлементно (чистая функция, без I/O и побочных эффектов).

    Этапы — в фиксированном порядке ``Case.ordered`` (ADR-004). Каждый грейдер переиспользует
    готовые методы сверки домена и никогда не падает на отсутствующих ответах (ADR-008).
    """
    return CaseReport(
        case_id=case.meta.id,
        stages=(
            _grade_patients(case.patients, attempt.patients),
            _grade_clinical(case.clinical, attempt.clinical),
            _grade_contacts(case.contacts, attempt.contacts),
            _grade_environment(case.environment, attempt.environment),
            _grade_ses(case.ses, attempt.ses),
            _grade_final(case.final, attempt.final),
        ),
    )


# --- Грейдеры этапов (порядок findings — как в конфигурации этапа) ---


def _grade_patients(stage: StagePatients, att: AttemptPatients) -> StageReport:
    """Этап 1 «Пациенты»: оценивать нечего (поиск опционален, ADR-006)."""
    return StageReport(StageKind.PATIENTS, ())


def _grade_clinical(stage: StageClinical, att: AttemptClinical) -> StageReport:
    """Этап 2 «Клинический диагноз»: ветвление «Вариант B» + документы."""
    return StageReport(
        StageKind.CLINICAL,
        _grade_branch(stage.branch, att.branch)
        + _grade_documents(stage.documents, att.documents),
    )


def _grade_contacts(stage: StageContacts, att: AttemptContacts) -> StageReport:
    """Этап 3 «Контактные лица»: покрытие осмотра."""
    return StageReport(
        StageKind.CONTACTS,
        _grade_inspection(stage.inspection, att.inspection),
    )


def _grade_environment(stage: StageEnvironment, att: AttemptEnvironment) -> StageReport:
    """Этап 4 «Объекты внешней среды»: документы + покрытие осмотра."""
    return StageReport(
        StageKind.ENVIRONMENT,
        _grade_documents(stage.documents, att.documents)
        + _grade_inspection(stage.inspection, att.inspection),
    )


def _grade_ses(stage: StageSes, att: AttemptSes) -> StageReport:
    """Этап 5 «Оценка СЭС»: выбор уровня + документы."""
    return StageReport(
        StageKind.SES,
        _grade_level(stage.level_choice, att.level_choice)
        + _grade_documents(stage.documents, att.documents),
    )


def _grade_final(stage: StageFinal, att: AttemptFinal) -> StageReport:
    """Этап 6 «Окончательный диагноз»: документы."""
    return StageReport(
        StageKind.FINAL,
        _grade_documents(stage.documents, att.documents),
    )


# --- Общие хелперы сверки (опциональный элемент → пустой кортеж findings) ---


def _grade_branch(
    branch: BranchPoint | None, resp: BranchResponse | None
) -> tuple[Finding, ...]:
    """Сверить выбор в точке ветвления (вскрытие «Варианта B», ADR-005).

    Ветвления нет в кейсе → findings не создаём. Иначе ищем выбранную опцию по
    ``resp.chosen_option_id`` (``resp`` может быть ``None``): ``correct`` — опция найдена и
    помечена верной; ``detail`` — её подпись (или ``""``, если выбор не сопоставился).
    """
    if branch is None:
        return ()
    chosen_id = resp.chosen_option_id if resp is not None else ""
    chosen = next((opt for opt in branch.options if opt.id == chosen_id), None)
    return (
        Finding(
            kind=FindingKind.BRANCH,
            element_id=branch.id,
            correct=chosen is not None and chosen.is_correct,
            label=branch.prompt,
            detail=chosen.label if chosen is not None else "",
        ),
    )


def _grade_documents(
    tasks: tuple[DocumentTask, ...], resps: tuple[DocumentResponse, ...]
) -> tuple[Finding, ...]:
    """Сверить задания-документы: выбор документа + поля верного шаблона.

    На каждое задание — одна ``DOCUMENT_CHOICE`` (верна ли выбранная опция) и по одной
    ``DOCUMENT_FIELD`` на каждое поле ВЕРНОГО документа (если у него есть шаблон).
    """
    by_id = {resp.task_id: resp for resp in resps}
    findings: list[Finding] = []
    for task in tasks:
        resp = by_id.get(task.id)
        chosen_id = resp.chosen_option_id if resp is not None else ""
        chosen = next((opt for opt in task.options if opt.id == chosen_id), None)
        findings.append(
            Finding(
                kind=FindingKind.DOCUMENT_CHOICE,
                element_id=task.id,
                correct=chosen is not None and chosen.is_correct,
                label=task.prompt,
                detail=chosen.title if chosen is not None else "",
            )
        )
        findings.extend(_grade_document_fields(task, resp))
    return tuple(findings)


def _grade_document_fields(
    task: DocumentTask, resp: DocumentResponse | None
) -> tuple[Finding, ...]:
    """Сверить поля ВЕРНОГО документа задания по его шаблону (если такой есть).

    Поля оцениваются по эталонному шаблону независимо от выбора курсанта; ответы берутся
    из ``resp.field_answers`` по ``field.id`` (отсутствующий ответ → ``""`` → ``correct=False``
    для обязательного поля). Верной опции с шаблоном нет → поля пропускаем.
    """
    template = next(
        (opt.template for opt in task.options if opt.is_correct and opt.template is not None),
        None,
    )
    if template is None:
        return ()
    answers = dict(resp.field_answers) if resp is not None else {}
    return tuple(
        Finding(
            kind=FindingKind.DOCUMENT_FIELD,
            element_id=doc_field.id,
            correct=doc_field.check(answers.get(doc_field.id, "")),
            label=doc_field.label,
            detail=answers.get(doc_field.id, ""),
        )
        for doc_field in template.fields
    )


def _grade_inspection(
    check: InspectionCheck | None, resp: InspectionResponse | None
) -> tuple[Finding, ...]:
    """Сверить покрытие осмотра: по одной ``Finding`` на каждую ожидаемую группу.

    Осмотра нет в кейсе → findings не создаём. Иначе ``InspectionCheck.covered`` возвращает
    флаги покрытия в порядке ``check.expected``; подпись группы — её канонический термин.
    """
    if check is None:
        return ()
    text = resp.text if resp is not None else ""
    covered = check.covered(text)
    return tuple(
        Finding(
            kind=FindingKind.INSPECTION,
            element_id=f"insp-{index}",
            correct=covered[index],
            label=group.canonical,
        )
        for index, group in enumerate(check.expected)
    )


def _grade_level(
    field: DocumentField | None, resp: ChoiceResponse | None
) -> tuple[Finding, ...]:
    """Сверить выбор уровня СЭС по правилу поля (``DocumentField.check``).

    Выбора уровня нет в кейсе → findings не создаём. Иначе ответ берётся из ``resp.answer``
    (``resp`` может быть ``None`` → ``""``).
    """
    if field is None:
        return ()
    ans = resp.answer if resp is not None else ""
    return (
        Finding(
            kind=FindingKind.LEVEL_CHOICE,
            element_id=field.id,
            correct=field.check(ans),
            label=field.label,
            detail=ans,
        ),
    )
