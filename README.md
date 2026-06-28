# EpiCase

Десктоп-тренажёр для подготовки военных эпидемиологов (ВМА им. Кирова). Windows 10/11,
компьютерный класс. Две раздельные программы:

- **Constructor** — преподаватель собирает кейсы (без авторизации).
- **Player** — курсант проходит кейс и формирует результат.

Обмен — только файлами `.epicase` (кейс) и `.epiresult` (результат), перенос вручную.
**Сетевого кода в проекте нет** (ADR-003).

## Стек

Python 3.12 · PySide6 (только виджеты) · loguru · PyInstaller · pytest-qt · ruff ·
mypy (strict). Персистентность — файловая (кодек `.epicase`/`.epiresult`), без БД/ORM (ADR-009).

## Разработка

```bash
python -m venv .venv && . .venv/Scripts/activate    # Windows
pip install -e ".[dev]"

# Запуск
epicase-constructor      # или: python -m epicase_constructor
epicase-player           # или: python -m epicase_player

# Quality gate
ruff check src tests
mypy src tests
pytest -q
```

## Сборка EXE

```bash
pyinstaller packaging/constructor.spec
pyinstaller packaging/player.spec
# результат — в dist/
```

## Для ИИ-агентов

- `AGENTS.md` — инструкция для Codex.
- `CLAUDE.md` — инструкция для Claude Code (архитектор/senior/UI/ревью).
- `CODEX.md` — правила для Codex GPT 5.5 (скаффолдинг).
- `.agents/skills/` — проектные skills Codex.
- `.claude/agents/` — сабагенты с привязкой к лестнице моделей (`model:`).
- `.claude/skills/` — проектные скиллы (контекст, механика этапов, документы, формат архива).

## Структура

```
src/epicase_core/          общий слой (домен, application, infrastructure, кодеки архивов)
src/epicase_constructor/   GUI преподавателя
src/epicase_player/        GUI курсанта
tests/                     pytest / pytest-qt
packaging/                 .spec для PyInstaller
docs/adr/                  материализованные архитектурные решения (ADR-013..016)
```

Constructor показывает преподавателю подробную предварительную машинную сверку, но
не вычисляет баллы или pass/fail. Player правильность не показывает; окончательное
решение принимает преподаватель (ADR-016).
