"""Тесты сверки ответов: MatchRule.accepts и DocumentField.check (FEATURE-03).

Сверка строгая, без fuzzy (ADR-006); неверный ответ возвращает ``False`` и не падает (ADR-008).
"""
from __future__ import annotations

from epicase_core.domain import (
    ChoiceMatch,
    DateMatch,
    DocumentField,
    FieldType,
    NumberMatch,
    SynonymSet,
    TextMatch,
)


def test_text_match_synonym_accepted_typo_rejected() -> None:
    rule = TextMatch(keywords=SynonymSet(canonical="диарея", synonyms=("понос",)))
    assert rule.accepts("Понос") is True
    assert rule.accepts("  диарея ") is True
    assert rule.accepts("диарей") is False  # опечатка/обрезка — нет fuzzy


def test_number_match_exact_and_tolerance() -> None:
    assert NumberMatch(value=5.0).accepts("5") is True
    assert NumberMatch(value=5.0, tolerance=0.3).accepts("5,2") is True
    assert NumberMatch(value=5.0, tolerance=0.3).accepts("5,5") is False


def test_number_match_unparseable_is_false() -> None:
    assert NumberMatch(value=5.0).accepts("abc") is False
    assert NumberMatch(value=5.0).accepts("") is False


def test_number_match_ndigits_rounding() -> None:
    rule = NumberMatch(value=5.0, ndigits=0)
    assert rule.accepts("5,4") is True   # округление до 5
    assert rule.accepts("5,6") is False  # округление до 6


def test_date_match_exact_with_whitespace() -> None:
    rule = DateMatch(value="2026-06-09")
    assert rule.accepts("2026-06-09") is True
    assert rule.accepts("  2026-06-09 ") is True
    assert rule.accepts("2026-06-10") is False


def test_choice_match_case_insensitive() -> None:
    rule = ChoiceMatch(correct=("Неблагополучное",))
    assert rule.accepts("неблагополучное") is True
    assert rule.accepts("  НЕБЛАГОПОЛУЧНОЕ ") is True
    assert rule.accepts("Чрезвычайное") is False


def test_document_field_check_empty_optional_accepted() -> None:
    doc_field = DocumentField(
        id="f-opt",
        type=FieldType.TEXT,
        rule=TextMatch(keywords=SynonymSet(canonical="да")),
        required=False,
    )
    assert doc_field.check("   ") is True  # пустой ответ необязательного поля
    assert doc_field.check("нет") is False  # непустой неверный — сверяется правилом


def test_document_field_check_required_and_valid() -> None:
    doc_field = DocumentField(
        id="f-req",
        type=FieldType.TEXT,
        rule=TextMatch(keywords=SynonymSet(canonical="да")),
        required=True,
    )
    assert doc_field.check("") is False  # обязательное пустое — не принято
    assert doc_field.check("да") is True
