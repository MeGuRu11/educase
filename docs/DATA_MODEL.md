# EduCase — Модель данных (DATA_MODEL)

> ⚠️ **РЕКОНСТРУКЦИЯ ИЗ ПАМЯТИ — САМЫЙ НЕНАДЁЖНЫЙ ФАЙЛ.** Я помню *механику* этапов и
> *названия* документов, но не помню точную схему оригинального DATA_MODEL.md (поля, типы,
> связи). Ниже — **скелет сущностей, выведенный из механики**, который надо привести в
> соответствие с реальностью. Всё, что помечено `?`, — моя догадка.

## Общая картина

Один **кейс (Case)** = метаданные + **шесть этапов (Stage)**. Кейс упаковывается в `.epicase`.
Прохождение курсантом порождает **результат (Result)**, упаковываемый в `.epiresult`.

Слой: домен — чистые сущности; сериализация в JSON внутри ZIP — в `infrastructure/archive`.

## Сущности кейса (.epicase)

### Case
- `id`, `title`, `format_version` (= 1?), `created_at?`
- `stages: list[Stage]` — ровно 6, в фиксированном порядке.
- ссылки на ассеты (фото, документы).

### Stage (6 типов, фиксированный порядок)
Базово у этапа: `kind`, `title`, опциональный `keyword_search`, набор `documents`, ассеты.

1. **PatientsStage** — опциональный контекстный поиск + `patient_cards: list[PatientCard]`.
2. **DiagnosisStage** — поиск + `branch_point` (см. BranchPoint) + документы (ДМ4 / форма 23).
3. **ContactExamStage** — `facility_scheme` с персоналом + иконки действий (`action_icons`).
4. **EnvObjectStage** — схема + фото + иконки действий + документы (акт ГСЭН, донесение
   командира с обманками) + (возможно) `room_inspection`.
5. **SesAssessmentStage** — поиск + документы (план + приказ с обманками).
6. **FinalDiagnosisStage** — поиск + документы (акт расследования вспышки) +
   `observation_timelines`.

### Вспомогательные
- **PatientCard** — поля карточки пациента (?).
- **KeywordSearch** — `synonyms: dict[term, list[str]]`, строгое сопоставление (ADR-006). Без fuzzy.
- **BranchPoint** (этап 2) — варианты ответа; верный/неверный путь ведут через те же этапы;
  ошибка фиксируется, но не блокирует (ADR-005), вскрывается в отчёте.
- **FacilityScheme** — план объекта + `personnel` + `action_icons` (кликабельные действия).
- **EnvironmentalObject** — схема + `photos` + `action_icons`.
- **SchemeDocument** (осмотр помещений, ADR-008 + ADR-012) — план одного объекта:
  - `canvas_size`, опц. `background_image`;
  - `layers: list[Layer]`.
  - **Layer** — `name`, `visible: bool`, `locked: bool`, `z_order: int`, `items: list[SchemeItem]`.
  - **SchemeItem** (база) — `id` + привязки: `photos`, `content`, `expected_keywords`. Подтипы:
    - **Room** — `points: list[Point]` (прямоугольник = 4 точки; полигон = N точек);
      `interior_photos` с хотспотами для второго уровня навигации.
    - **Wall** — `start: Point`, `end: Point`, опц. `thickness`.
    - **Marker** — `kind` (вход / личный состав / иконка действия), `position: Point`; для входа —
      ссылка на связанную `Room`.
    - **Hotspot** — зона на интерьерном фото: геометрия + `expected_keywords`.
  - **Point** — `x: float`, `y: float` (координаты холста).
  - Редактор (Constructor) и вьюер (Player, read-only) используют **один** тип `SchemeDocument`.
- **Document** (механика «Вариант B», ADR-007):
  - `template_kind` (см. educase-document-templates);
  - предъявляется в списке с `decoys` (обманками) — курсант выбирает правильный;
  - `fields: list[DocumentField]` с `expected_value` и правилом сравнения.
- **DocumentField** — `name`, `type` (текст/число/выбор?), `expected_value`, `compare_rule?`.
- **ObservationTimeline** (этап 6) — временная шкала наблюдения (?).

### Документы (типы шаблонов) — детали в educase-document-templates
- Приложение 1 — ДМ4 / Внеочередное донесение (критерии вспышки).
- Приложение 3 — Ежемесячный отчёт.
- Приложение 22 — оценка СЭС: 4 уровня + числовые пороги.
- Приложение 23 — формулы расчёта заболеваемости.
- Акт расследования вспышки — 11+ полей.
- Прочее: форма 23, акт ГСЭН, донесение командира, план, приказ.

## Сущности результата (.epiresult)

### Result
- `case_id`, `format_version`, `completed_at?`
- по каждому этапу: ответы, выбранные документы, заполненные поля, свободные выводы.
- зафиксированная ветка (верная/неверная) с этапа 2.
- итог: ошибки/баллы и данные для финального отчёта.

## TODO по сверке (критично)
- [ ] Заменить весь скелет на реальную схему из оригинального DATA_MODEL.md.
- [ ] Поля и типы PatientCard, DocumentField, ObservationTimeline.
- [x] ~~Структура facility_scheme / action_icons / hotspots~~ — задана SchemeDocument (ADR-012).
- [ ] Модель оценивания: что считается ошибкой, как формируется финальный отчёт.
- [x] ~~Решить: SQLite у Constructor или только .epicase~~ — документная модель, без БД (ADR-009).
