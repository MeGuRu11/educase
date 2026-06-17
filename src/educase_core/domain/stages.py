"""Шесть фиксированных этапов кейса (ADR-004).

Этапы — независимые frozen-dataclass'ы без наследования полей (чтобы не ловить ordering
дефолтов); идентичность этапа задаёт ``ClassVar KIND``. Ветвление «Вариант B» (ADR-005) —
запись выбора на этапе 2, навигацию не меняет. Схему осмотра (этапы 3/4) моделирует
``SchemeDocument`` (фон + хотспоты, ADR-013).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from educase_core.domain._serde import (
    as_map,
    opt_bool,
    opt_str,
    pair_tuple,
    req_str,
    seq,
    str_tuple,
)
from educase_core.domain.documents import DocumentField, DocumentTask
from educase_core.domain.scheme import SchemeDocument, scheme_from_raw
from educase_core.domain.search import InspectionCheck, KeywordSearch


class StageKind(StrEnum):
    """Идентичность одного из шести фиксированных этапов."""

    PATIENTS = "patients"
    CLINICAL = "clinical"
    CONTACTS = "contacts"
    ENVIRONMENT = "environment"
    SES = "ses"
    FINAL = "final"


@dataclass(frozen=True)
class BranchOption:
    """Вариант выбора в точке ветвления (этап 2)."""

    id: str
    label: str = ""
    is_correct: bool = False

    def to_dict(self) -> dict[str, object]:
        return {"id": self.id, "label": self.label, "is_correct": self.is_correct}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> BranchOption:
        return cls(
            id=req_str(data, "id"),
            label=opt_str(data, "label"),
            is_correct=opt_bool(data, "is_correct"),
        )


@dataclass(frozen=True)
class BranchPoint:
    """Точка ветвления «Вариант B»: выбор пути, не меняющий навигацию (ADR-005)."""

    id: str
    prompt: str = ""
    options: tuple[BranchOption, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "options": [opt.to_dict() for opt in self.options],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> BranchPoint:
        return cls(
            id=req_str(data, "id"),
            prompt=opt_str(data, "prompt"),
            options=tuple(
                BranchOption.from_dict(as_map(item)) for item in seq(data, "options")
            ),
        )


@dataclass(frozen=True)
class PatientCard:
    """Карточка пациента: пары «поле → значение» и ссылки на ассеты по id."""

    id: str
    title: str = ""
    fields: tuple[tuple[str, str], ...] = ()
    assets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "fields": [list(pair) for pair in self.fields],
            "assets": list(self.assets),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> PatientCard:
        return cls(
            id=req_str(data, "id"),
            title=opt_str(data, "title"),
            fields=pair_tuple(data, "fields"),
            assets=str_tuple(data, "assets"),
        )


@dataclass(frozen=True)
class Timeline:
    """Таймлайн (сроки наблюдения за очагом): пары «дата → событие»."""

    id: str
    title: str = ""
    events: tuple[tuple[str, str], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "events": [list(pair) for pair in self.events],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Timeline:
        return cls(
            id=req_str(data, "id"),
            title=opt_str(data, "title"),
            events=pair_tuple(data, "events"),
        )


@dataclass(frozen=True)
class StagePatients:
    """Этап 1 «Пациенты»: контекстный поиск + карточки пациентов (могут отсутствовать)."""

    KIND: ClassVar[StageKind] = StageKind.PATIENTS
    title: str = "Пациенты"
    intro: str = ""
    search: KeywordSearch | None = None
    patients: tuple[PatientCard, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "title": self.title,
            "intro": self.intro,
            "search": self.search.to_dict() if self.search is not None else None,
            "patients": [p.to_dict() for p in self.patients],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StagePatients:
        raw_search = data.get("search")
        return cls(
            title=opt_str(data, "title", "Пациенты"),
            intro=opt_str(data, "intro"),
            search=(
                KeywordSearch.from_dict(as_map(raw_search))
                if raw_search is not None
                else None
            ),
            patients=tuple(
                PatientCard.from_dict(as_map(item)) for item in seq(data, "patients")
            ),
        )


@dataclass(frozen=True)
class StageClinical:
    """Этап 2 «Клинико-эпидемиологический диагноз»: поиск, точка ветвления, документы."""

    KIND: ClassVar[StageKind] = StageKind.CLINICAL
    title: str = "Клинико-эпидемиологический диагноз"
    intro: str = ""
    search: KeywordSearch | None = None
    branch: BranchPoint | None = None
    documents: tuple[DocumentTask, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "title": self.title,
            "intro": self.intro,
            "search": self.search.to_dict() if self.search is not None else None,
            "branch": self.branch.to_dict() if self.branch is not None else None,
            "documents": [d.to_dict() for d in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StageClinical:
        raw_search = data.get("search")
        raw_branch = data.get("branch")
        return cls(
            title=opt_str(data, "title", "Клинико-эпидемиологический диагноз"),
            intro=opt_str(data, "intro"),
            search=(
                KeywordSearch.from_dict(as_map(raw_search))
                if raw_search is not None
                else None
            ),
            branch=(
                BranchPoint.from_dict(as_map(raw_branch))
                if raw_branch is not None
                else None
            ),
            documents=tuple(
                DocumentTask.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
        )


@dataclass(frozen=True)
class StageContacts:
    """Этап 3 «Обследование контактных лиц»: схема осмотра (SchemeDocument) + сверка осмотра."""

    KIND: ClassVar[StageKind] = StageKind.CONTACTS
    title: str = "Обследование контактных лиц"
    intro: str = ""
    scheme: SchemeDocument | None = None
    inspection: InspectionCheck | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "title": self.title,
            "intro": self.intro,
            "scheme": self.scheme.to_dict() if self.scheme is not None else None,
            "inspection": (
                self.inspection.to_dict() if self.inspection is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StageContacts:
        raw_scheme = data.get("scheme")
        raw_inspection = data.get("inspection")
        return cls(
            title=opt_str(data, "title", "Обследование контактных лиц"),
            intro=opt_str(data, "intro"),
            scheme=scheme_from_raw(raw_scheme),
            inspection=(
                InspectionCheck.from_dict(as_map(raw_inspection))
                if raw_inspection is not None
                else None
            ),
        )


@dataclass(frozen=True)
class StageEnvironment:
    """Этап 4 «Обследование объектов внешней среды»: схема, фото, документы, осмотр."""

    KIND: ClassVar[StageKind] = StageKind.ENVIRONMENT
    title: str = "Обследование объектов внешней среды"
    intro: str = ""
    scheme: SchemeDocument | None = None
    photos: tuple[str, ...] = ()
    documents: tuple[DocumentTask, ...] = ()
    inspection: InspectionCheck | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "title": self.title,
            "intro": self.intro,
            "scheme": self.scheme.to_dict() if self.scheme is not None else None,
            "photos": list(self.photos),
            "documents": [d.to_dict() for d in self.documents],
            "inspection": (
                self.inspection.to_dict() if self.inspection is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StageEnvironment:
        raw_scheme = data.get("scheme")
        raw_inspection = data.get("inspection")
        return cls(
            title=opt_str(data, "title", "Обследование объектов внешней среды"),
            intro=opt_str(data, "intro"),
            scheme=scheme_from_raw(raw_scheme),
            photos=str_tuple(data, "photos"),
            documents=tuple(
                DocumentTask.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
            inspection=(
                InspectionCheck.from_dict(as_map(raw_inspection))
                if raw_inspection is not None
                else None
            ),
        )


@dataclass(frozen=True)
class StageSes:
    """Этап 5 «Оценка СЭС» (Прил. 22): поиск, выбор уровня СЭС, документы."""

    KIND: ClassVar[StageKind] = StageKind.SES
    title: str = "Оценка СЭС"
    intro: str = ""
    search: KeywordSearch | None = None
    level_choice: DocumentField | None = None
    documents: tuple[DocumentTask, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "title": self.title,
            "intro": self.intro,
            "search": self.search.to_dict() if self.search is not None else None,
            "level_choice": (
                self.level_choice.to_dict() if self.level_choice is not None else None
            ),
            "documents": [d.to_dict() for d in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StageSes:
        raw_search = data.get("search")
        raw_level = data.get("level_choice")
        return cls(
            title=opt_str(data, "title", "Оценка СЭС"),
            intro=opt_str(data, "intro"),
            search=(
                KeywordSearch.from_dict(as_map(raw_search))
                if raw_search is not None
                else None
            ),
            level_choice=(
                DocumentField.from_dict(as_map(raw_level))
                if raw_level is not None
                else None
            ),
            documents=tuple(
                DocumentTask.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
        )


@dataclass(frozen=True)
class StageFinal:
    """Этап 6 «Окончательный эпидемиологический диагноз»: поиск, документы, таймлайны."""

    KIND: ClassVar[StageKind] = StageKind.FINAL
    title: str = "Окончательный эпидемиологический диагноз"
    intro: str = ""
    search: KeywordSearch | None = None
    documents: tuple[DocumentTask, ...] = ()
    timelines: tuple[Timeline, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "title": self.title,
            "intro": self.intro,
            "search": self.search.to_dict() if self.search is not None else None,
            "documents": [d.to_dict() for d in self.documents],
            "timelines": [t.to_dict() for t in self.timelines],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> StageFinal:
        raw_search = data.get("search")
        return cls(
            title=opt_str(data, "title", "Окончательный эпидемиологический диагноз"),
            intro=opt_str(data, "intro"),
            search=(
                KeywordSearch.from_dict(as_map(raw_search))
                if raw_search is not None
                else None
            ),
            documents=tuple(
                DocumentTask.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
            timelines=tuple(
                Timeline.from_dict(as_map(item)) for item in seq(data, "timelines")
            ),
        )


Stage = StagePatients | StageClinical | StageContacts | StageEnvironment | StageSes | StageFinal
