# Ten-File Attachment Limit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every `ATTACHMENT` document block accept up to ten files, remove bulk clearing and preserve old archive compatibility.

**Architecture:** Keep the serialized `allow_multiple` field so format version 1 archives continue to load, but stop using it as Player behavior. `DocumentWidget` owns the per-block limit and UI state; Constructor writes `allow_multiple=True` for attachment templates without exposing a redundant setting.

**Tech Stack:** Python 3.12, PySide6 Widgets, pytest/pytest-qt, QSS, ruff, mypy strict.

---

### Task 1: Player always accepts up to ten files

**Files:**
- Modify: `src/epicase_player/ui/document_widget.py:50-272`
- Modify: `src/epicase_core/theme/theme.qss:483-508`
- Modify: `tests/player/test_document_widget.py:271-490`
- Modify: `tests/player/test_stage_views.py:331-390`
- Modify: `tests/player/test_main_window.py:120-155`

- [ ] **Step 1: Write failing Player behavior tests**

Replace the old single/multiple and bulk-clear expectations with tests that exercise a legacy
`allow_multiple=False` template, the ten-file cap and per-card removal:

```python
def test_attachment_legacy_single_flag_still_allows_multiple_files(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = tmp_path / "first.pdf"
    second = tmp_path / "second.docx"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    widget = DocumentWidget(_make_attachment_task(allow_multiple=False))
    qtbot.addWidget(widget)
    widget.options_combo.setCurrentIndex(0)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: ([str(first), str(second)], ""),
    )

    widget._pick_files()

    assert [name for _, name in widget.attachments()] == ["first.pdf", "second.docx"]
    attach_button = widget.form_area.findChild(QPushButton, "attachButton")
    assert attach_button is not None
    assert attach_button.text() == "Прикрепить файлы"
```

```python
def test_attachment_limit_keeps_first_ten_and_disables_picker(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = []
    for index in range(11):
        path = tmp_path / f"file-{index}.pdf"
        path.write_bytes(str(index).encode())
        paths.append(str(path))
    widget = DocumentWidget(_make_attachment_task(allow_multiple=False))
    qtbot.addWidget(widget)
    widget.options_combo.setCurrentIndex(0)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: (paths, ""),
    )

    widget._pick_files()

    assert len(widget.attachments()) == 10
    assert len(widget.attachment_bytes()) == 10
    header = widget.form_area.findChild(QLabel, "attachmentSectionTitle")
    assert header is not None
    assert header.text() == "Прикреплённые файлы · 10 / 10"
    attach_button = widget.form_area.findChild(QPushButton, "attachButton")
    assert attach_button is not None
    assert not attach_button.isEnabled()
    assert widget._status_label.text() == "Можно прикрепить не более 10 файлов"
```

```python
def test_removing_attachment_reopens_one_limit_slot(
    qtbot: QtBot,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths = []
    for index in range(10):
        path = tmp_path / f"file-{index}.pdf"
        path.write_bytes(b"x")
        paths.append(str(path))
    widget = DocumentWidget(_make_attachment_task())
    qtbot.addWidget(widget)
    widget.options_combo.setCurrentIndex(0)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileNames",
        lambda *args, **kwargs: (paths, ""),
    )
    widget._pick_files()

    remove = widget.form_area.findChild(QPushButton, "attachmentRemoveButton")
    assert remove is not None
    remove.click()

    assert len(widget.attachments()) == 9
    attach_button = widget.form_area.findChild(QPushButton, "attachButton")
    assert attach_button is not None
    assert attach_button.isEnabled()
    assert widget.form_area.findChild(QPushButton, "attachClear") is None
```

Update direct test calls in `test_stage_views.py` and `test_main_window.py` from
`_pick_files(allow_multiple=...)` to `_pick_files()`.

- [ ] **Step 2: Run the Player tests and verify RED**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q -o addopts="" `
  tests/player/test_document_widget.py `
  tests/player/test_stage_views.py `
  tests/player/test_main_window.py
```

Expected: failures because `_pick_files()` still requires `allow_multiple`, old templates use
the single-file dialog, the limit is absent and `attachClear` still exists.

- [ ] **Step 3: Implement the per-block limit**

In `document_widget.py`, define the policy next to the result type:

```python
_MAX_ATTACHMENTS = 10
_ATTACHMENT_LIMIT_MESSAGE = "Можно прикрепить не более 10 файлов"
```

Replace the clear-button state with the attachment button:

```python
self._attach_button: QPushButton | None = None
```

Replace `_pick_files` with unconditional multiple selection and bounded insertion:

```python
def _pick_files(self) -> None:
    remaining = _MAX_ATTACHMENTS - len(self._attachments)
    if remaining <= 0:
        self._status_label.setText(_ATTACHMENT_LIMIT_MESSAGE)
        return
    paths, _ = QFileDialog.getOpenFileNames(self, "Выберите файл(ы)")
    if not paths:
        return
    accepted_paths = paths[:remaining]
    for path_text in accepted_paths:
        path = Path(path_text)
        data = path.read_bytes()
        asset_id = "att-" + uuid4().hex + path.suffix
        self._attach_bytes[asset_id] = data
        self._attachments.append((asset_id, path.name))
    self._status_label.setText(
        _ATTACHMENT_LIMIT_MESSAGE if len(paths) > remaining else ""
    )
    self._refresh_attach_list()
```

Delete `_clear_attachments`. In `_refresh_attach_list`, update count and button state:

```python
count = len(self._attachments)
if self._attach_header is not None:
    self._attach_header.setText(
        f"Прикреплённые файлы · {count} / {_MAX_ATTACHMENTS}"
    )
if self._attach_empty is not None:
    self._attach_empty.setVisible(count == 0)
if self._attach_button is not None:
    self._attach_button.setEnabled(count < _MAX_ATTACHMENTS)
```

In `_rebuild_form`, reset `_attach_button`, always create one `attachButton` labelled
`Прикрепить файлы`, remove `attachClear`, and connect through an argument-free lambda:

```python
self._attach_button = None
```

```python
attach_button = QPushButton("Прикрепить файлы")
attach_button.setObjectName("attachButton")
self._attach_button = attach_button
self._form_layout.addWidget(attach_button)
attach_button.clicked.connect(lambda: self._pick_files())
```

Keep the panel, header, empty label and card layout unchanged. Remove all
`QPushButton#attachClear` selectors from `theme.qss`.

- [ ] **Step 4: Run Player tests and verify GREEN**

Run the same command as Step 2.

Expected: all selected Player tests pass.

- [ ] **Step 5: Commit Player behavior**

```powershell
git add -- src/epicase_player/ui/document_widget.py src/epicase_core/theme/theme.qss tests/player/test_document_widget.py tests/player/test_stage_views.py tests/player/test_main_window.py
git commit -m "feat(player): allow ten files per attachment block"
```

### Task 2: Constructor removes the obsolete switch

**Files:**
- Modify: `src/epicase_constructor/ui/template_editor.py:8-130`
- Modify: `tests/constructor/test_template_editor.py:1-105`

- [ ] **Step 1: Write failing Constructor tests**

Remove assertions against `multiple_checkbox` and add:

```python
def test_attachment_mode_has_no_multiple_files_toggle(qtbot: QtBot) -> None:
    widget = TemplateEditor()
    qtbot.addWidget(widget)

    assert widget.findChild(QCheckBox, "allowMultipleToggle") is None
```

```python
def test_attachment_draft_always_uses_compatible_multiple_value(
    qtbot: QtBot,
) -> None:
    widget = TemplateEditor()
    qtbot.addWidget(widget)
    widget.load(
        TemplateDraft(
            title="Старый шаблон",
            fields=(),
            fill_mode="attachment",
            allow_multiple=False,
        )
    )

    restored = widget.to_draft()

    assert restored.fill_mode == "attachment"
    assert restored.allow_multiple is True
```

Keep the existing test that `fields` mode round-trips and assert its compatibility value is
`False`.

- [ ] **Step 2: Run Constructor tests and verify RED**

Run:

```powershell
.\.venv\Scripts\pytest.exe -q -o addopts="" tests/constructor/test_template_editor.py
```

Expected: the toggle still exists and an old attachment draft still returns
`allow_multiple=False`.

- [ ] **Step 3: Remove the toggle and normalize saved drafts**

Delete the `QCheckBox` import, `multiple_checkbox` construction, form row and all visibility
or load logic for it. Reduce `_sync_mode_visibility` to:

```python
def _sync_mode_visibility(self) -> None:
    """Показать редактор полей только для режима FIELDS."""
    self._fields_container.setVisible(self.mode_combo.currentData() == "fields")
```

Build the compatibility field from the selected mode:

```python
mode = self.mode_combo.currentData()
return TemplateDraft(
    title=self.title_edit.text(),
    fields=tuple(editor.to_draft() for editor in self.field_editors),
    fill_mode=mode,
    allow_multiple=mode == "attachment",
)
```

- [ ] **Step 4: Run Constructor tests and verify GREEN**

Run the same command as Step 2.

Expected: all template editor tests pass.

- [ ] **Step 5: Commit Constructor behavior**

```powershell
git add -- src/epicase_constructor/ui/template_editor.py tests/constructor/test_template_editor.py
git commit -m "refactor(constructor): remove attachment count toggle"
```

### Task 3: Synchronize policy documentation and task tracking

**Files:**
- Modify: `docs/adr/015-document-attachment-mode.md:15-40`
- Modify: `.agents/skills/epicase-document-templates/SKILL.md:15-25`
- Modify: `docs/superpowers/specs/2026-06-28-ui-readability-attachments-design.md:25-40`
- Modify: `TASKS.md:25-35`

- [ ] **Step 1: Amend ADR-015 without changing the archive format**

Replace the one-or-multiple policy with:

```markdown
3. Каждый блок `ATTACHMENT` принимает от нуля до 10 файлов. Настройка количества
   преподавателем удалена. Поле `allow_multiple` сохраняется в формате версии 1 только
   для обратной совместимости; Player его не использует.
```

Update the Player/Constructor consequences to state that Player always uses multiple selection
with a ten-file cap and Constructor no longer displays the toggle.

- [ ] **Step 2: Synchronize project guidance**

In `.agents/skills/epicase-document-templates/SKILL.md`, describe `ATTACHMENT` as
`до 10 файлов на один блок`.

In the previous UI design spec, replace the bulk-clear and one-file replacement bullets with:

```markdown
- Каждый блок принимает до 10 файлов; удаление выполняется по одной карточке.
- Кнопка «Очистить всё» отсутствует.
```

Add the completed task:

```markdown
- [x] UI: до 10 вложений на каждый блок документа без массовой очистки
```

- [ ] **Step 3: Check documentation consistency**

Run:

```powershell
rg -n "Очистить всё|один файл.*несколько|allow_multiple" docs/adr/015-document-attachment-mode.md .agents/skills/epicase-document-templates/SKILL.md docs/superpowers/specs/2026-06-28-ui-readability-attachments-design.md
git diff --check
```

Expected: no active policy still requires bulk clearing or a user-selectable one/multiple mode;
`allow_multiple` appears only in the compatibility explanation.

- [ ] **Step 4: Commit policy synchronization**

```powershell
git add -- docs/adr/015-document-attachment-mode.md .agents/skills/epicase-document-templates/SKILL.md docs/superpowers/specs/2026-06-28-ui-readability-attachments-design.md TASKS.md
git commit -m "docs: synchronize ten-file attachment policy"
```

### Task 4: Full verification and live handoff

**Files:**
- Verify: all modified files

- [ ] **Step 1: Run the required quality gate in order**

```powershell
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src tests
.\.venv\Scripts\pytest.exe -q -o addopts=""
.\.venv\Scripts\python.exe -m compileall -q src tests
```

Expected: every command exits with code 0 and pytest reports the exact passing-test count.

- [ ] **Step 2: Verify Git scope**

```powershell
git diff --check
git status --short
git log -6 --oneline
```

Expected: no unstaged or untracked implementation files remain; the three implementation
commits follow the documentation-plan commit.

- [ ] **Step 3: Hand off the live regression checklist**

Use `C:\Users\user\Desktop\Program\educase_testdata\shigellosis.epicase`:

1. On stage 4 select several files in one dialog despite the legacy single-file flag.
2. Add more files in another dialog until the block shows `10 / 10`.
3. Verify the attach button is disabled and no bulk-clear button is present.
4. Remove one card, attach one replacement and save the result.
5. Open the `.epiresult` in Constructor and verify all ten cards and their Open/Save actions.
