# Application Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Constructor and Player fixed, distinct runtime names, Windows AppUserModelIDs, and packaged window/taskbar icons while preserving two independent entrypoints.

**Architecture:** Add one shared presentation-layer identity module in `epicase_ui` with an enum-keyed allowlist and no arbitrary path input. Each entrypoint configures its `QApplication` before constructing the first window, then explicitly assigns the returned icon to that window; PyInstaller `.spec` files remain out of scope for `PKG-1`.

**Tech Stack:** Python 3.12, PySide6 `QApplication`/`QIcon`, `importlib.resources`, Windows `shell32`, loguru, pytest/pytest-qt, ruff, mypy.

---

## File map

- Create `src/epicase_ui/application_identity.py`: immutable identities, packaged ICO loading, application configuration, and guarded Windows AppUserModelID integration.
- Create `tests/ui/test_application_identity.py`: real-Qt tests for identities, icons, fallback behavior, and platform integration.
- Modify `src/epicase_ui/__init__.py`: export the shared public identity API.
- Modify `src/epicase_constructor/__main__.py`: select and apply the Constructor identity.
- Modify `src/epicase_player/__main__.py`: select and apply the Player identity.
- Modify `tests/test_entrypoints.py`: verify each process chooses its own identity and sets its main-window icon before maximizing.
- Modify `TASKS.md`: close `ICON-1C` and its parent `ICON-1`, leaving `PKG-1` open.

### Task 1: Shared application identity

**Files:**
- Create: `tests/ui/test_application_identity.py`
- Create: `src/epicase_ui/application_identity.py`
- Modify: `src/epicase_ui/__init__.py`

- [ ] **Step 1: Write failing identity and icon tests**

Create tests that import the not-yet-existing public API and assert the exact fixed contract:

```python
def test_application_identities_are_fixed_and_distinct() -> None:
    constructor = application_identity(ApplicationVariant.CONSTRUCTOR)
    player = application_identity(ApplicationVariant.PLAYER)

    assert constructor == ApplicationIdentity(
        application_name="EpiCase Constructor",
        display_name="EpiCase Constructor",
        app_user_model_id="VMedA.EpiCase.Constructor",
        icon_filename="epicase_constructor.ico",
    )
    assert player == ApplicationIdentity(
        application_name="EpiCase Player",
        display_name="EpiCase Player",
        app_user_model_id="VMedA.EpiCase.Player",
        icon_filename="epicase_player.ico",
    )
    assert constructor != player


def test_application_icons_are_packaged_and_distinct(qtbot: QtBot) -> None:
    del qtbot
    constructor = application_icon(ApplicationVariant.CONSTRUCTOR)
    player = application_icon(ApplicationVariant.PLAYER)

    assert not constructor.isNull()
    assert not player.isNull()
    assert constructor.pixmap(64, 64).cacheKey() != player.pixmap(64, 64).cacheKey()
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\python.exe' -m pytest tests/ui/test_application_identity.py -q
```

Expected: collection fails because `epicase_ui.application_identity` does not exist.

- [ ] **Step 3: Implement the immutable allowlist and packaged icon loader**

Create the shared types and fixed mapping:

```python
class ApplicationVariant(StrEnum):
    CONSTRUCTOR = "constructor"
    PLAYER = "player"


@dataclass(frozen=True)
class ApplicationIdentity:
    application_name: str
    display_name: str
    app_user_model_id: str
    icon_filename: str


_APPLICATION_IDENTITIES = {
    ApplicationVariant.CONSTRUCTOR: ApplicationIdentity(
        "EpiCase Constructor",
        "EpiCase Constructor",
        "VMedA.EpiCase.Constructor",
        "epicase_constructor.ico",
    ),
    ApplicationVariant.PLAYER: ApplicationIdentity(
        "EpiCase Player",
        "EpiCase Player",
        "VMedA.EpiCase.Player",
        "epicase_player.ico",
    ),
}
```

Implement `application_identity()` as an enum lookup. Implement `application_icon()` by resolving only the mapped filename under `epicase_ui/resources/app_icons` with `importlib.resources.files`, constructing `QIcon`, and returning an empty icon after a loguru warning when the resource cannot be read or the icon is null.

- [ ] **Step 4: Run the identity/icon tests and verify GREEN**

Run the focused command from Step 2.

Expected: both tests pass.

- [ ] **Step 5: Write failing configuration and platform tests**

Add tests using the real pytest-qt application:

```python
def test_configure_application_sets_qt_identity(qapp: QApplication) -> None:
    icon = configure_application(qapp, ApplicationVariant.CONSTRUCTOR)

    assert qapp.applicationName() == "EpiCase Constructor"
    assert qapp.applicationDisplayName() == "EpiCase Constructor"
    assert qapp.windowIcon().cacheKey() == icon.cacheKey()


def test_configure_application_sets_windows_app_user_model_id(
    qapp: QApplication,
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(application_identity_module.sys, "platform", "win32")
    monkeypatch.setattr(
        application_identity_module,
        "_call_windows_app_user_model_id",
        lambda value: calls.append(value) or 0,
    )

    configure_application(qapp, ApplicationVariant.PLAYER)

    assert calls == ["VMedA.EpiCase.Player"]


def test_configure_application_skips_windows_api_on_other_platforms(
    qapp: QApplication,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(application_identity_module.sys, "platform", "linux")
    monkeypatch.setattr(
        application_identity_module,
        "_call_windows_app_user_model_id",
        lambda value: pytest.fail(f"unexpected Windows call: {value}"),
    )

    configure_application(qapp, ApplicationVariant.PLAYER)
```

Add a missing-resource test by temporarily replacing the mapped Constructor identity with one whose allowlisted filename is `missing.ico`; assert that `application_icon()` returns a null `QIcon` without raising and that loguru receives a warning.

- [ ] **Step 6: Run the new tests and verify RED**

Run the focused command from Step 2.

Expected: tests fail because `configure_application()` and the Windows helper do not exist.

- [ ] **Step 7: Implement Qt configuration and guarded Windows integration**

Implement:

```python
def configure_application(
    app: QApplication,
    variant: ApplicationVariant,
) -> QIcon:
    identity = application_identity(variant)
    app.setApplicationName(identity.application_name)
    app.setApplicationDisplayName(identity.display_name)
    icon = application_icon(variant)
    app.setWindowIcon(icon)
    _set_windows_app_user_model_id(identity.app_user_model_id)
    return icon
```

Add a private Windows call that loads `shell32`, configures
`SetCurrentProcessExplicitAppUserModelID` for a wide string, and returns its HRESULT. The guarding helper must:

```python
def _set_windows_app_user_model_id(app_user_model_id: str) -> None:
    if sys.platform != "win32":
        return
    try:
        result = _call_windows_app_user_model_id(app_user_model_id)
    except (AttributeError, OSError) as exc:
        logger.warning("Cannot set Windows AppUserModelID {}: {}", app_user_model_id, exc)
        return
    if result != 0:
        logger.warning(
            "Windows rejected AppUserModelID {} with HRESULT {}",
            app_user_model_id,
            result,
        )
```

Export `ApplicationIdentity`, `ApplicationVariant`, `application_icon`,
`application_identity`, and `configure_application` from `epicase_ui.__init__`.

- [ ] **Step 8: Run the focused tests and full quality gate**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\ruff.exe' check src tests
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\mypy.exe' src tests
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\python.exe' -m pytest -q
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\python.exe' -m compileall -q src tests
```

Expected: all four commands exit 0.

- [ ] **Step 9: Commit the shared identity module**

```powershell
git add src/epicase_ui/application_identity.py src/epicase_ui/__init__.py tests/ui/test_application_identity.py
git commit -m "feat(ui): add application identities"
```

### Task 2: Apply identities in both process entrypoints

**Files:**
- Modify: `tests/test_entrypoints.py`
- Modify: `src/epicase_constructor/__main__.py`
- Modify: `src/epicase_player/__main__.py`

- [ ] **Step 1: Extend the entrypoint test and verify RED**

Parameterize the expected variant for each module, make `configure_application()` return a sentinel icon, and record call order:

```python
@pytest.mark.parametrize(
    ("module_name", "expected_variant"),
    (
        ("epicase_constructor.__main__", ApplicationVariant.CONSTRUCTOR),
        ("epicase_player.__main__", ApplicationVariant.PLAYER),
    ),
)
def test_main_configures_identity_and_launches_window_maximized(
    monkeypatch: MonkeyPatch,
    module_name: str,
    expected_variant: ApplicationVariant,
) -> None:
    events: list[object] = []
    sentinel_icon = object()

    def fake_configure_application(
        app: object,
        variant: ApplicationVariant,
    ) -> object:
        events.append(("configure", app, variant))
        return sentinel_icon

    class FakeMainWindow:
        def setWindowIcon(self, icon: object) -> None:
            events.append(("window-icon", icon))

        def showMaximized(self) -> None:
            events.append("maximized")
```

Retain assertions that reject `show()` and `showFullScreen()`, then assert the configured variant, the sentinel window icon, and that `"window-icon"` precedes `"maximized"`.

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& 'C:\Users\user\Desktop\Program\educase\.venv\Scripts\python.exe' -m pytest tests/test_entrypoints.py -q
```

Expected: both cases fail because the entrypoints do not import or call `configure_application`.

- [ ] **Step 2: Integrate the Constructor and Player variants**

In each entrypoint, import the shared API and configure the application before loading the stylesheet or constructing `MainWindow`:

```python
icon = configure_application(app, ApplicationVariant.CONSTRUCTOR)
app.setStyleSheet(load_qss())
window = MainWindow()
window.setWindowIcon(icon)
window.showMaximized()
```

Use `ApplicationVariant.PLAYER` in `epicase_player.__main__`.

- [ ] **Step 3: Run the focused tests and full quality gate**

Run the focused entrypoint command, then the four full-gate commands from Task 1 Step 8.

Expected: focused tests and all four gate commands exit 0.

- [ ] **Step 4: Commit entrypoint integration**

```powershell
git add src/epicase_constructor/__main__.py src/epicase_player/__main__.py tests/test_entrypoints.py
git commit -m "feat(apps): apply distinct window identities"
```

### Task 3: Close ICON-1C and verify the deliverable

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Update task status**

Change:

```markdown
- [ ] ICON-1
  - [ ] ICON-1C
```

to:

```markdown
- [x] ICON-1
  - [x] ICON-1C
```

Keep `PKG-1` unchecked because separate PyInstaller builds are not implemented here.

- [ ] **Step 2: Run the final full quality gate**

Run the four full-gate commands from Task 1 Step 8.

Expected: all commands exit 0 and the test count increases beyond the 617-test baseline.

- [ ] **Step 3: Commit task completion**

```powershell
git add TASKS.md
git commit -m "docs: close application icon task"
```

- [ ] **Step 4: Inspect the final branch**

Run:

```powershell
git status --short --branch
git log --oneline -5
git diff 9c13ef8..HEAD --stat
```

Expected: clean `codex/application-identity` worktree with the design, plan, implementation, tests, and task-status commits; no PyInstaller `.spec` files.

- [ ] **Step 5: Prepare live acceptance**

Run Constructor and Player simultaneously from the shared virtual environment. Verify distinct titlebar icons, distinct taskbar icons/groups, distinct Alt+Tab entries, icon persistence after minimize/restore, and unchanged startup behavior. Do not push, merge, or create a PR without explicit user confirmation.
