"""Тесты сборки ``Case`` из ``CaseDraft`` (CONSTRUCTOR-01, слой приложения)."""
from __future__ import annotations

from pathlib import Path

import pytest

from epicase_core.application.case_builder import (
    AssetRef,
    BranchDraft,
    BranchOptionDraft,
    CaseDraft,
    ClinicalDraft,
    ContactsDraft,
    DocumentOptionDraft,
    DocumentTaskDraft,
    EnvironmentDraft,
    FieldDraft,
    FinalDraft,
    HotspotDraft,
    InspectionDraft,
    PatientDraft,
    SchemeViewDraft,
    SearchDraft,
    SearchEntryDraft,
    SesDraft,
    SynonymSetDraft,
    TemplateDraft,
    TimelineDraft,
    _build_field,
    _field_is_blank,
    build_case,
)
from epicase_core.domain import (
    Case,
    ChoiceMatch,
    DateMatch,
    FieldType,
    HotspotShape,
    NumberMatch,
    SchemeView,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StageSes,
    TextMatch,
)
from epicase_core.domain.documents import FillMode


def test_build_case_with_meta_and_patients() -> None:
    """Мета и два ``PatientDraft`` → корректный ``Case`` с двумя ``PatientCard``."""
    draft = CaseDraft(
        case_id="case-1",
        title="Вспышка ОКИ",
        author="Иванов",
        author_rank="полковник",
        nosology="Сальмонеллёз",
        unit_personnel=150,
        patients=(
            PatientDraft(title="Пациент 1", fields=(("Возраст", "25"),)),
            PatientDraft(
                title="Пациент 2",
                assets=(AssetRef("img_01", "/tmp/p2.png", "p2.png"),),
            ),
        ),
    )
    case = build_case(draft)

    assert case.meta.id == "case-1"
    assert case.meta.title == "Вспышка ОКИ"
    assert case.meta.author == "Иванов"
    assert case.meta.author_rank == "полковник"
    assert case.meta.nosology == "Сальмонеллёз"
    assert case.meta.unit_personnel == 150
    assert case.meta.created_at  # ISO-дата проставлена
    assert len(case.patients.patients) == 2
    # id пациентов автогенерируются — непустые и уникальные между карточками.
    assert case.patients.patients[0].id
    assert case.patients.patients[0].id != case.patients.patients[1].id
    assert case.patients.patients[0].fields == (("Возраст", "25"),)
    assert case.patients.patients[1].assets == ("img_01",)
    # Остальные этапы — дефолтные пустые.
    assert case.clinical == StageClinical()
    assert case.final == StageFinal()
    assert case.patients.search is None


def test_build_case_blank_id_autogenerates() -> None:
    """Пустой (или пробельный) идентификатор кейса → автогенерация непустого id."""
    case = build_case(CaseDraft(case_id="   "))
    assert case.meta.id


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
                    reveal_assets=(AssetRef("img_temp", "/tmp/temp.png", "temp.png"),),
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


def test_build_case_document_fields_mode_and_reference_assets() -> None:
    """FIELDS и ``reference_assets`` задания доходят до домена."""
    task = DocumentTaskDraft(
        prompt="Заполните поля документа",
        reference_assets=("ref-1", "ref-2"),
        options=(
            DocumentOptionDraft(
                title="Форма 23",
                is_correct=True,
                template=TemplateDraft(title="Форма 23", fill_mode="fields"),
            ),
        ),
    )
    clinical = ClinicalDraft(documents=(task,))
    case = build_case(CaseDraft(case_id="case-fm", clinical=clinical))

    doc = case.clinical.documents[0]
    assert doc.reference_assets == ("ref-1", "ref-2")
    template = doc.options[0].template
    assert template is not None
    assert template.fill_mode is FillMode.FIELDS


def test_build_case_document_attachment_mode_and_allow_multiple() -> None:
    """ADR-015: режим ``attachment`` и флаг ``allow_multiple`` шаблона доходят до домена."""
    task = DocumentTaskDraft(
        prompt="Прикрепите заполненную форму",
        options=(
            DocumentOptionDraft(
                title="Форма 23",
                is_correct=True,
                template=TemplateDraft(
                    title="Форма 23", fill_mode="attachment", allow_multiple=True
                ),
            ),
        ),
    )
    clinical = ClinicalDraft(documents=(task,))
    case = build_case(CaseDraft(case_id="case-att", clinical=clinical))

    template = case.clinical.documents[0].options[0].template
    assert template is not None
    assert template.fill_mode is FillMode.ATTACHMENT
    assert template.allow_multiple is True


def test_build_case_clinical_documents_round_trip_codec(tmp_path: Path) -> None:
    """round-trip через кодек .epicase: ``clinical.documents`` сохраняются (save→load)."""
    from epicase_core.application.cases import load_case, save_case

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
        scheme=AssetRef("scheme_contacts", "/tmp/scheme.png", "scheme.png"),
        inspection=InspectionDraft(
            groups=(
                SynonymSetDraft(canonical="сыпь", synonyms=("экзантема",)),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-ct", contacts=contacts))

    assert case.contacts.intro == "Обследуйте контактных"
    scheme = case.contacts.scheme
    assert scheme is not None
    assert scheme.root.background == "scheme_contacts"
    inspection = case.contacts.inspection
    assert inspection is not None
    assert len(inspection.expected) == 1
    assert inspection.expected[0].canonical == "сыпь"
    assert inspection.expected[0].synonyms == ("экзантема",)


def test_build_case_contacts_blank_scheme_and_empty_inspection_are_none() -> None:
    """Не выбранная схема → ``None``; осмотр без валидных групп → ``inspection`` равен ``None``."""
    contacts = ContactsDraft(
        scheme=None,
        inspection=InspectionDraft(groups=(SynonymSetDraft(canonical="  "),)),
    )
    case = build_case(CaseDraft(case_id="case-cn", contacts=contacts))
    assert case.contacts.scheme is None
    assert case.contacts.inspection is None


def test_build_case_environment_photos_documents_inspection() -> None:
    """``environment`` → схема, фото (asset_id каждого ``AssetRef`` дословно), документы, осмотр."""
    environment = EnvironmentDraft(
        intro="Обследуйте пищеблок",
        scheme=AssetRef("scheme_env", "/tmp/env.png", "env.png"),
        photos=(
            AssetRef("img_01", "/tmp/img_01.png", "img_01.png"),
            AssetRef("img_02", "/tmp/img_02.png", "img_02.png"),
        ),
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

    env_scheme = case.environment.scheme
    assert env_scheme is not None
    assert env_scheme.root.background == "scheme_env"
    assert case.environment.photos == ("img_01", "img_02")
    assert len(case.environment.documents) == 1
    assert case.environment.documents[0].id == "doc-1"
    assert case.environment.documents[0].prompt == "Выберите акт"
    inspection = case.environment.inspection
    assert inspection is not None
    assert len(inspection.expected) == 1
    assert inspection.expected[0].canonical == "грязь"


def test_build_case_environment_blank_scheme_and_empty_inspection_are_none() -> None:
    """Не выбранная схема → ``None``; осмотр без валидных групп → ``inspection`` равен ``None``."""
    case = build_case(
        CaseDraft(case_id="case-eb", environment=EnvironmentDraft(scheme=None))
    )
    assert case.environment.scheme is None
    assert case.environment.inspection is None


def test_build_case_contacts_environment_round_trip_to_dict() -> None:
    """round-trip: build_case(...).to_dict() → Case.from_dict(...) сохраняет этапы 3 и 4."""
    contacts = ContactsDraft(
        scheme=AssetRef("scheme_contacts", "/tmp/scheme.png", "scheme.png"),
        inspection=InspectionDraft(groups=(SynonymSetDraft(canonical="сыпь"),)),
    )
    environment = EnvironmentDraft(
        scheme=AssetRef("scheme_env", "/tmp/env.png", "env.png"),
        photos=(AssetRef("img_01", "/tmp/img_01.png", "img_01.png"),),
        inspection=InspectionDraft(groups=(SynonymSetDraft(canonical="грязь"),)),
    )
    case = build_case(
        CaseDraft(case_id="case-rt34", contacts=contacts, environment=environment)
    )
    restored = Case.from_dict(case.to_dict())
    assert restored.contacts == case.contacts
    assert restored.environment == case.environment


def test_build_case_contacts_hotspots() -> None:
    """``contacts`` с фоном и зоной → плоский ``Hotspot`` в ``scheme.root.hotspots``."""
    contacts = ContactsDraft(
        scheme=AssetRef("bg-1", "/p"),
        hotspots=(
            HotspotDraft(
                0.1,
                0.2,
                0.3,
                0.4,
                label="Спальное",
                reveal_text="скученность",
                reveal_assets=(AssetRef("z1", "/pz"),),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-hc", contacts=contacts))

    scheme = case.contacts.scheme
    assert scheme is not None
    assert scheme.root.background == "bg-1"
    assert len(scheme.root.hotspots) == 1
    spot = scheme.root.hotspots[0]
    assert spot.id == "hotspot-1"
    assert spot.shape == HotspotShape(x=0.1, y=0.2, w=0.3, h=0.4)
    assert spot.label == "Спальное"
    assert spot.reveal_text == "скученность"
    assert spot.reveal_assets == ("z1",)
    assert spot.child is None


def test_build_contacts_preserves_hotspot_icon() -> None:
    """Ключ иконки из draft попадает в доменный Hotspot."""
    contacts = ContactsDraft(
        scheme=AssetRef("scheme", "", data=b"PNG"),
        hotspots=(
            HotspotDraft(
                x=0.1,
                y=0.2,
                w=0.3,
                h=0.4,
                label="Медпункт",
                icon="medical",
            ),
        ),
    )

    stage = build_case(
        CaseDraft(case_id="case-icon", title="Case", contacts=contacts)
    ).contacts

    assert stage.scheme is not None
    assert stage.scheme.root.hotspots[0].icon == "medical"


def test_build_case_environment_hotspots() -> None:
    """``environment`` с фоном и зоной → плоский ``Hotspot`` в ``scheme.root.hotspots``."""
    environment = EnvironmentDraft(
        scheme=AssetRef("bg-2", "/p"),
        hotspots=(
            HotspotDraft(
                0.5,
                0.6,
                0.2,
                0.1,
                label="Пищеблок",
                reveal_text="нарушение",
                reveal_assets=(AssetRef("z2", "/pz"),),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-he", environment=environment))

    scheme = case.environment.scheme
    assert scheme is not None
    assert scheme.root.background == "bg-2"
    assert len(scheme.root.hotspots) == 1
    spot = scheme.root.hotspots[0]
    assert spot.id == "hotspot-1"
    assert spot.shape == HotspotShape(x=0.5, y=0.6, w=0.2, h=0.1)
    assert spot.label == "Пищеблок"
    assert spot.reveal_text == "нарушение"
    assert spot.reveal_assets == ("z2",)
    assert spot.child is None


def test_build_case_contacts_hotspots_ignored_without_scheme() -> None:
    """Фон ``None`` → схема ``None``, зоны игнорируются (зона без фона недостижима)."""
    contacts = ContactsDraft(
        scheme=None,
        hotspots=(HotspotDraft(0.1, 0.2, 0.3, 0.4, label="x"),),
    )
    case = build_case(CaseDraft(case_id="case-hn", contacts=contacts))
    assert case.contacts.scheme is None


def test_build_case_environment_hotspots_ignored_without_scheme() -> None:
    """Фон ``None`` у среды → схема ``None``, зоны игнорируются."""
    environment = EnvironmentDraft(
        scheme=None,
        hotspots=(HotspotDraft(0.1, 0.2, 0.3, 0.4),),
    )
    case = build_case(CaseDraft(case_id="case-hen", environment=environment))
    assert case.environment.scheme is None


def test_build_case_hotspots_round_trip_to_dict() -> None:
    """round-trip: зоны контактов и среды сохраняются через ``to_dict`` → ``from_dict``."""
    contacts = ContactsDraft(
        scheme=AssetRef("bg-1", "/p"),
        hotspots=(
            HotspotDraft(
                0.1,
                0.2,
                0.3,
                0.4,
                label="A",
                reveal_text="t",
                reveal_assets=(AssetRef("z1", "/pz"),),
            ),
        ),
    )
    environment = EnvironmentDraft(
        scheme=AssetRef("bg-2", "/p"),
        hotspots=(HotspotDraft(0.0, 0.0, 1.0, 1.0, label="B"),),
    )
    case = build_case(
        CaseDraft(case_id="case-hrt", contacts=contacts, environment=environment)
    )
    restored = Case.from_dict(case.to_dict())
    assert restored.contacts == case.contacts
    assert restored.environment == case.environment


# --- Вложенный интерьерный вид зоны (R2.1-A): рекурсивный child ---


def test_build_case_contacts_nested_child_view() -> None:
    """Зона с child (фон + вложенная reveal-зона) → ``child`` — ``SchemeView`` с её зоной."""
    contacts = ContactsDraft(
        scheme=AssetRef("bg-root", "/p"),
        hotspots=(
            HotspotDraft(
                0.1,
                0.2,
                0.3,
                0.4,
                label="Казарма",
                child=SchemeViewDraft(
                    background=AssetRef("bg-child", "/pc"),
                    caption="Интерьер казармы",
                    hotspots=(
                        HotspotDraft(
                            0.5,
                            0.5,
                            0.2,
                            0.2,
                            label="Койка",
                            reveal_text="скученность",
                            reveal_assets=(AssetRef("zc1", "/pzc"),),
                        ),
                    ),
                ),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-nest-c", contacts=contacts))

    scheme = case.contacts.scheme
    assert scheme is not None
    child = scheme.root.hotspots[0].child
    assert isinstance(child, SchemeView)
    assert child.background == "bg-child"  # фон свёрнут в asset_id
    assert child.caption == "Интерьер казармы"
    assert len(child.hotspots) == 1
    inner = child.hotspots[0]
    assert inner.id == "hotspot-1"  # независимая нумерация вложенного вида с 1
    assert inner.label == "Койка"
    assert inner.reveal_text == "скученность"
    assert inner.reveal_assets == ("zc1",)
    assert inner.child is None


def test_build_case_environment_nested_child_view() -> None:
    """То же для среды: зона с child → вложенный ``SchemeView`` со своей зоной."""
    environment = EnvironmentDraft(
        scheme=AssetRef("bg-root-e", "/p"),
        hotspots=(
            HotspotDraft(
                0.0,
                0.0,
                0.5,
                0.5,
                label="Пищеблок",
                child=SchemeViewDraft(
                    background=AssetRef("bg-child-e", "/pc"),
                    caption="Цех",
                    hotspots=(HotspotDraft(0.1, 0.1, 0.2, 0.2, label="Котёл"),),
                ),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-nest-e", environment=environment))

    scheme = case.environment.scheme
    assert scheme is not None
    child = scheme.root.hotspots[0].child
    assert isinstance(child, SchemeView)
    assert child.background == "bg-child-e"
    assert child.caption == "Цех"
    assert len(child.hotspots) == 1
    assert child.hotspots[0].label == "Котёл"


def test_build_case_nested_child_without_background_dropped() -> None:
    """Вложенный вид без фона → ``child`` зоны схлопывается в ``None`` (вид недостижим)."""
    contacts = ContactsDraft(
        scheme=AssetRef("bg-root", "/p"),
        hotspots=(
            HotspotDraft(
                0.1,
                0.2,
                0.3,
                0.4,
                label="Казарма",
                child=SchemeViewDraft(
                    background=None,
                    hotspots=(HotspotDraft(0.5, 0.5, 0.2, 0.2, label="Койка"),),
                ),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-nest-nb", contacts=contacts))

    scheme = case.contacts.scheme
    assert scheme is not None
    assert scheme.root.hotspots[0].child is None


def test_build_case_nested_child_round_trip_to_dict() -> None:
    """Трёхуровневая вложенность собирается рекурсивно и переживает ``to_dict`` → ``from_dict``."""
    contacts = ContactsDraft(
        scheme=AssetRef("bg-l0", "/p"),
        hotspots=(
            HotspotDraft(
                0.1,
                0.1,
                0.2,
                0.2,
                label="L1",
                child=SchemeViewDraft(
                    background=AssetRef("bg-l1", "/p1"),
                    caption="Уровень 1",
                    hotspots=(
                        HotspotDraft(
                            0.2,
                            0.2,
                            0.2,
                            0.2,
                            label="L2",
                            child=SchemeViewDraft(
                                background=AssetRef("bg-l2", "/p2"),
                                caption="Уровень 2",
                                hotspots=(HotspotDraft(0.3, 0.3, 0.2, 0.2, label="L3"),),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-nest-rt", contacts=contacts))

    # Факт рекурсии: три уровня собрались и доходят до самого глубокого вида.
    scheme = case.contacts.scheme
    assert scheme is not None
    level1 = scheme.root.hotspots[0].child
    assert level1 is not None
    level2 = level1.hotspots[0].child
    assert level2 is not None
    assert level2.background == "bg-l2"
    assert level2.hotspots[0].label == "L3"
    assert level2.hotspots[0].child is None

    restored = Case.from_dict(case.to_dict())
    assert restored.contacts == case.contacts


# --- Этапы 5–6: оценка СЭС и окончательный диагноз ---


def test_build_case_without_ses_and_final_default_stages() -> None:
    """``CaseDraft`` без ses/final → дефолтные пустые этапы 5 и 6."""
    case = build_case(CaseDraft(case_id="case-sf"))
    assert case.ses == StageSes()
    assert case.final == StageFinal()


def test_build_case_ses_level_choice_and_documents() -> None:
    """``ses`` → поле выбора уровня (CHOICE → ``ChoiceMatch``), поиск и документы как заданы."""
    ses = SesDraft(
        intro="Оцените СЭС",
        search=SearchDraft(
            entries=(SearchEntryDraft(triggers=SynonymSetDraft(canonical="вспышка")),),
        ),
        level_choice=FieldDraft(
            label="Уровень СЭС",
            field_type="choice",
            choice_options=(
                "благополучное",
                "неустойчивое",
                "неблагополучное",
                "чрезвычайное",
            ),
            choice_correct=("чрезвычайное",),
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Выберите Прил. 22",
                options=(DocumentOptionDraft(title="Приложение 22"),),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-ses", ses=ses))

    level = case.ses.level_choice
    assert level is not None
    assert level.id == "field-1"
    assert level.type is FieldType.CHOICE
    assert level.label == "Уровень СЭС"
    assert isinstance(level.rule, ChoiceMatch)
    assert level.rule.correct == ("чрезвычайное",)
    assert level.options == (
        "благополучное",
        "неустойчивое",
        "неблагополучное",
        "чрезвычайное",
    )

    search = case.ses.search
    assert search is not None
    assert search.entries[0].triggers.canonical == "вспышка"
    assert len(case.ses.documents) == 1
    assert case.ses.documents[0].id == "doc-1"
    assert case.ses.documents[0].prompt == "Выберите Прил. 22"


def test_build_case_ses_level_choice_none_when_draft_none() -> None:
    """``level_choice=None`` в драфте → ``case.ses.level_choice`` равен ``None``."""
    case = build_case(CaseDraft(case_id="case-sn", ses=SesDraft(level_choice=None)))
    assert case.ses.level_choice is None


def test_build_case_final_timelines_documents_search() -> None:
    """``final`` → таймлайны (``tl-<i>``), документы и поиск; пустые таймлайны отброшены."""
    final = FinalDraft(
        intro="Окончательный диагноз",
        search=SearchDraft(
            entries=(SearchEntryDraft(triggers=SynonymSetDraft(canonical="источник")),),
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Выберите акт",
                options=(DocumentOptionDraft(title="Акт расследования"),),
            ),
        ),
        timelines=(
            TimelineDraft(title="", events=()),  # пустой — отбрасывается
            TimelineDraft(
                title="Очаг",
                events=(("2026-06-01", "Завоз"), ("2026-06-10", "Снятие")),
            ),
        ),
    )
    case = build_case(CaseDraft(case_id="case-fin", final=final))

    assert len(case.final.timelines) == 1
    timeline = case.final.timelines[0]
    assert timeline.id == "tl-1"
    assert timeline.title == "Очаг"
    assert timeline.events == (("2026-06-01", "Завоз"), ("2026-06-10", "Снятие"))

    search = case.final.search
    assert search is not None
    assert search.entries[0].triggers.canonical == "источник"
    assert len(case.final.documents) == 1
    assert case.final.documents[0].options[0].title == "Акт расследования"


def test_build_case_final_keeps_timeline_with_events_but_blank_title() -> None:
    """Таймлайн с пустым заголовком, но с событиями — сохраняется (id ``tl-1``)."""
    final = FinalDraft(
        timelines=(TimelineDraft(title="   ", events=(("2026-06-01", "Завоз"),)),)
    )
    case = build_case(CaseDraft(case_id="case-ft", final=final))
    assert len(case.final.timelines) == 1
    assert case.final.timelines[0].id == "tl-1"
    assert case.final.timelines[0].events == (("2026-06-01", "Завоз"),)


def test_build_case_ses_final_round_trip_to_dict() -> None:
    """round-trip: build_case(...).to_dict() → Case.from_dict(...) сохраняет ses и final."""
    ses = SesDraft(
        level_choice=FieldDraft(
            label="Уровень",
            field_type="choice",
            choice_options=("благополучное", "чрезвычайное"),
            choice_correct=("чрезвычайное",),
        ),
    )
    final = FinalDraft(
        timelines=(TimelineDraft(title="Очаг", events=(("2026-06-01", "Завоз"),)),),
    )
    case = build_case(CaseDraft(case_id="case-rt56", ses=ses, final=final))
    restored = Case.from_dict(case.to_dict())
    assert restored.ses == case.ses
    assert restored.final == case.final


# --- Фиксы коллапса пустого и непокрытые инварианты (адресный ревью) ---


def test_field_is_blank_by_type() -> None:
    """``_field_is_blank``: пусто, когда нет подписи И нет значения правила по типу."""
    assert _field_is_blank(FieldDraft(label="  ", field_type="text"))
    assert _field_is_blank(FieldDraft(label="", field_type="number"))
    assert _field_is_blank(FieldDraft(label="", field_type="date"))
    assert _field_is_blank(FieldDraft(label="", field_type="choice"))
    # Непустая подпись → не пусто.
    assert not _field_is_blank(FieldDraft(label="Доза", field_type="number"))
    # Непустое значение правила по своему типу → не пусто.
    assert not _field_is_blank(
        FieldDraft(label="", field_type="text", keywords=SynonymSetDraft("сыпь"))
    )
    assert not _field_is_blank(
        FieldDraft(label="", field_type="date", date_value="2026-06-01")
    )
    assert not _field_is_blank(
        FieldDraft(label="", field_type="choice", choice_correct=("a",))
    )
    # Неизвестный тип — НЕ считается пустым.
    assert not _field_is_blank(FieldDraft(label="", field_type="bogus"))


def test_build_case_ses_level_choice_collapses_empty_choice() -> None:
    """Пустое CHOICE-поле уровня (нет подписи и верных) → ``level_choice`` равен ``None``."""
    ses = SesDraft(level_choice=FieldDraft(label="  ", field_type="choice"))
    case = build_case(CaseDraft(case_id="case-lc", ses=ses))
    assert case.ses.level_choice is None


def test_build_case_ses_level_choice_collapses_empty_text() -> None:
    """Пустое TEXT-поле уровня (нет подписи и ключевых слов) → ``level_choice`` равен ``None``."""
    ses = SesDraft(
        level_choice=FieldDraft(
            label="", field_type="text", keywords=SynonymSetDraft("")
        )
    )
    case = build_case(CaseDraft(case_id="case-lt", ses=ses))
    assert case.ses.level_choice is None


def test_build_case_documents_drops_blank_template_field() -> None:
    """Пустое поле шаблона отбрасывается; оставшимся id ``field-<i>`` без дыр."""
    task = DocumentTaskDraft(
        prompt="Выберите акт",
        options=(
            DocumentOptionDraft(
                title="Акт",
                is_correct=True,
                template=TemplateDraft(
                    title="Шаблон",
                    fields=(
                        FieldDraft(
                            label="Дата", field_type="date", date_value="2026-06-01"
                        ),
                        FieldDraft(
                            label="", field_type="text", keywords=SynonymSetDraft("")
                        ),
                    ),
                ),
            ),
        ),
    )
    clinical = ClinicalDraft(documents=(task,))
    case = build_case(CaseDraft(case_id="case-bf", clinical=clinical))

    template = case.clinical.documents[0].options[0].template
    assert template is not None
    assert len(template.fields) == 1
    assert template.fields[0].id == "field-1"
    assert template.fields[0].label == "Дата"


def test_build_case_documents_blank_number_field_does_not_raise() -> None:
    """Пустое NUMBER-поле шаблона отбрасывается, а не роняет сборку через ``ValueError``."""
    task = DocumentTaskDraft(
        prompt="Выберите акт",
        options=(
            DocumentOptionDraft(
                title="Акт",
                is_correct=True,
                template=TemplateDraft(
                    fields=(
                        FieldDraft(label="", field_type="number", number_value=""),
                    ),
                ),
            ),
        ),
    )
    clinical = ClinicalDraft(documents=(task,))
    case = build_case(CaseDraft(case_id="case-bn", clinical=clinical))

    template = case.clinical.documents[0].options[0].template
    assert template is not None
    assert template.fields == ()


def test_build_field_negative_ndigits_raises() -> None:
    """Отрицательное число знаков округления → ``ValueError``."""
    with pytest.raises(ValueError, match="отрицательным"):
        _build_field(
            FieldDraft(
                label="N",
                field_type="number",
                number_value="1",
                number_ndigits="-2",
            ),
            1,
        )


def test_build_case_patients_stage_has_no_intro_or_search() -> None:
    """Пиннинг (W1): этап «Пациенты» намеренно без stage-level intro и search."""
    case = build_case(
        CaseDraft(
            case_id="case-p",
            patients=(PatientDraft(title="Пациент 1"),),
        )
    )
    assert case.patients.intro == ""
    assert case.patients.search is None


def test_build_field_choice_correct_outside_options_kept() -> None:
    """Пиннинг (W4/K2): ``choice_correct`` вне ``choice_options`` собирается без валидации."""
    field = _build_field(
        FieldDraft(
            label="Уровень",
            field_type="choice",
            choice_options=("благополучное", "чрезвычайное"),
            choice_correct=("несуществующее",),
        ),
        1,
    )
    assert isinstance(field.rule, ChoiceMatch)
    assert field.rule.correct == ("несуществующее",)
    assert field.options == ("благополучное", "чрезвычайное")


def test_build_case_stage_intros_round_trip() -> None:
    """intro этапов environment/ses/final сохраняется через ``to_dict`` → ``from_dict``."""
    draft = CaseDraft(
        case_id="case-intro",
        environment=EnvironmentDraft(intro="Осмотр среды"),
        ses=SesDraft(intro="Оценка СЭС"),
        final=FinalDraft(intro="Окончательный диагноз"),
    )
    case = build_case(draft)
    restored = Case.from_dict(case.to_dict())
    assert restored.environment.intro == "Осмотр среды"
    assert restored.ses.intro == "Оценка СЭС"
    assert restored.final.intro == "Окончательный диагноз"
