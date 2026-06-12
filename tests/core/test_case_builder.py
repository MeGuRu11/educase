"""Тесты сборки ``Case`` из ``CaseDraft`` (CONSTRUCTOR-01, слой приложения)."""
from __future__ import annotations

from pathlib import Path

import pytest

from educase_core.application.case_builder import (
    BranchDraft,
    BranchOptionDraft,
    CaseDraft,
    ClinicalDraft,
    ContactsDraft,
    DocumentOptionDraft,
    DocumentTaskDraft,
    EnvironmentDraft,
    FieldDraft,
    InspectionDraft,
    PatientDraft,
    SearchDraft,
    SearchEntryDraft,
    SynonymSetDraft,
    TemplateDraft,
    _build_field,
    build_case,
)
from educase_core.domain import (
    Case,
    ChoiceMatch,
    DateMatch,
    FieldType,
    NumberMatch,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    TextMatch,
)


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


# --- Документы: сборка полей по типу правила ---


def test_build_field_text_rule() -> None:
    """Поле ``text`` → ``TextMatch`` с переданными ключевыми словами; id и тип проставлены."""
    field = _build_field(
        FieldDraft(
            label="Диагноз",
            field_type="text",
            keywords=SynonymSetDraft(canonical="сальмонеллёз", synonyms=("salmonella",)),
        ),
        1,
    )
    assert field.id == "field-1"
    assert field.type is FieldType.TEXT
    assert field.label == "Диагноз"
    assert isinstance(field.rule, TextMatch)
    assert field.rule.keywords.canonical == "сальмонеллёз"
    assert field.rule.keywords.synonyms == ("salmonella",)


def test_build_field_number_rule_comma_tolerance_ndigits() -> None:
    """Поле ``number`` → ``NumberMatch``: запятая→точка, допуск и ndigits разобраны."""
    field = _build_field(
        FieldDraft(
            label="Температура",
            field_type="number",
            number_value="38,5",
            number_tolerance="0,2",
            number_ndigits="1",
        ),
        2,
    )
    assert field.id == "field-2"
    assert field.type is FieldType.NUMBER
    assert isinstance(field.rule, NumberMatch)
    assert field.rule.value == 38.5
    assert field.rule.tolerance == 0.2
    assert field.rule.ndigits == 1


def test_build_field_number_defaults_when_optional_blank() -> None:
    """Пустые допуск/ndigits → ``tolerance=0.0`` и ``ndigits=None``."""
    field = _build_field(FieldDraft(label="N", field_type="number", number_value="10"), 1)
    assert isinstance(field.rule, NumberMatch)
    assert field.rule.tolerance == 0.0
    assert field.rule.ndigits is None


def test_build_field_number_empty_value_raises() -> None:
    """Пустое значение числа → ``ValueError`` с именем поля."""
    with pytest.raises(ValueError, match="Доза"):
        _build_field(FieldDraft(label="Доза", field_type="number", number_value="  "), 1)


def test_build_field_number_garbage_ndigits_raises() -> None:
    """Нечисловые знаки округления → ``ValueError``."""
    with pytest.raises(ValueError):
        _build_field(
            FieldDraft(
                label="N",
                field_type="number",
                number_value="1",
                number_ndigits="abc",
            ),
            1,
        )


def test_build_field_date_rule() -> None:
    """Поле ``date`` → ``DateMatch`` с ISO-строкой."""
    field = _build_field(FieldDraft(label="Дата", field_type="date", date_value="2026-06-11"), 1)
    assert field.type is FieldType.DATE
    assert isinstance(field.rule, DateMatch)
    assert field.rule.value == "2026-06-11"


def test_build_field_choice_rule_with_options() -> None:
    """Поле ``choice`` → ``ChoiceMatch`` с верными; ``options`` хранят все варианты."""
    field = _build_field(
        FieldDraft(
            label="Тяжесть",
            field_type="choice",
            choice_options=("лёгкая", "средняя", "тяжёлая"),
            choice_correct=("средняя", "тяжёлая"),
        ),
        1,
    )
    assert field.type is FieldType.CHOICE
    assert isinstance(field.rule, ChoiceMatch)
    assert field.rule.correct == ("средняя", "тяжёлая")
    assert field.options == ("лёгкая", "средняя", "тяжёлая")


# --- Документы: сборка заданий с верной опцией и обманкой ---


def _document_draft() -> DocumentTaskDraft:
    return DocumentTaskDraft(
        prompt="Выберите донесение",
        options=(
            DocumentOptionDraft(
                title="Внеочередное донесение",
                is_correct=True,
                template=TemplateDraft(
                    title="ДМ-4",
                    fields=(
                        FieldDraft(label="Дата", field_type="date", date_value="2026-06-11"),
                    ),
                ),
            ),
            DocumentOptionDraft(title="Обычная справка", is_correct=False),
        ),
    )


def test_build_case_clinical_document_correct_and_decoy() -> None:
    """Документ: верная опция несёт шаблон с полями, обманка — ``template=None``."""
    clinical = ClinicalDraft(documents=(_document_draft(),))
    case = build_case(CaseDraft(case_id="case-doc", clinical=clinical))

    documents = case.clinical.documents
    assert len(documents) == 1
    task = documents[0]
    assert task.id == "doc-1"
    assert task.prompt == "Выберите донесение"
    assert len(task.options) == 2

    correct, decoy = task.options
    assert correct.id == "opt-1"
    assert correct.is_correct is True
    assert correct.template is not None
    assert correct.template.id == "tmpl-1"
    assert correct.template.title == "ДМ-4"
    assert len(correct.template.fields) == 1
    assert correct.template.fields[0].id == "field-1"
    assert isinstance(correct.template.fields[0].rule, DateMatch)

    assert decoy.id == "opt-2"
    assert decoy.is_correct is False
    assert decoy.template is None


def test_build_case_clinical_drops_blank_option_and_task() -> None:
    """Опции с пустым title и задания без prompt и опций отбрасываются."""
    clinical = ClinicalDraft(
        documents=(
            DocumentTaskDraft(
                prompt="Есть формулировка",
                options=(
                    DocumentOptionDraft(title="   "),
                    DocumentOptionDraft(title="Годная опция"),
                ),
            ),
            DocumentTaskDraft(prompt="   ", options=()),
        )
    )
    case = build_case(CaseDraft(case_id="case-drop", clinical=clinical))

    documents = case.clinical.documents
    assert len(documents) == 1
    assert documents[0].id == "doc-1"
    assert len(documents[0].options) == 1
    assert documents[0].options[0].id == "opt-1"
    assert documents[0].options[0].title == "Годная опция"


def test_build_case_clinical_documents_round_trip_codec(tmp_path: Path) -> None:
    """round-trip через кодек .educase: ``clinical.documents`` сохраняются (save→load)."""
    from educase_core.application.cases import load_case, save_case

    clinical = ClinicalDraft(documents=(_document_draft(),))
    case = build_case(CaseDraft(case_id="case-rt-doc", clinical=clinical))

    dst = save_case(case, tmp_path / "case")
    loaded = load_case(dst)
    assert loaded.case.clinical.documents == case.clinical.documents
    assert loaded.case == case


# --- Этапы 3–4: обследование контактных лиц и объектов внешней среды ---


def test_build_case_without_contacts_and_environment_default_stages() -> None:
    """``CaseDraft`` без contacts/environment → дефолтные пустые этапы 3 и 4."""
    case = build_case(CaseDraft(case_id="case-cd"))
    assert case.contacts == StageContacts()
    assert case.environment == StageEnvironment()


def test_build_case_contacts_scheme_and_inspection() -> None:
    """``contacts`` → схема и ожидаемые группы осмотра как заданы."""
    contacts = ContactsDraft(
        intro="Обследуйте контактных",
        scheme="scheme_contacts",
        inspection=InspectionDraft(
            groups=(
                SynonymSetDraft(canonical="сыпь", synonyms=("экзантема",)),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-ct", contacts=contacts))

    assert case.contacts.intro == "Обследуйте контактных"
    assert case.contacts.scheme == "scheme_contacts"
    inspection = case.contacts.inspection
    assert inspection is not None
    assert len(inspection.expected) == 1
    assert inspection.expected[0].canonical == "сыпь"
    assert inspection.expected[0].synonyms == ("экзантема",)


def test_build_case_contacts_blank_scheme_and_empty_inspection_are_none() -> None:
    """Пустая схема → ``None``; осмотр без валидных групп → ``inspection`` равен ``None``."""
    contacts = ContactsDraft(
        scheme="   ",
        inspection=InspectionDraft(groups=(SynonymSetDraft(canonical="  "),)),
    )
    case = build_case(CaseDraft(case_id="case-cn", contacts=contacts))
    assert case.contacts.scheme is None
    assert case.contacts.inspection is None


def test_build_case_environment_photos_documents_inspection() -> None:
    """``environment`` → схема, отфильтрованные фото, документы и осмотр как заданы."""
    environment = EnvironmentDraft(
        intro="Обследуйте пищеблок",
        scheme="scheme_env",
        photos=("img_01", "  img_02  ", "   "),  # пустые/пробельные отбрасываются
        documents=(
            DocumentTaskDraft(
                prompt="Выберите акт",
                options=(DocumentOptionDraft(title="Акт обследования"),),
            ),
        ),
        inspection=InspectionDraft(
            groups=(SynonymSetDraft(canonical="грязь"),),
        ),
    )
    case = build_case(CaseDraft(case_id="case-en", environment=environment))

    assert case.environment.scheme == "scheme_env"
    assert case.environment.photos == ("img_01", "img_02")
    assert len(case.environment.documents) == 1
    assert case.environment.documents[0].id == "doc-1"
    assert case.environment.documents[0].prompt == "Выберите акт"
    inspection = case.environment.inspection
    assert inspection is not None
    assert len(inspection.expected) == 1
    assert inspection.expected[0].canonical == "грязь"


def test_build_case_environment_blank_scheme_and_empty_inspection_are_none() -> None:
    """Пустая схема → ``None``; осмотр без валидных групп → ``inspection`` равен ``None``."""
    case = build_case(
        CaseDraft(case_id="case-eb", environment=EnvironmentDraft(scheme=""))
    )
    assert case.environment.scheme is None
    assert case.environment.inspection is None


def test_build_case_contacts_environment_round_trip_to_dict() -> None:
    """round-trip: build_case(...).to_dict() → Case.from_dict(...) сохраняет этапы 3 и 4."""
    contacts = ContactsDraft(
        scheme="scheme_contacts",
        inspection=InspectionDraft(groups=(SynonymSetDraft(canonical="сыпь"),)),
    )
    environment = EnvironmentDraft(
        scheme="scheme_env",
        photos=("img_01",),
        inspection=InspectionDraft(groups=(SynonymSetDraft(canonical="грязь"),)),
    )
    case = build_case(
        CaseDraft(case_id="case-rt34", contacts=contacts, environment=environment)
    )
    restored = Case.from_dict(case.to_dict())
    assert restored.contacts == case.contacts
    assert restored.environment == case.environment
