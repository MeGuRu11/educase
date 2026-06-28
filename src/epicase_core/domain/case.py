"""Корневая сущность кейса: метаданные, шесть именованных слотов этапов, реестр ассетов.

Документная модель (ADR-009): сериализация только через ``to_dict``/``from_dict``; версия
формата живёт исключительно в ``manifest`` архива (ADR-010) и здесь НЕ дублируется.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from epicase_core.domain._serde import as_map, opt_int, opt_str, req_str, seq
from epicase_core.domain.assets import AssetRef
from epicase_core.domain.stages import (
    Stage,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StagePatients,
    StageSes,
)


@dataclass(frozen=True)
class CaseMeta:
    """Метаданные кейса (без версии формата — она только в manifest, ADR-010).

    ``author`` — ФИО преподавателя; ``author_rank`` — звание. Звание необязательно на
    уровне модели (дефолт ``""``); обязательность ФИО — забота UI.
    """

    id: str
    title: str = ""
    author: str = ""
    nosology: str = ""
    unit_personnel: int | None = None
    created_at: str = ""
    author_rank: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "nosology": self.nosology,
            "unit_personnel": self.unit_personnel,
            "created_at": self.created_at,
            "author_rank": self.author_rank,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CaseMeta:
        return cls(
            id=req_str(data, "id"),
            title=opt_str(data, "title"),
            author=opt_str(data, "author"),
            nosology=opt_str(data, "nosology"),
            unit_personnel=opt_int(data, "unit_personnel"),
            created_at=opt_str(data, "created_at"),
            author_rank=opt_str(data, "author_rank"),
        )


@dataclass(frozen=True)
class Case:
    """Кейс целиком: метаданные + шесть именованных этапов + реестр ассетов."""

    meta: CaseMeta
    patients: StagePatients = field(default_factory=StagePatients)
    clinical: StageClinical = field(default_factory=StageClinical)
    contacts: StageContacts = field(default_factory=StageContacts)
    environment: StageEnvironment = field(default_factory=StageEnvironment)
    ses: StageSes = field(default_factory=StageSes)
    final: StageFinal = field(default_factory=StageFinal)
    assets: tuple[AssetRef, ...] = ()

    def ordered(self) -> tuple[Stage, ...]:
        """Этапы в фиксированном порядке (ADR-004)."""
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
            "assets": [a.to_dict() for a in self.assets],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Case:
        stages = as_map(data["stages"])
        return cls(
            meta=CaseMeta.from_dict(as_map(data["meta"])),
            patients=StagePatients.from_dict(as_map(stages["patients"])),
            clinical=StageClinical.from_dict(as_map(stages["clinical"])),
            contacts=StageContacts.from_dict(as_map(stages["contacts"])),
            environment=StageEnvironment.from_dict(as_map(stages["environment"])),
            ses=StageSes.from_dict(as_map(stages["ses"])),
            final=StageFinal.from_dict(as_map(stages["final"])),
            assets=tuple(AssetRef.from_dict(as_map(item)) for item in seq(data, "assets")),
        )
