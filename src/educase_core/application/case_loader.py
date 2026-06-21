"""Обращение доменного ``Case`` в ``CaseDraft`` для правки (этот срез: мета + пациенты + этапы 2–4).

Зеркало ``case_builder`` (драфт → домен): здесь домен раскладывается обратно в «сырые»
``*Draft``-структуры UI, чтобы редактор мог открыть сохранённый кейс. Ассеты восстанавливаются
ИЗ ПАМЯТИ (байты из архива ``LoadedCase.assets``): путь к исходному файлу и его имя при
загрузке утрачены, поэтому ``AssetRef`` собирается с ``data=<байты>``, пустым ``source_path`` и
``display_name=asset_id`` (для показа в пикере этого достаточно). Этапы 2–4 (клинический,
контакты, среда) уже обращаются; этапы 5–6 пока не обращаются (остаются ``None``) — их добьют
следующие срезы. Чистые функции без I/O.
"""
from __future__ import annotations

from collections.abc import Mapping

from educase_core.application.case_builder import (
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
    HotspotDraft,
    InspectionDraft,
    PatientDraft,
    SchemeViewDraft,
    SearchDraft,
    SearchEntryDraft,
    SynonymSetDraft,
    TemplateDraft,
)
from educase_core.application.cases import LoadedCase
from educase_core.domain.documents import (
    ChoiceMatch,
    DateMatch,
    DocumentField,
    DocumentOption,
    DocumentTask,
    DocumentTemplate,
    FieldType,
    NumberMatch,
    TextMatch,
)
from educase_core.domain.scheme import Hotspot, SchemeDocument, SchemeView
from educase_core.domain.search import InspectionCheck, KeywordSearch, SynonymSet
from educase_core.domain.stages import (
    BranchPoint,
    PatientCard,
    StageClinical,
    StageContacts,
    StageEnvironment,
)


def _asset_ref(asset_id: str, assets: Mapping[str, bytes]) -> AssetRef:
    """Собрать ``AssetRef`` загруженного ассета: байты из памяти, имя файла = ``asset_id``.

    Имя исходного файла при загрузке утрачено — для показа в пикере подставляется ``asset_id``.
    Вызывается только для известных ``asset_id`` (наличие в ``assets`` проверяет вызывающий).
    """
    return AssetRef(
        asset_id=asset_id,
        source_path="",
        display_name=asset_id,
        data=assets[asset_id],
    )


def _patient_to_draft(card: PatientCard, assets: Mapping[str, bytes]) -> PatientDraft:
    """Обратить ``PatientCard`` в ``PatientDraft``: заголовок, поля, ссылки на ассеты по id.

    Ссылки на ассеты без байтов в архиве (битые) отбрасываются: восстановить их в пикере
    нечем, а пере-сохранение всё равно не нашло бы файл.
    """
    return PatientDraft(
        title=card.title,
        fields=card.fields,
        assets=tuple(_asset_ref(a, assets) for a in card.assets if a in assets),
    )


def _synset_to_draft(s: SynonymSet) -> SynonymSetDraft:
    """Обратить ``SynonymSet`` в ``SynonymSetDraft``: канонический термин + синонимы."""
    return SynonymSetDraft(canonical=s.canonical, synonyms=s.synonyms)


def _search_to_draft(
    ks: KeywordSearch | None, assets: Mapping[str, bytes]
) -> SearchDraft:
    """Обратить ``KeywordSearch`` в ``SearchDraft`` (``None`` → пустой ``SearchDraft``).

    Зеркало ``_build_search``: точки переносятся как есть (домен уже отбросил пустые при
    сборке), триггеры — через ``_synset_to_draft``, ``reveal_assets`` восстанавливаются из
    памяти через ``_asset_ref`` с отбрасыванием id без байтов (как для ассетов пациентов в L1).
    """
    if ks is None:
        return SearchDraft()
    return SearchDraft(
        entries=tuple(
            SearchEntryDraft(
                triggers=_synset_to_draft(entry.triggers),
                reveal_text=entry.reveal_text,
                reveal_assets=tuple(
                    _asset_ref(a, assets) for a in entry.reveal_assets if a in assets
                ),
            )
            for entry in ks.entries
        ),
        optional=ks.optional,
    )


def _branch_to_draft(bp: BranchPoint | None) -> BranchDraft:
    """Обратить ``BranchPoint`` в ``BranchDraft`` (``None`` → пустой ``BranchDraft``).

    Зеркало ``_build_branch``: формулировка и опции переносятся как есть (id опций генерит
    сборка — в драфте не воспроизводится).
    """
    if bp is None:
        return BranchDraft()
    return BranchDraft(
        prompt=bp.prompt,
        options=tuple(
            BranchOptionDraft(label=o.label, is_correct=o.is_correct)
            for o in bp.options
        ),
    )


def _num_to_str(x: float) -> str:
    """Число в строку для поля ввода: целое без хвоста (25.0 → "25"), иначе обычная строка."""
    return str(int(x)) if x.is_integer() else str(x)


def _field_to_draft(f: DocumentField) -> FieldDraft:
    """Обратить ``DocumentField`` в ``FieldDraft``: заполнить под-форму своего типа.

    Зеркало ``_build_field``: заполняются ТОЛЬКО параметры правила, соответствующего ``f.type``
    (остальные остаются дефолтами ``FieldDraft``). Тип правила сужается ``isinstance`` под
    ``f.type`` (домен гарантирует их согласованность) — этого требует mypy strict.
    """
    keywords = SynonymSetDraft("")
    number_value = ""
    number_tolerance = ""
    number_ndigits = ""
    date_value = ""
    choice_options: tuple[str, ...] = ()
    choice_correct: tuple[str, ...] = ()
    rule = f.rule
    if f.type is FieldType.TEXT and isinstance(rule, TextMatch):
        keywords = _synset_to_draft(rule.keywords)
    elif f.type is FieldType.NUMBER and isinstance(rule, NumberMatch):
        number_value = _num_to_str(rule.value)
        number_tolerance = "" if rule.tolerance == 0.0 else _num_to_str(rule.tolerance)
        number_ndigits = "" if rule.ndigits is None else str(rule.ndigits)
    elif f.type is FieldType.DATE and isinstance(rule, DateMatch):
        date_value = rule.value
    elif f.type is FieldType.CHOICE and isinstance(rule, ChoiceMatch):
        choice_options = f.options
        choice_correct = rule.correct
    return FieldDraft(
        label=f.label,
        field_type=f.type.value,
        required=f.required,
        keywords=keywords,
        number_value=number_value,
        number_tolerance=number_tolerance,
        number_ndigits=number_ndigits,
        date_value=date_value,
        choice_options=choice_options,
        choice_correct=choice_correct,
    )


def _template_to_draft(t: DocumentTemplate) -> TemplateDraft:
    """Обратить ``DocumentTemplate`` в ``TemplateDraft``: заголовок + поля (``_field_to_draft``)."""
    return TemplateDraft(
        title=t.title,
        fields=tuple(_field_to_draft(field) for field in t.fields),
    )


def _option_to_draft(o: DocumentOption) -> DocumentOptionDraft:
    """Обратить ``DocumentOption`` в ``DocumentOptionDraft``.

    Зеркало ``_build_documents``: шаблон есть только у верного варианта; у обманки
    (``template=None``) в драфт кладётся ПУСТОЙ ``TemplateDraft`` (при повторной сборке
    ``is_correct=False`` всё равно даст ``template=None``).
    """
    return DocumentOptionDraft(
        title=o.title,
        is_correct=o.is_correct,
        template=(
            _template_to_draft(o.template) if o.template is not None else TemplateDraft()
        ),
    )


def _task_to_draft(t: DocumentTask) -> DocumentTaskDraft:
    """Обратить ``DocumentTask`` в ``DocumentTaskDraft``: формулировка + варианты."""
    return DocumentTaskDraft(
        prompt=t.prompt,
        options=tuple(_option_to_draft(o) for o in t.options),
    )


def _clinical_to_draft(
    stage: StageClinical, assets: Mapping[str, bytes]
) -> ClinicalDraft:
    """Обратить этап 2 ``StageClinical`` в ``ClinicalDraft`` для правки.

    Зеркало ``build_clinical``: вступление, поиск (``_search_to_draft``), развилка
    (``_branch_to_draft``) и задания по документам (``_task_to_draft``).
    """
    return ClinicalDraft(
        intro=stage.intro,
        search=_search_to_draft(stage.search, assets),
        branch=_branch_to_draft(stage.branch),
        documents=tuple(_task_to_draft(t) for t in stage.documents),
    )


def _scheme_view_to_draft(
    view: SchemeView, assets: Mapping[str, bytes]
) -> SchemeViewDraft | None:
    """Обратить вложенный ``SchemeView`` в ``SchemeViewDraft`` (или ``None`` для orphan-вида).

    Зеркало ``_build_scheme_view`` (тот возвращает ``None`` у вида без фона): вид без
    восстановимого фона (id отсутствует в архиве) недостижим и схлопывается в ``None`` — та же
    orphan-логика, что и на КОРНЕ (``_scheme_fields``), на КАЖДОМ уровне вложенности. Иначе фон
    восстанавливается из памяти, подпись копируется, зоны обращаются ``_hotspot_to_draft``
    (рекурсия по ``child``).
    """
    if view.background is None or view.background not in assets:
        return None
    return SchemeViewDraft(
        background=_asset_ref(view.background, assets),
        caption=view.caption,
        hotspots=tuple(_hotspot_to_draft(h, assets) for h in view.hotspots),
    )


def _hotspot_to_draft(h: Hotspot, assets: Mapping[str, bytes]) -> HotspotDraft:
    """Обратить доменный ``Hotspot`` в ``HotspotDraft`` (рекурсивно по ``child``).

    Зеркало ``_build_hotspots``: геометрия из ``HotspotShape`` в доли, ``reveal_assets``
    восстанавливаются из памяти с отбрасыванием id без байтов, ``child`` — рекурсивно через
    ``_scheme_view_to_draft`` (``None`` у плоской зоны ИЛИ у вложенного вида без восстановимого
    фона — orphan-логика глубины). Иконка домена в драфт не переносится (её ставит
    ``_build_hotspots`` по умолчанию — симметрия сохраняется).
    """
    return HotspotDraft(
        x=h.shape.x,
        y=h.shape.y,
        w=h.shape.w,
        h=h.shape.h,
        label=h.label,
        reveal_text=h.reveal_text,
        reveal_assets=tuple(
            _asset_ref(a, assets) for a in h.reveal_assets if a in assets
        ),
        child=(
            _scheme_view_to_draft(h.child, assets) if h.child is not None else None
        ),
    )


def _inspection_to_draft(ins: InspectionCheck | None) -> InspectionDraft:
    """Обратить ``InspectionCheck`` в ``InspectionDraft`` (``None`` → пустой ``InspectionDraft``).

    Зеркало ``_build_inspection``: группы переносятся как есть (домен уже отбросил пустые при
    сборке) через ``_synset_to_draft``.
    """
    if ins is None:
        return InspectionDraft()
    return InspectionDraft(groups=tuple(_synset_to_draft(g) for g in ins.expected))


def _scheme_fields(
    scheme: SchemeDocument | None, assets: Mapping[str, bytes]
) -> tuple[AssetRef | None, tuple[HotspotDraft, ...]]:
    """Разложить ``SchemeDocument`` в пару «фон + зоны» драфта этапа (зеркало упаковки схемы).

    Возвращает ``(None, ())``, если схемы нет ИЛИ фон корневого вида утерян в архиве: ``build``
    пакует зоны лишь при заданном фоне, поэтому без восстановленного фона зоны не обращаются
    (orphan-логика). Иначе — восстановленный фон корня и его зоны (``_hotspot_to_draft``,
    рекурсивно по вложенным видам).
    """
    if (
        scheme is None
        or scheme.root.background is None
        or scheme.root.background not in assets
    ):
        return None, ()
    return (
        _asset_ref(scheme.root.background, assets),
        tuple(_hotspot_to_draft(h, assets) for h in scheme.root.hotspots),
    )


def _contacts_to_draft(
    stage: StageContacts, assets: Mapping[str, bytes]
) -> ContactsDraft:
    """Обратить этап 3 ``StageContacts`` в ``ContactsDraft`` (зеркало ``build_contacts``)."""
    scheme, hotspots = _scheme_fields(stage.scheme, assets)
    return ContactsDraft(
        intro=stage.intro,
        scheme=scheme,
        hotspots=hotspots,
        inspection=_inspection_to_draft(stage.inspection),
    )


def _environment_to_draft(
    stage: StageEnvironment, assets: Mapping[str, bytes]
) -> EnvironmentDraft:
    """Обратить этап 4 ``StageEnvironment`` в ``EnvironmentDraft`` (зеркало ``build_environment``).

    Фото восстанавливаются из памяти с отбрасыванием id без байтов; документы — через
    ``_task_to_draft`` (как этап 2).
    """
    scheme, hotspots = _scheme_fields(stage.scheme, assets)
    return EnvironmentDraft(
        intro=stage.intro,
        scheme=scheme,
        hotspots=hotspots,
        photos=tuple(_asset_ref(a, assets) for a in stage.photos if a in assets),
        documents=tuple(_task_to_draft(t) for t in stage.documents),
        inspection=_inspection_to_draft(stage.inspection),
    )


def case_to_draft(loaded: LoadedCase) -> CaseDraft:
    """Обратить загруженный ``Case`` в ``CaseDraft`` для правки (срез: мета + пациенты + этапы 2–4).

    ``case_id`` берётся из меты — правка сохраняет идентичность кейса. Этапы 2–4 (клинический,
    контакты, среда) обращаются; этапы 5–6 в этом срезе остаются ``None`` (их обращение —
    следующие срезы). Ассеты карточек пациентов, точек поиска и схем восстанавливаются из памяти
    (``loaded.assets``).
    """
    case = loaded.case
    return CaseDraft(
        case_id=case.meta.id,
        title=case.meta.title,
        author=case.meta.author,
        nosology=case.meta.nosology,
        unit_personnel=case.meta.unit_personnel,
        patients=tuple(
            _patient_to_draft(p, loaded.assets) for p in case.patients.patients
        ),
        clinical=_clinical_to_draft(case.clinical, loaded.assets),
        contacts=_contacts_to_draft(case.contacts, loaded.assets),
        environment=_environment_to_draft(case.environment, loaded.assets),
        ses=None,
        final=None,
    )


__all__ = ["case_to_draft"]
