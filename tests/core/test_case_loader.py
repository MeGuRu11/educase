"""Round-trip L1: ``case_to_draft`` (домен → драфт) и источники байтов ассетов (Qt-free)."""
from __future__ import annotations

from pathlib import Path

from epicase_core.application.assets import read_asset_sources
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
    build_case,
)
from epicase_core.application.case_loader import case_to_draft
from epicase_core.application.cases import LoadedCase, load_case, save_case
from epicase_core.domain import Case, CaseMeta
from epicase_core.domain.scheme import Hotspot, HotspotShape, SchemeDocument, SchemeView
from epicase_core.domain.stages import PatientCard, StageContacts, StagePatients


def test_case_to_draft_round_trip(tmp_path: Path) -> None:
    """CaseDraft → .epicase → load_case → case_to_draft: мета, пациенты и ассеты сохранены."""
    draft = CaseDraft(
        case_id="case-l1",
        title="Вспышка ОКИ",
        author="Иванов",
        author_rank="полковник",
        nosology="Сальмонеллёз",
        unit_personnel=150,
        patients=(
            PatientDraft(
                title="Пациент 1",
                fields=(("Возраст", "25 лет"), ("Жалобы", "температура")),
                assets=(
                    AssetRef("p1-a.png", "", data=b"IMG-A"),
                    AssetRef("p1-b.png", "", data=b"IMG-B"),
                ),
            ),
            PatientDraft(title="Пациент 2", fields=(("Возраст", "30 лет"),)),
        ),
    )

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.epicase"
    save_case(case, dst, assets=assets)

    reloaded = case_to_draft(load_case(dst))

    # Мета.
    assert reloaded.case_id == "case-l1"
    assert reloaded.title == "Вспышка ОКИ"
    assert reloaded.author == "Иванов"
    assert reloaded.author_rank == "полковник"
    assert reloaded.nosology == "Сальмонеллёз"
    assert reloaded.unit_personnel == 150

    # Все шесть этапов обращаются всегда: пустые этапы → пустые драфты.
    assert reloaded.clinical == ClinicalDraft()
    assert reloaded.contacts == ContactsDraft()
    assert reloaded.environment == EnvironmentDraft()
    assert reloaded.ses == SesDraft()
    assert reloaded.final == FinalDraft()

    # Пациенты: заголовки и поля.
    assert [p.title for p in reloaded.patients] == ["Пациент 1", "Пациент 2"]
    assert reloaded.patients[0].fields == (
        ("Возраст", "25 лет"),
        ("Жалобы", "температура"),
    )
    assert reloaded.patients[1].fields == (("Возраст", "30 лет"),)
    assert reloaded.patients[1].assets == ()

    # Ассеты восстановлены из памяти: множество id и совпадение байтов.
    refs = reloaded.patients[0].assets
    assert {r.asset_id for r in refs} == {"p1-a.png", "p1-b.png"}
    by_id = {r.asset_id: r.data for r in refs}
    assert by_id["p1-a.png"] == b"IMG-A"
    assert by_id["p1-b.png"] == b"IMG-B"
    # Имя файла утрачено → display_name = asset_id; путь к файлу пуст.
    assert all(r.display_name == r.asset_id and r.source_path == "" for r in refs)


def test_case_to_draft_drops_assets_without_bytes() -> None:
    """Ссылка карточки без байтов в архиве (битая) отбрасывается при обращении."""
    case = Case(
        meta=CaseMeta(id="case-orphan"),
        patients=StagePatients(
            patients=(
                PatientCard(id="p1", title="П", assets=("present.png", "missing.png")),
            )
        ),
    )
    loaded = LoadedCase(case=case, assets={"present.png": b"OK"})

    reloaded = case_to_draft(loaded)
    refs = reloaded.patients[0].assets
    assert {r.asset_id for r in refs} == {"present.png"}
    assert refs[0].data == b"OK"


def _clinical_draft() -> ClinicalDraft:
    """Непустой ``ClinicalDraft`` со всеми элементами этапа 2 (поиск, ветка, документы).

    Шаблон верного документа покрывает поля ВСЕХ типов (text/number/date/choice); рядом —
    обманка без шаблона. Точка поиска тащит ассет (байты из памяти) и необязательность.
    """
    return ClinicalDraft(
        intro="Введение к клиническому этапу",
        search=SearchDraft(
            entries=(
                SearchEntryDraft(
                    triggers=SynonymSetDraft("температура", ("жар", "лихорадка")),
                    reveal_text="38.5",
                    reveal_assets=(AssetRef("cl-a.png", "", data=b"CLIMG"),),
                ),
            ),
            optional=True,
        ),
        branch=BranchDraft(
            prompt="Выберите дальнейший путь",
            options=(
                BranchOptionDraft("Верный путь", is_correct=True),
                BranchOptionDraft("Неверный путь", is_correct=False),
            ),
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Выберите правильный документ",
                options=(
                    DocumentOptionDraft(
                        title="Донесение ДМ-4",
                        is_correct=True,
                        template=TemplateDraft(
                            title="Донесение",
                            fields=(
                                FieldDraft(
                                    label="Возбудитель",
                                    field_type="text",
                                    keywords=SynonymSetDraft(
                                        "сальмонелла", ("salmonella",)
                                    ),
                                ),
                                FieldDraft(
                                    label="Число заболевших",
                                    field_type="number",
                                    number_value="25",
                                    number_tolerance="2",
                                    number_ndigits="0",
                                ),
                                FieldDraft(
                                    label="Дата вспышки",
                                    field_type="date",
                                    date_value="01.06.2026",
                                ),
                                FieldDraft(
                                    label="Уровень СЭС",
                                    field_type="choice",
                                    choice_options=("низкий", "высокий"),
                                    choice_correct=("высокий",),
                                ),
                            ),
                        ),
                    ),
                    DocumentOptionDraft(title="Неверный документ", is_correct=False),
                ),
            ),
        ),
    )


def test_clinical_round_trip(tmp_path: Path) -> None:
    """Этап 2: CaseDraft → .epicase → load → case_to_draft даёт симметричный домен этапа 2."""
    draft = CaseDraft(case_id="case-l2", title="Клин", clinical=_clinical_draft())

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.epicase"
    save_case(case, dst, assets=assets)

    reloaded = case_to_draft(load_case(dst))

    # ГЛАВНЫЙ инвариант: повторная сборка из reloaded даёт ТОТ ЖЕ доменный этап 2 — доменное
    # равенство ловит любую асимметрию чисел, правил, обманок и ассетов.
    assert build_case(reloaded).clinical == build_case(draft).clinical

    # Точечные проверки на reloaded.
    clinical = reloaded.clinical
    assert clinical is not None
    assert clinical.intro == "Введение к клиническому этапу"
    assert clinical.search.optional is True

    # Ветка: число опций и верный выбор.
    assert len(clinical.branch.options) == 2
    assert [o.is_correct for o in clinical.branch.options] == [True, False]

    # Типы полей шаблона верного документа — в исходном порядке.
    correct = clinical.documents[0].options[0]
    assert correct.is_correct is True
    assert [f.field_type for f in correct.template.fields] == [
        "text",
        "number",
        "date",
        "choice",
    ]

    # reveal_assets точки поиска: байты восстановлены из архива.
    entry_refs = clinical.search.entries[0].reveal_assets
    assert len(entry_refs) == 1
    assert entry_refs[0].data == b"CLIMG"

    # Шаблон обманки пуст (template=None в домене → пустой TemplateDraft).
    decoy = clinical.documents[0].options[1]
    assert decoy.is_correct is False
    assert decoy.template == TemplateDraft()


def test_document_fields_mode_and_reference_assets_round_trip(tmp_path: Path) -> None:
    """FIELDS и reference_assets переживают build_case → .epicase → case_to_draft."""
    task = DocumentTaskDraft(
        prompt="Заполните поля формы",
        reference_assets=("ref-1", "ref-2"),
        options=(
            DocumentOptionDraft(
                title="Форма 23",
                is_correct=True,
                template=TemplateDraft(title="Форма 23", fill_mode="fields"),
            ),
            DocumentOptionDraft(title="Обманка", is_correct=False),
        ),
    )
    draft = CaseDraft(
        case_id="case-fm", title="Док", clinical=ClinicalDraft(documents=(task,))
    )

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.epicase"
    save_case(case, dst, assets=assets)
    reloaded = case_to_draft(load_case(dst))

    # Доменный инвариант симметрии: повторная сборка даёт тот же этап.
    assert build_case(reloaded).clinical == build_case(draft).clinical

    clinical = reloaded.clinical
    assert clinical is not None
    reloaded_task = clinical.documents[0]
    assert reloaded_task.reference_assets == ("ref-1", "ref-2")
    assert reloaded_task.options[0].template.fill_mode == "fields"


def test_document_attachment_mode_and_allow_multiple_round_trip(tmp_path: Path) -> None:
    """ADR-015: attachment и allow_multiple переживают build_case → .epicase → case_to_draft."""
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
            DocumentOptionDraft(title="Обманка", is_correct=False),
        ),
    )
    draft = CaseDraft(
        case_id="case-att", title="Док", clinical=ClinicalDraft(documents=(task,))
    )

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.epicase"
    save_case(case, dst, assets=assets)
    reloaded = case_to_draft(load_case(dst))

    # Доменный инвариант симметрии: повторная сборка даёт тот же этап.
    assert build_case(reloaded).clinical == build_case(draft).clinical

    clinical = reloaded.clinical
    assert clinical is not None
    reloaded_template = clinical.documents[0].options[0].template
    assert reloaded_template.fill_mode == "attachment"
    assert reloaded_template.allow_multiple is True


def _contacts_draft() -> ContactsDraft:
    """Непустой ``ContactsDraft``: схема с фоном и 2 зонами (одна с вложенным видом), осмотр.

    Первая зона несёт вложенный интерьерный вид (свой фон + 1 зона) — проверяем рекурсию;
    вторая зона плоская. Все ассеты — байты из памяти (``AssetRef`` с ``data``).
    """
    return ContactsDraft(
        intro="Введение к этапу контактов",
        scheme=AssetRef("ct-bg.png", "", data=b"CTBG"),
        hotspots=(
            HotspotDraft(
                x=0.1,
                y=0.2,
                w=0.3,
                h=0.25,
                label="Казарма",
                reveal_text="Спальное помещение",
                reveal_assets=(AssetRef("ct-z1.png", "", data=b"CTZ1"),),
                child=SchemeViewDraft(
                    background=AssetRef("ct-int.png", "", data=b"CTINT"),
                    caption="Интерьер казармы",
                    hotspots=(
                        HotspotDraft(
                            x=0.4,
                            y=0.5,
                            w=0.2,
                            h=0.2,
                            label="Койка",
                            reveal_text="Спальное место",
                            reveal_assets=(AssetRef("ct-int-z1.png", "", data=b"CTIZ"),),
                        ),
                    ),
                ),
            ),
            HotspotDraft(
                x=0.6,
                y=0.55,
                w=0.25,
                h=0.3,
                label="Пищеблок",
                reveal_text="Кухня",
            ),
        ),
        inspection=InspectionDraft(
            groups=(
                SynonymSetDraft("вентиляция", ("проветривание",)),
                SynonymSetDraft("скученность", ("теснота",)),
            )
        ),
    )


def _environment_draft() -> EnvironmentDraft:
    """Непустой ``EnvironmentDraft``: схема с фоном и 2 зонами, 2 фото, 1 документ, осмотр."""
    return EnvironmentDraft(
        intro="Введение к этапу среды",
        scheme=AssetRef("env-bg.png", "", data=b"ENVBG"),
        hotspots=(
            HotspotDraft(
                x=0.15,
                y=0.15,
                w=0.2,
                h=0.2,
                label="Колодец",
                reveal_text="Источник воды",
                reveal_assets=(AssetRef("env-z1.png", "", data=b"ENVZ1"),),
            ),
            HotspotDraft(
                x=0.5,
                y=0.5,
                w=0.3,
                h=0.2,
                label="Склад",
                reveal_text="Хранение продуктов",
            ),
        ),
        photos=(
            AssetRef("env-p1.png", "", data=b"ENVP1"),
            AssetRef("env-p2.png", "", data=b"ENVP2"),
        ),
        documents=(
            DocumentTaskDraft(
                prompt="Выберите документ среды",
                options=(
                    DocumentOptionDraft(
                        title="Протокол отбора проб",
                        is_correct=True,
                        template=TemplateDraft(
                            title="Протокол",
                            fields=(
                                FieldDraft(
                                    label="Объект",
                                    field_type="text",
                                    keywords=SynonymSetDraft("вода", ("h2o",)),
                                ),
                            ),
                        ),
                    ),
                    DocumentOptionDraft(title="Обманка", is_correct=False),
                ),
            ),
        ),
        inspection=InspectionDraft(
            groups=(
                SynonymSetDraft("загрязнение", ("контаминация",)),
                SynonymSetDraft("санитария"),
            )
        ),
    )


def test_case_to_draft_preserves_nested_hotspot_icon() -> None:
    """Domain → draft сохраняет ключ иконки и во вложенном виде."""
    case = Case(
        meta=CaseMeta(id="case-icons", title="Case"),
        contacts=StageContacts(
            scheme=SchemeDocument(
                root=SchemeView(
                    background="root",
                    hotspots=(
                        Hotspot(
                            id="outer",
                            shape=HotspotShape(0.1, 0.1, 0.2, 0.2),
                            icon="barracks",
                            child=SchemeView(
                                background="child",
                                hotspots=(
                                    Hotspot(
                                        id="inner",
                                        shape=HotspotShape(0.2, 0.2, 0.3, 0.3),
                                        icon="cold_storage",
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        ),
    )

    draft = case_to_draft(
        LoadedCase(case=case, assets={"root": b"ROOT", "child": b"CHILD"})
    )

    assert draft.contacts is not None
    assert draft.contacts.hotspots[0].icon == "barracks"
    child = draft.contacts.hotspots[0].child
    assert child is not None
    assert child.hotspots[0].icon == "cold_storage"


def test_contacts_environment_round_trip(tmp_path: Path) -> None:
    """Этапы 3–4: CaseDraft → .epicase → case_to_draft даёт симметричный домен (рекурсия схемы)."""
    draft = CaseDraft(
        case_id="case-l3",
        title="Очаг",
        contacts=_contacts_draft(),
        environment=_environment_draft(),
    )

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.epicase"
    save_case(case, dst, assets=assets)

    reloaded = case_to_draft(load_case(dst))

    # ГЛАВНЫЙ инвариант: повторная сборка из reloaded даёт ТЕ ЖЕ доменные этапы 3–4 — доменное
    # равенство ловит асимметрию геометрии, вложенности, ассетов, инспекции и фото.
    assert build_case(reloaded).contacts == build_case(draft).contacts
    assert build_case(reloaded).environment == build_case(draft).environment

    # Точечно — контакты: фон и зоны восстановлены.
    contacts = reloaded.contacts
    assert contacts is not None
    assert contacts.intro == "Введение к этапу контактов"
    assert contacts.scheme is not None
    assert contacts.scheme.asset_id == "ct-bg.png"
    assert contacts.scheme.data == b"CTBG"
    assert len(contacts.hotspots) == 2

    # Первая зона несёт вложенный вид (фон + 1 зона); вторая — плоская.
    nested = contacts.hotspots[0].child
    assert nested is not None
    assert nested.background is not None
    assert nested.background.data == b"CTINT"
    assert len(nested.hotspots) == 1
    assert contacts.hotspots[1].child is None

    # reveal_assets зоны: байты восстановлены из архива.
    z1_refs = contacts.hotspots[0].reveal_assets
    assert len(z1_refs) == 1
    assert z1_refs[0].data == b"CTZ1"

    # Осмотр: 2 группы.
    assert len(contacts.inspection.groups) == 2

    # Точечно — среда: фон, зоны, фото и документы.
    env = reloaded.environment
    assert env is not None
    assert env.scheme is not None
    assert env.scheme.asset_id == "env-bg.png"
    assert len(env.hotspots) == 2
    assert {p.asset_id for p in env.photos} == {"env-p1.png", "env-p2.png"}
    assert {p.data for p in env.photos} == {b"ENVP1", b"ENVP2"}
    assert len(env.documents) == 1


def test_contacts_scheme_background_orphan_dropped() -> None:
    """Схема, чьи байты фона отсутствуют в архиве → схема и зоны отбрасываются (``None``, ())."""
    case = Case(
        meta=CaseMeta(id="case-orphan-scheme"),
        contacts=StageContacts(
            scheme=SchemeDocument(
                root=SchemeView(
                    background="missing-bg.png",
                    hotspots=(
                        Hotspot(id="hotspot-1", shape=HotspotShape(0.1, 0.1, 0.2, 0.2)),
                    ),
                )
            ),
        ),
    )
    loaded = LoadedCase(case=case, assets={})  # байтов фона в архиве нет

    reloaded = case_to_draft(loaded)
    assert reloaded.contacts is not None
    # Без восстановленного фона зоны недостижимы — как build пакует их лишь при фоне.
    assert reloaded.contacts.scheme is None
    assert reloaded.contacts.hotspots == ()


def test_nested_scheme_background_orphan_dropped() -> None:
    """Вложенный вид без байтов фона в архиве → child схлопывается в None (orphan глубины)."""
    case = Case(
        meta=CaseMeta(id="case-orphan-nested"),
        contacts=StageContacts(
            scheme=SchemeDocument(
                root=SchemeView(
                    background="root-bg.png",
                    hotspots=(
                        Hotspot(
                            id="hotspot-1",
                            shape=HotspotShape(0.1, 0.1, 0.2, 0.2),
                            child=SchemeView(
                                background="missing-child-bg.png",
                                caption="Интерьер",
                                hotspots=(
                                    Hotspot(
                                        id="hotspot-1",
                                        shape=HotspotShape(0.3, 0.3, 0.2, 0.2),
                                    ),
                                ),
                            ),
                        ),
                    ),
                )
            ),
        ),
    )
    # Корневой фон в архиве есть, фона вложенного вида — нет.
    loaded = LoadedCase(case=case, assets={"root-bg.png": b"ROOT"})

    reloaded = case_to_draft(loaded)
    assert reloaded.contacts is not None
    assert reloaded.contacts.scheme is not None  # корневой фон восстановлен
    assert len(reloaded.contacts.hotspots) == 1
    # Вложенный вид без восстановимого фона схлопнут в None — симметрично корню (depth >= 2).
    assert reloaded.contacts.hotspots[0].child is None


def test_case_to_draft_round_trip_ses_final(tmp_path: Path) -> None:
    """СЭС и Финал обращаются: build_case(reloaded).<stage> == build_case(draft).<stage>."""
    draft = CaseDraft(
        case_id="case-l4",
        title="Кейс L4",
        ses=SesDraft(
            intro="Оцените СЭС",
            search=SearchDraft(
                entries=(
                    SearchEntryDraft(
                        triggers=SynonymSetDraft("приказ", ("распоряжение",)),
                        reveal_text="текст приказа",
                    ),
                )
            ),
            level_choice=FieldDraft(
                label="Уровень", field_type="number", number_value="2"
            ),
            documents=(
                DocumentTaskDraft(
                    prompt="Выберите акт",
                    options=(
                        DocumentOptionDraft(
                            title="Акт ГСЭН",
                            is_correct=True,
                            template=TemplateDraft(
                                title="Акт",
                                fields=(
                                    FieldDraft(
                                        label="Дата",
                                        field_type="date",
                                        date_value="01.06.2026",
                                    ),
                                ),
                            ),
                        ),
                        DocumentOptionDraft(title="Обманка"),
                    ),
                ),
            ),
        ),
        final=FinalDraft(
            intro="Окончательный диагноз",
            search=SearchDraft(
                entries=(
                    SearchEntryDraft(
                        triggers=SynonymSetDraft("вспышка"), reveal_text="..."
                    ),
                )
            ),
            documents=(
                DocumentTaskDraft(
                    prompt="Выберите акт расследования",
                    options=(
                        DocumentOptionDraft(
                            title="Акт расследования", is_correct=True
                        ),
                    ),
                ),
            ),
            timelines=(
                TimelineDraft(
                    title="Наблюдение",
                    events=(("01.06", "выявление"), ("03.06", "госпитализация")),
                ),
                TimelineDraft(title="Контроль", events=(("10.06", "снятие"),)),
            ),
        ),
    )

    case = build_case(draft)
    assets = read_asset_sources(draft)
    dst = tmp_path / "c.epicase"
    save_case(case, dst, assets=assets)
    reloaded = case_to_draft(load_case(dst))

    # Доменный инвариант симметрии.
    assert build_case(reloaded).ses == build_case(draft).ses
    assert build_case(reloaded).final == build_case(draft).final

    # Точечно (Optional -> assert до доступа, mypy strict).
    assert reloaded.ses is not None
    assert reloaded.ses.level_choice is not None
    assert reloaded.ses.level_choice.number_value == "2"
    assert reloaded.final is not None
    assert tuple(tl.title for tl in reloaded.final.timelines) == ("Наблюдение", "Контроль")
    assert reloaded.final.timelines[0].events == (
        ("01.06", "выявление"),
        ("03.06", "госпитализация"),
    )


def test_read_asset_sources_uses_data_then_file(tmp_path: Path) -> None:
    """read_asset_sources: ``AssetRef`` с ``data`` берёт байты из памяти; без ``data`` — файл."""
    src = tmp_path / "real.png"
    src.write_bytes(b"FROM-FILE")

    draft = CaseDraft(
        case_id="case-src",
        patients=(
            PatientDraft(
                title="П",
                assets=(
                    AssetRef("mem.png", "", data=b"FROM-MEMORY"),
                    AssetRef("file.png", str(src)),
                ),
            ),
        ),
    )
    assert read_asset_sources(draft) == {
        "mem.png": b"FROM-MEMORY",
        "file.png": b"FROM-FILE",
    }
