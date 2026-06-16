"""Документы кейса (ADR-007).

Курсант выбирает правильный документ из списка с обманками и заполняет его поля; поля
сверяются по правилам. Обманка — ``DocumentOption`` с ``is_correct=False`` и ``template=None``.
Правила сверки — дискриминируемое объединение по ключу ``"type"``.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import ClassVar

from educase_core.domain._serde import (
    as_map,
    opt_bool,
    opt_float,
    opt_int,
    opt_str,
    req_float,
    req_str,
    seq,
    str_tuple,
)
from educase_core.domain.search import SynonymSet


class FieldType(StrEnum):
    """Тип поля документа (определяет UI-виджет ввода)."""

    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CHOICE = "choice"


# --- Правила сверки полей (дискриминатор — ClassVar TYPE, ключ "type" в to_dict) ---


@dataclass(frozen=True)
class TextMatch:
    """Сверка текста по ключевым словам (точное совпадение нормализованных строк)."""

    TYPE: ClassVar[str] = "text"
    keywords: SynonymSet

    def accepts(self, answer: str) -> bool:
        """Принять ответ при точном совпадении с одним из ключевых слов (ADR-006)."""
        return self.keywords.matches(answer)

    def to_dict(self) -> dict[str, object]:
        return {"type": self.TYPE, "keywords": self.keywords.to_dict()}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> TextMatch:
        return cls(keywords=SynonymSet.from_dict(as_map(data["keywords"])))


@dataclass(frozen=True)
class NumberMatch:
    """Числовая сверка: значение с допуском и опциональным округлением до ``ndigits``."""

    TYPE: ClassVar[str] = "number"
    value: float
    tolerance: float = 0.0
    ndigits: int | None = None

    def accepts(self, answer: str) -> bool:
        """Принять число в пределах допуска. Непарсящийся ответ — ``False`` (ADR-008).

        Перед парсингом запятая заменяется точкой; при заданном ``ndigits`` распарсенное
        значение округляется до указанного числа знаков.
        """
        try:
            parsed = float(answer.strip().replace(",", "."))
        except ValueError:
            return False
        if self.ndigits is not None:
            parsed = round(parsed, self.ndigits)
        return abs(parsed - self.value) <= self.tolerance

    def to_dict(self) -> dict[str, object]:
        return {
            "type": self.TYPE,
            "value": self.value,
            "tolerance": self.tolerance,
            "ndigits": self.ndigits,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> NumberMatch:
        return cls(
            value=req_float(data, "value"),
            tolerance=opt_float(data, "tolerance"),
            ndigits=opt_int(data, "ndigits"),
        )


@dataclass(frozen=True)
class DateMatch:
    """Сверка даты по строке формата ДД.ММ.ГГГГ."""

    TYPE: ClassVar[str] = "date"
    value: str = ""

    def accepts(self, answer: str) -> bool:
        """Принять дату при точном равенстве строк (ожидается ДД.ММ.ГГГГ); пробелы обрезаются."""
        return answer.strip() == self.value.strip()

    def to_dict(self) -> dict[str, object]:
        return {"type": self.TYPE, "value": self.value}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DateMatch:
        return cls(value=opt_str(data, "value"))


@dataclass(frozen=True)
class ChoiceMatch:
    """Сверка выбора: множество допустимых вариантов."""

    TYPE: ClassVar[str] = "choice"
    correct: tuple[str, ...] = ()

    def accepts(self, answer: str) -> bool:
        """Принять выбор: нормализованный (casefold + strip) ответ есть среди допустимых."""
        normalized = answer.strip().casefold()
        return any(normalized == option.strip().casefold() for option in self.correct)

    def to_dict(self) -> dict[str, object]:
        return {"type": self.TYPE, "correct": list(self.correct)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ChoiceMatch:
        return cls(correct=str_tuple(data, "correct"))


MatchRule = TextMatch | NumberMatch | DateMatch | ChoiceMatch


def match_rule_from_dict(data: Mapping[str, object]) -> MatchRule:
    """Диспетчер правил сверки по дискриминатору ``"type"`` (``ValueError`` на неизвестный)."""
    rule_type = req_str(data, "type")
    if rule_type == TextMatch.TYPE:
        return TextMatch.from_dict(data)
    if rule_type == NumberMatch.TYPE:
        return NumberMatch.from_dict(data)
    if rule_type == DateMatch.TYPE:
        return DateMatch.from_dict(data)
    if rule_type == ChoiceMatch.TYPE:
        return ChoiceMatch.from_dict(data)
    raise ValueError(f"неизвестный тип правила сверки: {rule_type!r}")


@dataclass(frozen=True)
class DocumentField:
    """Поле документа: тип, правило сверки, опции для выбора и признак обязательности."""

    id: str
    type: FieldType
    rule: MatchRule
    label: str = ""
    options: tuple[str, ...] = ()
    required: bool = True

    def check(self, answer: str) -> bool:
        """Сверить ответ с правилом поля. Пустой ответ необязательного поля принимается."""
        if not answer.strip() and not self.required:
            return True
        return self.rule.accepts(answer)

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type.value,
            "rule": self.rule.to_dict(),
            "options": list(self.options),
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DocumentField:
        return cls(
            id=req_str(data, "id"),
            type=FieldType(req_str(data, "type")),
            rule=match_rule_from_dict(as_map(data["rule"])),
            label=opt_str(data, "label"),
            options=str_tuple(data, "options"),
            required=opt_bool(data, "required", default=True),
        )


@dataclass(frozen=True)
class DocumentTemplate:
    """Шаблон документа: заголовок + поля для заполнения."""

    id: str
    title: str = ""
    fields: tuple[DocumentField, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "fields": [f.to_dict() for f in self.fields],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DocumentTemplate:
        return cls(
            id=req_str(data, "id"),
            title=opt_str(data, "title"),
            fields=tuple(
                DocumentField.from_dict(as_map(item)) for item in seq(data, "fields")
            ),
        )


@dataclass(frozen=True)
class DocumentOption:
    """Вариант выбора документа. Обманка: ``is_correct=False`` и ``template=None``."""

    id: str
    title: str = ""
    is_correct: bool = False
    template: DocumentTemplate | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "is_correct": self.is_correct,
            "template": self.template.to_dict() if self.template is not None else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DocumentOption:
        raw_template = data.get("template")
        template = (
            DocumentTemplate.from_dict(as_map(raw_template))
            if raw_template is not None
            else None
        )
        return cls(
            id=req_str(data, "id"),
            title=opt_str(data, "title"),
            is_correct=opt_bool(data, "is_correct"),
            template=template,
        )


@dataclass(frozen=True)
class DocumentTask:
    """Задание выбрать правильный документ из списка (с обманками)."""

    id: str
    prompt: str = ""
    options: tuple[DocumentOption, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "prompt": self.prompt,
            "options": [opt.to_dict() for opt in self.options],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> DocumentTask:
        return cls(
            id=req_str(data, "id"),
            prompt=opt_str(data, "prompt"),
            options=tuple(
                DocumentOption.from_dict(as_map(item)) for item in seq(data, "options")
            ),
        )
