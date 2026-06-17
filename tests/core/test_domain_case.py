"""Тесты доменной модели Case/Stage (FEATURE-02): round-trip to_dict/from_dict,
интеграция с кодеком .educase, фиксированный порядок этапов, строгий поиск."""
from __future__ import annotations

from pathlib import Path

from educase_core.domain import (
    AssetKind,
    AssetRef,
    BranchOption,
    BranchPoint,
    Case,
    CaseMeta,
    ChoiceMatch,
    DateMatch,
    DocumentField,
    DocumentOption,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    InspectionCheck,
    KeywordSearch,
    NumberMatch,
    PatientCard,
    SchemeDocument,
    SchemeView,
    SearchEntry,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StageKind,
    StagePatients,
    StageSes,
    SynonymSet,
    TextMatch,
    Timeline,
)
from educase_core.infrastructure.archive.codec import read_educase, write_educase


def _rich_case() -> Case:
    """Богатый кейс: все шесть этапов заполнены, документ с обманкой, выбор уровня СЭС,
    таймлайн и реестр ассетов."""
    fever = SynonymSet(canonical="температура", synonyms=("жар", "лихорадка"))
    diarrhea = SynonymSet(canonical="диарея", synonyms=("понос",))

    patients = StagePatients(
        intro="Поступили больные",
        search=KeywordSearch(
            entries=(
                SearchEntry(
                    id="p-fever",
                    triggers=fever,
                    reveal_text="Высокая температура у троих",
                    reveal_assets=("photo-1",),
                ),
            ),
        ),
        patients=(
            PatientCard(
                id="pat-1",
                title="Рядовой Иванов",
                fields=(("Диагноз", "ОКИ"), ("Возраст", "20")),
                assets=("photo-1",),
            ),
        ),
    )

    clinical = StageClinical(
        intro="Поставьте диагноз",
        search=KeywordSearch(entries=(SearchEntry(id="c1", triggers=diarrhea),)),
        branch=BranchPoint(
            id="branch-1",
            prompt="Выберите путь",
            options=(
                BranchOption(id="b-ok", label="Кишечная инфекция", is_correct=True),
                BranchOption(id="b-bad", label="Пищевое отравление"),
            ),
        ),
        documents=(
            DocumentTask(
                id="dm4",
                prompt="Выберите документ",
                options=(
                    DocumentOption(
                        id="opt-dm4",
                        title="Внеочередное донесение ДМ4",
                        is_correct=True,
                        template=DocumentTemplate(
                            id="tpl-dm4",
                            title="ДМ4",
                            fields=(
                                DocumentField(
                                    id="f-diag",
                                    type=FieldType.TEXT,
                                    rule=TextMatch(keywords=diarrhea),
                                    label="Диагноз",
                                ),
                                DocumentField(
                                    id="f-count",
                                    type=FieldType.NUMBER,
                                    rule=NumberMatch(value=20.0, tolerance=0.5, ndigits=1),
                                    label="Число заболевших",
                                ),
                                DocumentField(
                                    id="f-date",
                                    type=FieldType.DATE,
                                    rule=DateMatch(value="2026-06-09"),
                                    label="Дата",
                                ),
                            ),
                        ),
                    ),
                    # Обманка: неправильный документ без шаблона.
                    DocumentOption(id="opt-decoy", title="Рапорт командира части"),
                ),
            ),
        ),
    )

    contacts = StageContacts(
        intro="Осмотрите контактных",
        scheme=SchemeDocument(root=SchemeView(background="scheme-barrack")),
        inspection=InspectionCheck(
            expected=(
                SynonymSet(canonical="скученность", synonyms=("теснота",)),
                SynonymSet(canonical="вентиляция"),
            ),
        ),
    )

    environment = StageEnvironment(
        intro="Осмотрите объекты",
        scheme=SchemeDocument(root=SchemeView(background="scheme-canteen")),
        photos=("photo-kitchen", "photo-store"),
        documents=(
            DocumentTask(
                id="gsen",
                options=(DocumentOption(id="opt-gsen", title="Акт ГСЭН", is_correct=True),),
            ),
        ),
        inspection=InspectionCheck(expected=(SynonymSet(canonical="антисанитария"),)),
    )

    ses = StageSes(
        intro="Оцените СЭС",
        search=KeywordSearch(entries=(SearchEntry(id="s1", triggers=fever),)),
        level_choice=DocumentField(
            id="ses-level",
            type=FieldType.CHOICE,
            rule=ChoiceMatch(correct=("Неблагополучное",)),
            label="Уровень СЭС",
            options=("Благополучное", "Неустойчивое", "Неблагополучное", "Чрезвычайное"),
        ),
        documents=(
            DocumentTask(
                id="plan",
                options=(DocumentOption(id="opt-plan", title="План + приказ", is_correct=True),),
            ),
        ),
    )

    final = StageFinal(
        intro="Заключительный диагноз",
        search=KeywordSearch(entries=(SearchEntry(id="f1", triggers=diarrhea),)),
        documents=(
            DocumentTask(
                id="akt",
                options=(
                    DocumentOption(id="opt-akt", title="Акт расследования очага", is_correct=True),
                ),
            ),
        ),
        timelines=(
            Timeline(
                id="tl-1",
                title="Сроки наблюдения",
                events=(("2026-06-09", "Начало"), ("2026-06-16", "Контроль")),
            ),
        ),
    )

    return Case(
        meta=CaseMeta(
            id="case-1",
            title="Вспышка ОКИ",
            author="Преподаватель",
            nosology="Острая кишечная инфекция",
            unit_personnel=150,
            created_at="2026-06-09",
        ),
        patients=patients,
        clinical=clinical,
        contacts=contacts,
        environment=environment,
        ses=ses,
        final=final,
        assets=(
            AssetRef(id="photo-1", path="assets/photo-1.png", kind=AssetKind.PHOTO),
            AssetRef(id="scheme-barrack", path="assets/scheme-barrack.json", kind=AssetKind.SCHEME),
            AssetRef(id="doc-1", path="assets/doc-1.pdf", kind=AssetKind.DOCUMENT),
        ),
    )


def test_case_dict_round_trip() -> None:
    case = _rich_case()
    assert Case.from_dict(case.to_dict()) == case


def test_empty_case_round_trip() -> None:
    case = Case(CaseMeta("c0", "Пустой"))
    assert Case.from_dict(case.to_dict()) == case
    assert len(case.ordered()) == 6


def test_case_via_educase_archive(tmp_path: Path) -> None:
    case = _rich_case()
    dst = write_educase(case.to_dict(), tmp_path / "case")
    bundle = read_educase(dst)
    assert Case.from_dict(bundle.payload) == case


def test_stage_kinds_fixed() -> None:
    case = _rich_case()
    kinds = tuple(stage.KIND for stage in case.ordered())
    assert kinds == (
        StageKind.PATIENTS,
        StageKind.CLINICAL,
        StageKind.CONTACTS,
        StageKind.ENVIRONMENT,
        StageKind.SES,
        StageKind.FINAL,
    )


def test_strict_keyword_search_no_fuzzy() -> None:
    triggers = SynonymSet(canonical="температура", synonyms=("жар", "лихорадка"))
    search = KeywordSearch(
        entries=(SearchEntry(id="e1", triggers=triggers, reveal_text="t"),)
    )
    # Регистр и пробелы игнорируются нормализацией.
    assert search.find("  ТЕМПЕРАТУРА ") is not None
    assert search.find("Жар") is not None
    # Опечатка/обрезка и неточное совпадение — отвергаются (нет fuzzy).
    assert search.find("температур") is None
    assert search.find("температура тела") is None
