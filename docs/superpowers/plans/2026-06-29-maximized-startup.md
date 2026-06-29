# Maximized Application Startup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Launch Constructor and Player maximized while preserving normal Windows window controls.

**Architecture:** Keep the behavior in the two application entry points. The `MainWindow` classes remain reusable at normal size in tests and dialogs; only normal process startup calls `showMaximized()`.

**Tech Stack:** Python 3.12, PySide6 Widgets, pytest, ruff, mypy strict.

---

### Task 1: Launch both application windows maximized

**Files:**
- Create: `tests/test_entrypoints.py`
- Modify: `src/epicase_constructor/__main__.py`
- Modify: `src/epicase_player/__main__.py`

- [ ] **Step 1: Write the failing entry-point test**

Create a parametrized test for `epicase_constructor.__main__` and
`epicase_player.__main__`. Replace `QApplication` and `MainWindow` with local
fakes, call `main()`, and assert that `showMaximized()` is called exactly once.
The fake must raise if `show()` or `showFullScreen()` is called.

- [ ] **Step 2: Run the test and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_entrypoints.py -q
```

Expected: both cases fail because the current entry points call `show()`.

- [ ] **Step 3: Implement the minimal behavior**

In both entry points replace:

```python
window.show()
```

with:

```python
window.showMaximized()
```

- [ ] **Step 4: Run the focused tests and verify GREEN**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_entrypoints.py -q
```

Expected: both parametrized cases pass.

- [ ] **Step 5: Run the full quality gate**

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: all four commands exit with code 0.

- [ ] **Step 6: Commit**

```powershell
git add -- docs/superpowers/plans/2026-06-29-maximized-startup.md tests/test_entrypoints.py src/epicase_constructor/__main__.py src/epicase_player/__main__.py
git commit -m "feat(ui): launch applications maximized"
```
