---
name: epicase-project
description: >-
  Контекст и обязательные правила EpiCase — офлайн desktop-тренажёра на PySide6
  с Constructor, Player и файловым обменом. Используй при любой работе с проектом.
---

# EpiCase — проектный skill

## Перед задачей

1. Прочитай `AGENTS.md` и затронутые ADR.
2. Определи слой: Domain / Application / Infrastructure / Constructor UI / Player UI.
3. Для этапов, документов или архивов прочитай соответствующий `epicase-*` skill.
4. Сверяй документацию с фактическим кодом; при расхождении новейший ADR имеет приоритет.

## Архитектура

- `epicase_core.domain` — чистый Python, immutable-модели и бизнес-правила.
- `epicase_core.application` — оркестрация, сборка и загрузка моделей.
- `epicase_core.infrastructure.archive` — единственная персистентность.
- `epicase_constructor` — GUI преподавателя.
- `epicase_player` — GUI курсанта.

UI обращается к Infrastructure только через Application. БД/ORM нет. Сетевого кода нет
(ADR-003). JSON — исключительно внутреннее содержимое архивов.

## Файловый обмен

- `.epicase` — кейс;
- `.epiresult` — результат;
- перенос вручную через Проводник.

## Оценивание

Player не показывает правильность и не блокирует прохождение. `grade_case` формирует
подробную предварительную машинную проверку для преподавателя: `верно`, `неверно`,
`не отвечено`, фактические ответы и контекст. Баллов и pass/fail нет; окончательное
решение принимает преподаватель (ADR-016).

## Quality gate

`ruff check src tests` → `mypy src tests` → `pytest -q` →
`python -m compileall -q src tests` → Conventional Commit.

## Стиль

- Python 3.12, mypy strict, типы на всё.
- PySide6 Widgets и layout-менеджеры; стили только через `theme.qss`.
- Долгие операции не выполняются в GUI-потоке.
- `logging`/loguru вместо `print()` в `src`.
- Тесты Qt используют реальные виджеты, кодеки — `tmp_path`.
