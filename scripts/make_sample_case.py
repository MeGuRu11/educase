"""Генератор богатого синтетического кейса EduCase для визуальной приёмки Player.

Собирает доменный ``Case`` со ВСЕМИ шестью заполненными этапами (поиск, пациенты,
развилка, документы с обманками, осмотр, выбор уровня СЭС, таймлайны) и пакует его в
``_scratch/sample.epicase`` через слой приложения (``save_case``).

Запуск из .venv::

    python scripts/make_sample_case.py

Каталог вывода — ``_scratch`` в корне репозитория (``*.epicase`` уже в .gitignore);
переопределяется переменной окружения ``EDUCASE_SCRATCH``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Скрипт запускается как файл (не как пакет) — добавляем src/ в путь импорта.
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from epicase_core.application.cases import save_case  # noqa: E402
from epicase_core.domain.assets import AssetKind, AssetRef  # noqa: E402
from epicase_core.domain.case import Case, CaseMeta  # noqa: E402
from epicase_core.domain.documents import (  # noqa: E402
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
from epicase_core.domain.scheme import (  # noqa: E402
    Hotspot,
    HotspotShape,
    SchemeDocument,
    SchemeView,
)
from epicase_core.domain.search import (  # noqa: E402
    InspectionCheck,
    KeywordSearch,
    SearchEntry,
    SynonymSet,
)
from epicase_core.domain.stages import (  # noqa: E402
    BranchOption,
    BranchPoint,
    PatientCard,
    StageClinical,
    StageContacts,
    StageEnvironment,
    StageFinal,
    StagePatients,
    StageSes,
    Timeline,
)


def _stage_patients() -> StagePatients:
    """Этап 1: контекстный поиск + 3 карточки пациентов (одна со ссылкой на ассет)."""
    search = KeywordSearch(
        entries=(
            SearchEntry(
                id="s1-fever",
                triggers=SynonymSet(
                    canonical="лихорадка",
                    synonyms=("температура", "жар", "гипертермия"),
                ),
                reveal_text=(
                    "У 12 военнослужащих за сутки — подъём температуры до 38–39 °C, "
                    "озноб, слабость."
                ),
            ),
            SearchEntry(
                id="s1-diarrhea",
                triggers=SynonymSet(
                    canonical="диарея",
                    synonyms=("понос", "жидкий стул", "диарейный синдром"),
                ),
                reveal_text="Многократный жидкий стул с примесью слизи, тенезмы.",
                reveal_assets=("photo-patient-1",),
            ),
        ),
        optional=False,
    )
    patients = (
        PatientCard(
            id="p1",
            title="Рядовой А. — 1 рота",
            fields=(
                ("Жалобы", "Температура 38.7 °C, схваткообразные боли внизу живота"),
                ("Эпид. анамнез", "Питался в общей столовой 07.06, контакт с больными"),
                ("Ключевые данные", "Тенезмы, слизь в стуле, болезненная сигмовидная кишка"),
            ),
            assets=("photo-patient-1",),
        ),
        PatientCard(
            id="p2",
            title="Рядовой Б. — 1 рота",
            fields=(
                ("Жалобы", "Жидкий стул до 8 раз в сутки, слабость"),
                ("Эпид. анамнез", "Та же столовая, та же смена наряда по кухне"),
                ("Ключевые данные", "Обезвоживание лёгкой степени"),
            ),
        ),
        PatientCard(
            id="p3",
            title="Сержант В. — наряд по столовой",
            fields=(
                ("Жалобы", "Тошнота, субфебрилитет, дискомфорт в животе"),
                ("Эпид. анамнез", "Работал на раздаче пищи 05–07.06"),
                ("Ключевые данные", "Возможный источник — носительство"),
            ),
        ),
    )
    return StagePatients(
        intro=(
            "Поступили военнослужащие с острым кишечным синдромом. Изучите карточки "
            "и проведите контекстный поиск по ключевым словам."
        ),
        search=search,
        patients=patients,
    )


def _stage_clinical() -> StageClinical:
    """Этап 2: поиск, точка ветвления (верная опция + обманка), документ с обманкой."""
    search = KeywordSearch(
        entries=(
            SearchEntry(
                id="s2-pathogen",
                triggers=SynonymSet(
                    canonical="шигелла",
                    synonyms=("shigella", "возбудитель дизентерии"),
                ),
                reveal_text="Бактериологически выделена Shigella flexneri 2a.",
            ),
        )
    )
    branch = BranchPoint(
        id="b2-diagnosis",
        prompt="Сформулируйте клинико-эпидемиологический диагноз:",
        options=(
            BranchOption(
                id="b2-correct",
                label="Острая дизентерия (шигеллёз), пищевой путь, вспышка",
                is_correct=True,
            ),
            BranchOption(
                id="b2-decoy",
                label="Сальмонеллёз, спорадический случай",
                is_correct=False,
            ),
        ),
    )
    correct_template = DocumentTemplate(
        id="tpl-dm4",
        title="Внеочередное донесение (ДМ-4)",
        fields=(
            DocumentField(
                id="f-nosology",
                type=FieldType.TEXT,
                rule=TextMatch(
                    keywords=SynonymSet(
                        canonical="дизентерия",
                        synonyms=("шигеллёз", "острая дизентерия"),
                    )
                ),
                label="Нозологическая форма",
            ),
            DocumentField(
                id="f-cases",
                type=FieldType.NUMBER,
                rule=NumberMatch(value=23.0, tolerance=0.0),
                label="Число заболевших",
            ),
            DocumentField(
                id="f-onset",
                type=FieldType.DATE,
                rule=DateMatch(value="2026-06-09"),
                label="Дата начала вспышки (ISO)",
            ),
            DocumentField(
                id="f-status",
                type=FieldType.CHOICE,
                rule=ChoiceMatch(correct=("Подтверждён",)),
                label="Статус диагноза",
                options=("Подтверждён", "Под вопросом", "Исключён"),
            ),
        ),
    )
    documents = (
        DocumentTask(
            id="d2-report",
            prompt="Выберите документ для немедленного донесения и заполните его:",
            options=(
                DocumentOption(
                    id="opt-dm4",
                    title="Внеочередное донесение (ДМ-4)",
                    is_correct=True,
                    template=correct_template,
                ),
                DocumentOption(
                    id="opt-f058-decoy",
                    title="Экстренное извещение (ф. 058/у) — без полей",
                    is_correct=False,
                    template=None,
                ),
            ),
        ),
    )
    return StageClinical(
        intro="Установите диагноз по ключевым словам и оформите донесение.",
        search=search,
        branch=branch,
        documents=documents,
    )


def _stage_contacts() -> StageContacts:
    """Этап 3: ссылка на схему казармы + сверка свободного осмотра (3 группы)."""
    inspection = InspectionCheck(
        expected=(
            SynonymSet(canonical="скученность", synonyms=("теснота", "перенаселённость")),
            SynonymSet(canonical="вентиляция", synonyms=("проветривание", "воздухообмен")),
            SynonymSet(canonical="изоляция", synonyms=("изолятор", "разобщение")),
        )
    )
    scheme = SchemeDocument(
        title="Схема казармы",
        root=SchemeView(
            background="scheme-barracks-1",
            caption="Общая схема казармы: кликните по зоне для осмотра.",
            hotspots=(
                Hotspot(
                    id="hs-beds",
                    shape=HotspotShape(x=0.08, y=0.15, w=0.40, h=0.50),
                    label="Спальное помещение",
                    reveal_text=(
                        "Двухъярусные койки, расстояние между рядами менее 0.5 м — "
                        "выраженная скученность."
                    ),
                ),
                Hotspot(
                    id="hs-vent",
                    shape=HotspotShape(x=0.55, y=0.10, w=0.30, h=0.20),
                    label="Окна и вентиляция",
                    reveal_text="Часть окон не открывается, приточная вентиляция не работает.",
                ),
                Hotspot(
                    id="hs-isolation",
                    shape=HotspotShape(x=0.55, y=0.55, w=0.30, h=0.30),
                    label="Изолятор",
                    reveal_text="Помещение под изолятор не выделено, разобщение не организовано.",
                ),
            ),
        ),
    )
    return StageContacts(
        intro="Обследуйте контактных лиц по схеме казармы и опишите условия размещения.",
        scheme=scheme,
        inspection=inspection,
    )


def _stage_environment() -> StageEnvironment:
    """Этап 4: схема столовой + фото-ассеты, документ с обманкой, осмотр (2 группы)."""
    act_template = DocumentTemplate(
        id="tpl-gsen",
        title="Акт санитарно-эпидемиологического обследования (ГСЭН)",
        fields=(
            DocumentField(
                id="f-object",
                type=FieldType.TEXT,
                rule=TextMatch(
                    keywords=SynonymSet(
                        canonical="столовая",
                        synonyms=("пищеблок", "продовольственный объект"),
                    )
                ),
                label="Обследуемый объект",
            ),
            DocumentField(
                id="f-temp",
                type=FieldType.NUMBER,
                rule=NumberMatch(value=6.0, tolerance=1.0),
                label="Температура в холодильной камере, °C",
            ),
        ),
    )
    documents = (
        DocumentTask(
            id="d4-act",
            prompt="Какой документ оформляется по результатам обследования объекта?",
            options=(
                DocumentOption(
                    id="opt-gsen",
                    title="Акт ГСЭН (для МПД)",
                    is_correct=True,
                    template=act_template,
                ),
                DocumentOption(
                    id="opt-rapport-decoy",
                    title="Рапорт командира части — без полей",
                    is_correct=False,
                    template=None,
                ),
            ),
        ),
    )
    inspection = InspectionCheck(
        expected=(
            SynonymSet(canonical="хранение", synonyms=("холодильник", "холодильная камера")),
            SynonymSet(canonical="мухи", synonyms=("насекомые", "грызуны")),
        )
    )
    scheme = SchemeDocument(
        title="Схема пищеблока",
        root=SchemeView(
            background="scheme-canteen-1",
            caption="Общая схема пищеблока: кликните по зоне.",
            hotspots=(
                Hotspot(
                    id="hs-kitchen",
                    shape=HotspotShape(x=0.10, y=0.12, w=0.45, h=0.50),
                    label="Горячий цех",
                    icon="zoom",
                    child=SchemeView(
                        background="photo-kitchen-1",
                        caption="Горячий цех (фото): кликните по оборудованию.",
                        hotspots=(
                            Hotspot(
                                id="hs-fridge",
                                shape=HotspotShape(x=0.60, y=0.20, w=0.30, h=0.60),
                                label="Холодильная камера",
                                reveal_text=(
                                    "Температура +9 °C при норме +2…+6 °C — "
                                    "нарушение условий хранения."
                                ),
                                reveal_assets=("photo-store-1",),
                            ),
                        ),
                    ),
                ),
                Hotspot(
                    id="hs-store",
                    shape=HotspotShape(x=0.60, y=0.55, w=0.30, h=0.30),
                    label="Складское помещение",
                    reveal_text="Следы грызунов, продукты хранятся на полу.",
                ),
            ),
        ),
    )
    return StageEnvironment(
        intro="Обследуйте объекты внешней среды (столовая) по схеме и фото.",
        scheme=scheme,
        photos=("photo-kitchen-1", "photo-store-1"),
        documents=documents,
        inspection=inspection,
    )


def _stage_ses() -> StageSes:
    """Этап 5: поиск, выбор уровня СЭС (4 уровня, Прил. 22), документ с обманкой."""
    search = KeywordSearch(
        entries=(
            SearchEntry(
                id="s5-incidence",
                triggers=SynonymSet(
                    canonical="заболеваемость",
                    synonyms=("уровень заболеваемости", "показатель"),
                ),
                reveal_text="Показатель 47.9 на 1000 — рост более чем в 3 раза к фоновому.",
            ),
        )
    )
    level_choice = DocumentField(
        id="f-ses-level",
        type=FieldType.CHOICE,
        rule=ChoiceMatch(correct=("Неблагополучное",)),
        label="Санитарно-эпидемиологическое состояние части",
        options=(
            "Благополучное",
            "Неустойчивое",
            "Неблагополучное",
            "Чрезвычайное",
        ),
    )
    plan_template = DocumentTemplate(
        id="tpl-plan",
        title="План противоэпидемических мероприятий + приказ",
        fields=(
            DocumentField(
                id="f-quarantine",
                type=FieldType.NUMBER,
                rule=NumberMatch(value=7.0, tolerance=0.0),
                label="Срок обсервации, суток",
            ),
            DocumentField(
                id="f-measure",
                type=FieldType.TEXT,
                rule=TextMatch(
                    keywords=SynonymSet(
                        canonical="обсервация",
                        synonyms=("карантин", "ограничительные мероприятия"),
                    )
                ),
                label="Основное ограничительное мероприятие",
            ),
        ),
    )
    documents = (
        DocumentTask(
            id="d5-plan",
            prompt="Выберите документ, закрепляющий противоэпидемические мероприятия:",
            options=(
                DocumentOption(
                    id="opt-plan",
                    title="План + приказ командира части",
                    is_correct=True,
                    template=plan_template,
                ),
                DocumentOption(
                    id="opt-memo-decoy",
                    title="Служебная записка — без полей",
                    is_correct=False,
                    template=None,
                ),
            ),
        ),
    )
    return StageSes(
        intro="Оцените санитарно-эпидемиологическое состояние части (Приложение 22).",
        search=search,
        level_choice=level_choice,
        documents=documents,
    )


def _stage_final() -> StageFinal:
    """Этап 6: документ «Акт расследования» (пара полей) + два таймлайна наблюдения."""
    act_template = DocumentTemplate(
        id="tpl-investigation",
        title="Акт эпидемиологического расследования очага",
        fields=(
            DocumentField(
                id="f-source",
                type=FieldType.TEXT,
                rule=TextMatch(
                    keywords=SynonymSet(
                        canonical="пищевой путь",
                        synonyms=("через пищу", "алиментарный"),
                    )
                ),
                label="Установленный путь передачи",
            ),
            DocumentField(
                id="f-conclusion-date",
                type=FieldType.DATE,
                rule=DateMatch(value="2026-06-11"),
                label="Дата составления акта (ISO)",
            ),
        ),
    )
    documents = (
        DocumentTask(
            id="d6-investigation",
            prompt="Завершите расследование: выберите итоговый документ и заполните его.",
            options=(
                DocumentOption(
                    id="opt-investigation",
                    title="Акт расследования очага",
                    is_correct=True,
                    template=act_template,
                ),
                DocumentOption(
                    id="opt-explanatory-decoy",
                    title="Объяснительная записка — без полей",
                    is_correct=False,
                    template=None,
                ),
            ),
        ),
    )
    timelines = (
        Timeline(
            id="tl-observation",
            title="Сроки медицинского наблюдения за очагом",
            events=(
                ("2026-06-09", "Регистрация первого случая, начало наблюдения"),
                ("2026-06-16", "Промежуточный осмотр контактных (7 суток)"),
                ("2026-06-16", "Окончание максимального инкубационного периода"),
            ),
        ),
        Timeline(
            id="tl-measures",
            title="План снятия ограничительных мероприятий",
            events=(
                ("2026-06-12", "Заключительная дезинфекция пищеблока"),
                ("2026-06-23", "Контрольное бактериологическое обследование"),
            ),
        ),
    )
    return StageFinal(
        intro="Поставьте окончательный эпидемиологический диагноз и оформите акт.",
        search=None,
        documents=documents,
        timelines=timelines,
    )


def build_sample_case() -> Case:
    """Собрать богатый синтетический кейс со всеми шестью заполненными этапами."""
    meta = CaseMeta(
        id="sample-001",
        title="Острая кишечная инфекция в в/ч 00000",
        author="reality-checker",
        nosology="Острая дизентерия (шигеллёз)",
        unit_personnel=480,
        created_at="2026-06-11",
    )
    assets = (
        AssetRef("photo-patient-1", "assets/photo-patient-1.png", AssetKind.PHOTO),
        AssetRef("scheme-barracks-1", "assets/scheme-barracks-1.svg", AssetKind.SCHEME),
        AssetRef("scheme-canteen-1", "assets/scheme-canteen-1.svg", AssetKind.SCHEME),
        AssetRef("photo-kitchen-1", "assets/photo-kitchen-1.png", AssetKind.PHOTO),
        AssetRef("photo-store-1", "assets/photo-store-1.png", AssetKind.PHOTO),
    )
    return Case(
        meta=meta,
        patients=_stage_patients(),
        clinical=_stage_clinical(),
        contacts=_stage_contacts(),
        environment=_stage_environment(),
        ses=_stage_ses(),
        final=_stage_final(),
        assets=assets,
    )


def _output_path() -> Path:
    """Путь вывода: ``EDUCASE_SCRATCH`` или ``_scratch`` в корне репозитория."""
    base = os.environ.get("EDUCASE_SCRATCH")
    scratch = Path(base) if base else _REPO_ROOT / "_scratch"
    return scratch / "sample.epicase"


def _describe(case: Case) -> str:
    """Краткий состав кейса для вывода в консоль."""
    lines = [
        f"meta: id={case.meta.id!r} title={case.meta.title!r} "
        f"nosology={case.meta.nosology!r} personnel={case.meta.unit_personnel}",
        f"assets: {len(case.assets)} ссылок",
    ]
    p = case.patients
    n_p_search = len(p.search.entries) if p.search else 0
    lines.append(f"1 Пациенты: {len(p.patients)} карточки, поиск={n_p_search} записей")
    c = case.clinical
    n_branch = len(c.branch.options) if c.branch else 0
    lines.append(
        f"2 Клинический: поиск={len(c.search.entries) if c.search else 0}, "
        f"развилка={n_branch} опции, документов={len(c.documents)}"
    )
    ct = case.contacts
    n_ct_hotspots = len(ct.scheme.root.hotspots) if ct.scheme else 0
    lines.append(
        f"3 Контактные: хотспотов на схеме={n_ct_hotspots}, "
        f"осмотр={len(ct.inspection.expected) if ct.inspection else 0} групп"
    )
    e = case.environment
    n_e_hotspots = len(e.scheme.root.hotspots) if e.scheme else 0
    lines.append(
        f"4 Внешняя среда: хотспотов на схеме={n_e_hotspots}, фото={len(e.photos)}, "
        f"документов={len(e.documents)}, осмотр={len(e.inspection.expected) if e.inspection else 0}"
    )
    s = case.ses
    n_levels = len(s.level_choice.options) if s.level_choice else 0
    lines.append(
        f"5 Оценка СЭС: поиск={len(s.search.entries) if s.search else 0}, "
        f"уровней СЭС={n_levels}, документов={len(s.documents)}"
    )
    f = case.final
    lines.append(f"6 Финал: документов={len(f.documents)}, таймлайнов={len(f.timelines)}")
    return "\n".join(lines)


def main() -> int:
    """Собрать кейс, упаковать в .epicase, напечатать путь и состав."""
    case = build_sample_case()
    dst = _output_path()
    written = save_case(case, dst)
    print(f"Кейс записан: {written}")
    print(f"Размер: {written.stat().st_size} байт")
    print("--- Состав ---")
    print(_describe(case))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
