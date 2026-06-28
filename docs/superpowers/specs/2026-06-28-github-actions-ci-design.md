# GitHub Actions quality gate

## Статус

Утверждено пользователем 28 июня 2026 года.

## Цель

Запускать обязательный quality gate EpiCase в GitHub до слияния Pull Request и после
изменений в `main`.

## Workflow

- Файл: `.github/workflows/quality.yml`.
- События: Pull Request в `main`, push в `main`, ручной `workflow_dispatch`.
- Среда: `windows-latest`, Python 3.12.
- Официальные actions: `actions/checkout@v6` и `actions/setup-python@v6`.
- Зависимости устанавливаются командой `python -m pip install -e ".[dev]"`.
- `setup-python` кеширует pip по `pyproject.toml`.
- Для тестов PySide6 задаётся `QT_QPA_PLATFORM=offscreen`.
- Права `GITHUB_TOKEN` ограничиваются `contents: read`.
- Повторный запуск для той же ветки отменяет предыдущий незавершённый запуск.
- Тайм-аут job — 20 минут.

## Проверки

Один job `quality` выполняет проектный gate строго по порядку:

1. `ruff check src tests`
2. `mypy src tests`
3. `pytest -q`
4. `python -m compileall -q src tests`

Падение любого шага останавливает job и не даёт считать CI зелёным.

## Слияние

1. Workflow добавляется в текущую ветку `codex/project-consistency-sync` и отправляется в
   Pull Request #1.
2. GitHub запускает проверку Pull Request.
3. После зелёного результата PR переводится из draft в готовый.
4. PR сливается в `main` методом merge commit, чтобы сохранить все существующие коммиты и
   их хеши.
5. Удалённая и локальная feature-ветки удаляются только после успешного слияния и повторной
   проверки состояния `main`.

## Проверка результата

- В Pull Request отображается обязательный job `quality`.
- Все четыре шага зелёные.
- `main` содержит merge commit и всю историю feature-ветки.
- Локальная ветка `main` совпадает с `origin/main`.
