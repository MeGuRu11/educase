# Project Consistency Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Синхронизировать код, ADR, документацию и agent-skills с утверждённой моделью
предварительной машинной проверки и актуальным устройством EpiCase.

**Architecture:** `grade_case` остаётся чистым доменным механизмом предварительной
поэлементной сверки, а Constructor показывает её преподавателю без итогового балла.
Legacy `FREE_TEXT` удаляется из текущей модели с чтением старого значения как `FIELDS`;
остальные изменения устраняют расхождения имён, расширений и ADR без расширения runtime.

**Tech Stack:** Python 3.12, PySide6 Widgets, frozen dataclasses, pytest/pytest-qt,
ruff, mypy strict, Markdown ADR и локальные SKILL.md.

---

### Task 1: Зафиксировать архитектурную политику

**Files:**
- Create: `docs/adr/016-advisory-machine-review.md`
- Modify: `docs/adr/README.md`
- Modify: `docs/adr/014-department-feedback-manual-grading.md`
- Modify: `docs/adr/015-document-attachment-mode.md`

- [ ] Записать ADR-016: машинные статусы являются подсказкой преподавателю; Player их
  не показывает; баллов, pass/fail и сохраняемого ручного вердикта нет.
- [ ] Пометить ADR-014 изменённым ADR-016, не переписывая исторический контекст.
- [ ] Уточнить ADR-015: `FIELDS`/`ATTACHMENT` остаются, а запрет машинной сверки отменён.
- [ ] Проверить ссылки командой:
  `rg -n "ADR-016|машинн" docs/adr`.

### Task 2: Удалить legacy FREE_TEXT через TDD

**Files:**
- Modify: `tests/core/test_domain_case.py`
- Modify: `tests/core/test_attempt.py`
- Modify: `tests/core/test_case_builder.py`
- Modify: `tests/core/test_case_loader.py`
- Modify: `tests/player/test_document_widget.py`
- Modify: `src/epicase_core/domain/documents.py`
- Modify: `src/epicase_core/domain/attempt.py`
- Modify: `src/epicase_player/ui/document_widget.py`
- Modify: `src/epicase_player/ui/stage_views.py`

- [ ] Добавить падающий тест совместимости:

```python
def test_document_template_legacy_free_text_loads_as_fields() -> None:
    raw = template.to_dict()
    raw["fill_mode"] = "free_text"
    restored = DocumentTemplate.from_dict(raw)
    assert restored.fill_mode is FillMode.FIELDS
    assert not hasattr(FillMode, "FREE_TEXT")
```

- [ ] Добавить падающий тест результата:

```python
def test_document_response_ignores_legacy_free_text() -> None:
    restored = DocumentResponse.from_dict(
        {"task_id": "doc-1", "free_text": "legacy"}
    )
    assert not hasattr(restored, "free_text")
    assert "free_text" not in restored.to_dict()
```

- [ ] Запустить два новых теста и подтвердить ожидаемые сбои на `FREE_TEXT/free_text`.
- [ ] Оставить в `FillMode` только `FIELDS` и `ATTACHMENT`; в
  `DocumentTemplate.from_dict` преобразовать строку `free_text` в `fields`.
- [ ] Удалить `DocumentResponse.free_text`, ветку `QPlainTextEdit` и передачу
  `free_text` из `_doc_resp`.
- [ ] Удалить или переписать тесты, которые закрепляли старый режим; сохранить тест
  Constructor, проверяющий fallback старого шаблона в поля.
- [ ] Запустить:
  `pytest -q tests/core/test_domain_case.py tests/core/test_attempt.py tests/core/test_case_builder.py tests/core/test_case_loader.py tests/constructor/test_template_editor.py tests/player/test_document_widget.py`.

### Task 3: Синхронизировать фактическую модель и отчёт

**Files:**
- Modify: `docs/DATA_MODEL.md`
- Modify: `src/epicase_core/domain/report.py`
- Modify: `src/epicase_core/application/grading.py`
- Modify: `src/epicase_constructor/ui/main_window.py`
- Modify: `src/epicase_constructor/ui/report_dialog.py`
- Modify: `src/epicase_constructor/ui/report_view.py`
- Modify: `src/epicase_player/ui/inspection_widget.py`

- [ ] Описать фактические `Case`, шесть этапов, `Attempt`, `CaseReport`,
  `SchemeDocument` «фон + прямоугольные хотспоты» и ZIP-архивы.
- [ ] В docstring заменить двусмысленное «нейтральный отчёт без вердикта» на
  «предварительная машинная проверка без итоговой оценки».
- [ ] Сохранить нейтральность Player и существующий QSS-рендер Constructor.
- [ ] Проверить отсутствие баллов и pass/fail:
  `rg -n "score|pass/fail|процент" src`.

### Task 4: Синхронизировать проектные инструкции и skills

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `CODEX.md`
- Move: `.agents/skills/educase-project/SKILL.md` → `.agents/skills/epicase-project/SKILL.md`
- Move: `.agents/skills/educase-stage-mechanics/SKILL.md` → `.agents/skills/epicase-stage-mechanics/SKILL.md`
- Move: `.agents/skills/educase-document-templates/SKILL.md` → `.agents/skills/epicase-document-templates/SKILL.md`
- Move: `.agents/skills/educase-archive-format/SKILL.md` → `.agents/skills/epicase-archive-format/SKILL.md`
- Modify: `.claude/skills/epicase-project/SKILL.md`
- Modify: `.claude/skills/epicase-stage-mechanics/SKILL.md`
- Modify: `.claude/skills/epicase-document-templates/SKILL.md`
- Modify: `.claude/skills/epicase-archive-format/SKILL.md`
- Modify: `.codex/agents/*.toml`
- Modify: `.claude/agents/*.md`

- [ ] Везде использовать EpiCase, `epicase_core`, `.epicase/.epiresult` и реальные
  функции `write_epicase/read_epicase/write_epiresult/read_epiresult`.
- [ ] Описать ADR-013 вместо векторного ADR-012 и ADR-016 вместо полного отказа от
  машинной проверки.
- [ ] Удалить все упоминания дедлайна.
- [ ] Обновить пути Codex-skills на `.agents/skills/epicase-*`.

### Task 5: Синхронизировать рабочие документы и трекер

**Files:**
- Modify: `README.md`
- Modify: `docs/decisions.md`
- Modify: `docs/questions_for_department.md`
- Modify: `TASKS.md`

- [ ] Пометить ADR-012 отменённым ADR-013 и убрать его из backlog.
- [ ] Зафиксировать K2/K3 как решённые: машинная подсказка без балла, итог за
  преподавателем; формат отчёта подробный поэлементный.
- [ ] Исправить утверждение, что tracked-файл `TASKS.md` не отслеживается Git.
- [ ] Отметить завершение CLN-1 после прохождения тестов.
- [ ] Удалить дедлайн и устаревшие расширения/имена.

### Task 6: Проверка и коммиты

**Files:**
- Verify: all modified files

- [ ] Выполнить поиск остаточных рассинхронов:

```powershell
rg -n --hidden -g '!.git/**' -g '!.venv/**' -g '!.worktrees/**' `
  '25 июня|дедлайн|\.educase|\.eduresult|educase_core|FREE_TEXT|free_text|ADR-012' .
```

- [ ] Разобрать каждое совпадение: оставить только исторические упоминания ADR-012 и
  compatibility-строку `"free_text"` в чтении старого формата.
- [ ] Последовательно выполнить:

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\python.exe -m compileall -q src tests
```

- [ ] Проверить `git diff --check` и состав файлов.
- [ ] Создать Conventional Commit для runtime/tests и отдельный docs/chore-коммит для
  ADR, skills и трекера, если это сохраняет историю понятнее.
