"""Тесты сборки ``Case`` из ``CaseDraft`` (CONSTRUCTOR-01, слой приложения)."""
from __future__ import annotations

import pytest

from educase_core.application.case_builder import (
    BranchDraft,
    BranchOptionDraft,
    CaseDraft,
    ClinicalDraft,
    PatientDraft,
    SearchDraft,
    SearchEntryDraft,
    SynonymSetDraft,
    build_case,
)
from educase_core.domain import Case, StageClinical, StageFinal


def test_build_case_with_meta_and_patients() -> None:
    """Мета и два ``PatientDraft`` → корректный ``Case`` с двумя ``PatientCard``."""
    draft = CaseDraft(
        case_id="case-1",
        title="Вспышка ОКИ",
        author="Иванов",
        nosology="Сальмонеллёз",
        unit_personnel=150,
        patients=(
            PatientDraft(id="p1", title="Пациент 1", fields=(("Возраст", "25"),)),
            PatientDraft(id="p2", title="Пациент 2", assets=("img_01",)),
        ),
    )
    case = build_case(draft)

    assert case.meta.id == "case-1"
    assert case.meta.title == "Вспышка ОКИ"
    assert case.meta.author == "Иванов"
    assert case.meta.nosology == "Сальмонеллёз"
    assert case.meta.unit_personnel == 150
    assert case.meta.created_at  # ISO-дата проставлена
    assert len(case.patients.patients) == 2
    assert case.patients.patients[0].id == "p1"
    assert case.patients.patients[0].fields == (("Возраст", "25"),)
    assert case.patients.patients[1].assets == ("img_01",)
    # Остальные этапы — дефолтные пустые.
    assert case.clinical == StageClinical()
    assert case.final == StageFinal()
    assert case.patients.search is None


def test_build_case_empty_id_raises() -> None:
    """Пустой (или пробельный) идентификатор кейса → ``ValueError``."""
    with pytest.raises(ValueError):
        build_case(CaseDraft(case_id="   "))


def test_build_case_unit_personnel_none() -> None:
    """``unit_personnel=None`` пробрасывается в мету без подмены на 0."""
    case = build_case(CaseDraft(case_id="case-2", unit_personnel=None))
    assert case.meta.unit_personnel is None


def test_build_case_without_clinical_default_stage() -> None:
    """``CaseDraft`` без ``clinical`` → ``case.clinical`` равен дефолтному ``StageClinical``."""
    case = build_case(CaseDraft(case_id="case-3"))
    assert case.clinical == StageClinical()


def _clinical_draft() -> ClinicalDraft:
    return ClinicalDraft(
        intro="Осмотрите больных",
        search=SearchDraft(
            entries=(
                SearchEntryDraft(
                    triggers=SynonymSetDraft(
                        canonical="температура",
                        synonyms=("лихорадка",),
                    ),
                    reveal_text="38,5 °C",
                    reveal_assets=("img_temp",),
                ),
            ),
        ),
        branch=BranchDraft(
            prompt="Предварительный диагноз?",
            options=(
                BranchOptionDraft(label="ОКИ", is_correct=True),
                BranchOptionDraft(label="ОРВИ", is_correct=False),
            ),
        ),
    )


def test_build_case_clinical_search_and_branch() -> None:
    """``clinical`` → поиск содержит ожидаемую ``SearchEntry``; развилка — верный ``is_correct``."""
    case = build_case(CaseDraft(case_id="case-c", clinical=_clinical_draft()))

    search = case.clinical.search
    assert search is not None
    assert len(search.entries) == 1
    entry = search.entries[0]
    assert entry.id == "entry-1"
    assert entry.triggers.canonical == "температура"
    assert entry.triggers.synonyms == ("лихорадка",)
    assert entry.reveal_text == "38,5 °C"
    assert entry.reveal_assets == ("img_temp",)

    branch = case.clinical.branch
    assert branch is not None
    assert branch.prompt == "Предварительный диагноз?"
    assert len(branch.options) == 2
    assert branch.options[0].label == "ОКИ"
    assert branch.options[0].is_correct is True
    assert branch.options[1].is_correct is False


def test_build_case_clinical_drops_empty_entries() -> None:
    """Записи поиска с пустым каноническим термином отбрасываются, нумерация сквозная."""
    clinical = ClinicalDraft(
        search=SearchDraft(
            entries=(
                SearchEntryDraft(triggers=SynonymSetDraft(canonical="   ")),
                SearchEntryDraft(triggers=SynonymSetDraft(canonical="сыпь")),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-d", clinical=clinical))

    search = case.clinical.search
    assert search is not None
    assert len(search.entries) == 1
    assert search.entries[0].id == "entry-1"
    assert search.entries[0].triggers.canonical == "сыпь"


def test_build_case_clinical_optional_search_without_entries() -> None:
    """``optional=True`` при нуле записей → поиск не ``None`` (``KeywordSearch`` с optional)."""
    clinical = ClinicalDraft(search=SearchDraft(entries=(), optional=True))
    case = build_case(CaseDraft(case_id="case-o", clinical=clinical))

    search = case.clinical.search
    assert search is not None
    assert search.entries == ()
    assert search.optional is True


def test_build_case_clinical_empty_search_and_branch_are_none() -> None:
    """Пустой поиск (без optional) и пустая развилка → ``search``/``branch`` равны ``None``."""
    case = build_case(CaseDraft(case_id="case-e", clinical=ClinicalDraft()))
    assert case.clinical.search is None
    assert case.clinical.branch is None


def test_build_case_clinical_round_trip_to_dict() -> None:
    """round-trip: build_case(...).to_dict() → Case.from_dict(...) сохраняет ``clinical``."""
    case = build_case(CaseDraft(case_id="case-rt", clinical=_clinical_draft()))
    restored = Case.from_dict(case.to_dict())
    assert restored.clinical == case.clinical
