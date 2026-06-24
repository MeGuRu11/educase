"""Прохождение кейса курсантом: метаданные, шесть именованных слотов ответов (ADR-008).

Документная модель (ADR-009): сериализация только через ``to_dict``/``from_dict``; версия
формата живёт исключительно в ``manifest`` архива (ADR-010) и здесь НЕ дублируется.

``Attempt`` хранит СЫРЫЕ ответы курсанта без вычисления правильности (ADR-008): никакого
сопоставления с конфигурацией кейса — сверка живёт в будущем слое ``report``. Слоты этапов
зеркалят слоты ``Case`` и сопоставляются с ними по ``KIND`` (переиспользуется ``StageKind``).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import ClassVar

from educase_core.domain._serde import (
    as_map,
    opt_str,
    pair_tuple,
    req_str,
    seq,
    str_tuple,
)
from educase_core.domain.stages import StageKind

# --- Примитивы ответа курсанта (сырые данные, без сверки) ---


@dataclass(frozen=True)
class SearchLog:
    """Журнал поисковых запросов курсанта (сырые строки в порядке ввода)."""

    queries: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {"queries": list(self.queries)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SearchLog:
        return cls(queries=str_tuple(data, "queries"))


@dataclass(frozen=True)
class BranchResponse:
    """Выбор курсанта в точке ветвления: id точки + id выбранной опции."""

    point_id: str
    chosen_option_id: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"point_id": self.point_id, "chosen_option_id": self.chosen_option_id}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> BranchResponse:
        return cls(
            point_id=req_str(data, "point_id"),
            chosen_option_id=opt_str(data, "chosen_option_id"),
        )


@dataclass(frozen=True)
class DocumentResponse:
    """Ответ по заданию документа: выбранная опция + пары «поле → ответ» + свободный текст.

    ``free_text`` — ответ в режиме свободного заполнения (ADR-014); в полевом режиме пуст.
    """

    task_id: str
    chosen_option_id: str = ""
    field_answers: tuple[tuple[str, str], ...] = ()
    free_text: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "chosen_option_id": self.chosen_option_id,
            "field_answers": [list(pair) for pair in self.field_answers],
            "free_text": self.free_text,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DocumentResponse:
        return cls(
            task_id=req_str(data, "task_id"),
            chosen_option_id=opt_str(data, "chosen_option_id"),
            field_answers=pair_tuple(data, "field_answers"),
            free_text=opt_str(data, "free_text"),
        )


@dataclass(frozen=True)
class InspectionResponse:
    """Свободный вывод осмотра (сырой текст, без сверки покрытия)."""

    text: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"text": self.text}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> InspectionResponse:
        return cls(text=opt_str(data, "text"))


@dataclass(frozen=True)
class ChoiceResponse:
    """Сырой ответ-выбор (например, выбранный уровень СЭС)."""

    answer: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"answer": self.answer}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ChoiceResponse:
        return cls(answer=opt_str(data, "answer"))


# --- Слоты ответов по этапам (KIND зеркалит этапы Case, ADR-004) ---


@dataclass(frozen=True)
class AttemptPatients:
    """Ответы этапа 1 «Пациенты»: журнал поиска."""

    KIND: ClassVar[StageKind] = StageKind.PATIENTS
    search: SearchLog = SearchLog()

    def to_dict(self) -> dict[str, object]:
        return {"kind": self.KIND.value, "search": self.search.to_dict()}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptPatients:
        raw_search = data.get("search")
        return cls(
            search=(
                SearchLog.from_dict(as_map(raw_search))
                if raw_search is not None
                else SearchLog()
            ),
        )


@dataclass(frozen=True)
class AttemptClinical:
    """Ответы этапа 2 «Клинико-эпидемиологический диагноз»: поиск, ветвление, документы."""

    KIND: ClassVar[StageKind] = StageKind.CLINICAL
    search: SearchLog = SearchLog()
    branch: BranchResponse | None = None
    documents: tuple[DocumentResponse, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "search": self.search.to_dict(),
            "branch": self.branch.to_dict() if self.branch is not None else None,
            "documents": [d.to_dict() for d in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptClinical:
        raw_search = data.get("search")
        raw_branch = data.get("branch")
        return cls(
            search=(
                SearchLog.from_dict(as_map(raw_search))
                if raw_search is not None
                else SearchLog()
            ),
            branch=(
                BranchResponse.from_dict(as_map(raw_branch))
                if raw_branch is not None
                else None
            ),
            documents=tuple(
                DocumentResponse.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
        )


@dataclass(frozen=True)
class AttemptContacts:
    """Ответы этапа 3 «Обследование контактных лиц»: свободный вывод осмотра."""

    KIND: ClassVar[StageKind] = StageKind.CONTACTS
    inspection: InspectionResponse | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "inspection": (
                self.inspection.to_dict() if self.inspection is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptContacts:
        raw_inspection = data.get("inspection")
        return cls(
            inspection=(
                InspectionResponse.from_dict(as_map(raw_inspection))
                if raw_inspection is not None
                else None
            ),
        )


@dataclass(frozen=True)
class AttemptEnvironment:
    """Ответы этапа 4 «Обследование объектов внешней среды»: документы, осмотр."""

    KIND: ClassVar[StageKind] = StageKind.ENVIRONMENT
    documents: tuple[DocumentResponse, ...] = ()
    inspection: InspectionResponse | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "documents": [d.to_dict() for d in self.documents],
            "inspection": (
                self.inspection.to_dict() if self.inspection is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptEnvironment:
        raw_inspection = data.get("inspection")
        return cls(
            documents=tuple(
                DocumentResponse.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
            inspection=(
                InspectionResponse.from_dict(as_map(raw_inspection))
                if raw_inspection is not None
                else None
            ),
        )


@dataclass(frozen=True)
class AttemptSes:
    """Ответы этапа 5 «Оценка СЭС»: поиск, выбор уровня СЭС, документы."""

    KIND: ClassVar[StageKind] = StageKind.SES
    search: SearchLog = SearchLog()
    level_choice: ChoiceResponse | None = None
    documents: tuple[DocumentResponse, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "search": self.search.to_dict(),
            "level_choice": (
                self.level_choice.to_dict() if self.level_choice is not None else None
            ),
            "documents": [d.to_dict() for d in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptSes:
        raw_search = data.get("search")
        raw_level = data.get("level_choice")
        return cls(
            search=(
                SearchLog.from_dict(as_map(raw_search))
                if raw_search is not None
                else SearchLog()
            ),
            level_choice=(
                ChoiceResponse.from_dict(as_map(raw_level))
                if raw_level is not None
                else None
            ),
            documents=tuple(
                DocumentResponse.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
        )


@dataclass(frozen=True)
class AttemptFinal:
    """Ответы этапа 6 «Окончательный эпидемиологический диагноз»: поиск, документы."""

    KIND: ClassVar[StageKind] = StageKind.FINAL
    search: SearchLog = SearchLog()
    documents: tuple[DocumentResponse, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.KIND.value,
            "search": self.search.to_dict(),
            "documents": [d.to_dict() for d in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptFinal:
        raw_search = data.get("search")
        return cls(
            search=(
                SearchLog.from_dict(as_map(raw_search))
                if raw_search is not None
                else SearchLog()
            ),
            documents=tuple(
                DocumentResponse.from_dict(as_map(item)) for item in seq(data, "documents")
            ),
        )


AttemptStage = (
    AttemptPatients
    | AttemptClinical
    | AttemptContacts
    | AttemptEnvironment
    | AttemptSes
    | AttemptFinal
)


# --- Метаданные и агрегат прохождения (зеркалят CaseMeta/Case) ---


@dataclass(frozen=True)
class AttemptMeta:
    """Метаданные прохождения. Без авторизации/ролей.

    ``trainee_label`` — ФИО курсанта; ``rank`` — звание; ``study_group`` — учебная группа.
    Звание и учебная группа необязательны на уровне модели (дефолт ``""``); обязательность
    ФИО — забота UI.
    """

    case_id: str
    trainee_label: str = ""
    created_at: str = ""
    rank: str = ""
    study_group: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "trainee_label": self.trainee_label,
            "created_at": self.created_at,
            "rank": self.rank,
            "study_group": self.study_group,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> AttemptMeta:
        return cls(
            case_id=req_str(data, "case_id"),
            trainee_label=opt_str(data, "trainee_label"),
            created_at=opt_str(data, "created_at"),
            rank=opt_str(data, "rank"),
            study_group=opt_str(data, "study_group"),
        )


@dataclass(frozen=True)
class Attempt:
    """Прохождение целиком: метаданные + шесть именованных слотов ответов (без ассетов)."""

    meta: AttemptMeta
    patients: AttemptPatients = field(default_factory=AttemptPatients)
    clinical: AttemptClinical = field(default_factory=AttemptClinical)
    contacts: AttemptContacts = field(default_factory=AttemptContacts)
    environment: AttemptEnvironment = field(default_factory=AttemptEnvironment)
    ses: AttemptSes = field(default_factory=AttemptSes)
    final: AttemptFinal = field(default_factory=AttemptFinal)

    def ordered(self) -> tuple[AttemptStage, ...]:
        """Слоты ответов в фиксированном порядке этапов (ADR-004)."""
        return (
            self.patients,
            self.clinical,
            self.contacts,
            self.environment,
            self.ses,
            self.final,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "meta": self.meta.to_dict(),
            "stages": {
                "patients": self.patients.to_dict(),
                "clinical": self.clinical.to_dict(),
                "contacts": self.contacts.to_dict(),
                "environment": self.environment.to_dict(),
                "ses": self.ses.to_dict(),
                "final": self.final.to_dict(),
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Attempt:
        stages = as_map(data["stages"])
        return cls(
            meta=AttemptMeta.from_dict(as_map(data["meta"])),
            patients=AttemptPatients.from_dict(as_map(stages["patients"])),
            clinical=AttemptClinical.from_dict(as_map(stages["clinical"])),
            contacts=AttemptContacts.from_dict(as_map(stages["contacts"])),
            environment=AttemptEnvironment.from_dict(as_map(stages["environment"])),
            ses=AttemptSes.from_dict(as_map(stages["ses"])),
            final=AttemptFinal.from_dict(as_map(stages["final"])),
        )
