"""Строгий поиск по ключевым словам (ADR-006).

Нормализация — ``strip`` + ``casefold``; сопоставление — ТОЧНОЕ совпадение нормализованных
строк, без fuzzy-матчинга и устойчивости к опечаткам. Для свободного вывода осмотра — сверка
по вхождению термина как подстроки (containment).
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from epicase_core.domain._serde import (
    as_map,
    opt_bool,
    opt_str,
    req_str,
    seq,
    str_tuple,
)


def _normalize(text: str) -> str:
    """Нормализовать строку для сравнения: обрезать пробелы и привести регистр."""
    return text.strip().casefold()


@dataclass(frozen=True)
class SynonymSet:
    """Группа синонимов вокруг канонического термина (синонимы задаёт преподаватель)."""

    canonical: str
    synonyms: tuple[str, ...] = ()

    def terms(self) -> tuple[str, ...]:
        """Все термины группы: канонический + синонимы."""
        return (self.canonical, *self.synonyms)

    def matches(self, query: str) -> bool:
        """Точное совпадение нормализованного запроса с одним из терминов."""
        normalized = _normalize(query)
        return any(_normalize(term) == normalized for term in self.terms())

    def contained_in(self, text: str) -> bool:
        """Хотя бы один термин входит как подстрока в нормализованный текст."""
        haystack = _normalize(text)
        return any(_normalize(term) in haystack for term in self.terms())

    def to_dict(self) -> dict[str, object]:
        return {"canonical": self.canonical, "synonyms": list(self.synonyms)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SynonymSet:
        return cls(
            canonical=req_str(data, "canonical"),
            synonyms=str_tuple(data, "synonyms"),
        )


@dataclass(frozen=True)
class SearchEntry:
    """Точка вскрытия информации поиском: триггеры + что открывается (текст и ассеты по id)."""

    id: str
    triggers: SynonymSet
    reveal_text: str = ""
    reveal_assets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "triggers": self.triggers.to_dict(),
            "reveal_text": self.reveal_text,
            "reveal_assets": list(self.reveal_assets),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> SearchEntry:
        return cls(
            id=req_str(data, "id"),
            triggers=SynonymSet.from_dict(as_map(data["triggers"])),
            reveal_text=opt_str(data, "reveal_text"),
            reveal_assets=str_tuple(data, "reveal_assets"),
        )


@dataclass(frozen=True)
class KeywordSearch:
    """Контекстный поиск этапа: набор точек вскрытия (строгое совпадение)."""

    entries: tuple[SearchEntry, ...] = ()
    optional: bool = False

    def find(self, query: str) -> SearchEntry | None:
        """Первая запись, чьи триггеры точно совпали с запросом, иначе ``None``."""
        for entry in self.entries:
            if entry.triggers.matches(query):
                return entry
        return None

    def to_dict(self) -> dict[str, object]:
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "optional": self.optional,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> KeywordSearch:
        return cls(
            entries=tuple(
                SearchEntry.from_dict(as_map(item)) for item in seq(data, "entries")
            ),
            optional=opt_bool(data, "optional"),
        )


@dataclass(frozen=True)
class InspectionCheck:
    """Сверка свободного вывода осмотра: покрытие ожидаемых групп по вхождению (ADR-006)."""

    expected: tuple[SynonymSet, ...] = ()

    def covered(self, text: str) -> tuple[bool, ...]:
        """Для каждой ожидаемой группы — вошёл ли хоть один её термин в текст."""
        return tuple(group.contained_in(text) for group in self.expected)

    def to_dict(self) -> dict[str, object]:
        return {"expected": [group.to_dict() for group in self.expected]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> InspectionCheck:
        return cls(
            expected=tuple(
                SynonymSet.from_dict(as_map(item)) for item in seq(data, "expected")
            ),
        )
