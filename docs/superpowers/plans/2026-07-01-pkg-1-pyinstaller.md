# PKG-1 PyInstaller Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce two independent Windows one-file GUI executables with the correct EpiCase resources, application icons, and package isolation.

**Architecture:** Keep `packaging/constructor.spec` and `packaging/player.spec` as the build configuration. Resolve all inputs from PyInstaller's `SPECPATH`, package only the resources each application needs, and validate the executable contract by executing each spec against lightweight test doubles before running real builds.

**Tech Stack:** Python 3.12, PyInstaller 6, PySide6, pytest, PowerShell.

---

## File map

- Create `tests/test_packaging_specs.py`: executable contract tests for both spec files.
- Modify `packaging/constructor.spec`: robust paths, Constructor resources and ICO, Player exclusion.
- Modify `packaging/player.spec`: robust paths, shared resources and Player ICO, Constructor exclusion.
- Modify `TASKS.md`: close PKG-1 only after both built executables pass acceptance.

### Task 1: Lock the packaging contract with failing tests

**Files:**
- Create: `tests/test_packaging_specs.py`

- [ ] **Step 1: Add a typed spec harness and parameterized contract test**

Create `tests/test_packaging_specs.py` with fake `Analysis`, `PYZ`, and `EXE`
objects. Execute each repository-controlled spec with `SPECPATH` set to the
real `packaging` directory, then assert:

```python
@pytest.mark.parametrize(
    "expected",
    (
        ExpectedSpec(
            filename="constructor.spec",
            entrypoint="epicase_constructor/__main__.py",
            excluded_package="epicase_player",
            executable_name="EpiCase Constructor",
            icon_name="epicase_constructor.ico",
            data_destinations=frozenset(
                {
                    "epicase_core/theme",
                    "epicase_ui/resources",
                    "epicase_constructor/resources/icons",
                }
            ),
        ),
        ExpectedSpec(
            filename="player.spec",
            entrypoint="epicase_player/__main__.py",
            excluded_package="epicase_constructor",
            executable_name="EpiCase Player",
            icon_name="epicase_player.ico",
            data_destinations=frozenset(
                {
                    "epicase_core/theme",
                    "epicase_ui/resources",
                }
            ),
        ),
    ),
)
def test_spec_builds_one_file_gui_with_expected_resources(
    expected: ExpectedSpec,
) -> None:
    source, analysis, executable = _execute_spec(expected.filename)
    expected_entrypoint = SRC / expected.entrypoint

    assert analysis.call.args[0] == [str(expected_entrypoint)]
    assert analysis.call.kwargs["pathex"] == [str(SRC)]
    assert analysis.call.kwargs["excludes"] == [expected.excluded_package]

    datas = cast(list[tuple[str, str]], analysis.call.kwargs["datas"])
    assert {destination for _, destination in datas} == expected.data_destinations
    assert all(Path(path).exists() for path, _ in datas)

    icon = Path(cast(str, executable.call.kwargs["icon"]))
    assert icon == APP_ICONS / expected.icon_name
    assert icon.exists()
    assert executable.call.kwargs["name"] == expected.executable_name
    assert executable.call.kwargs["console"] is False
    assert executable.call.kwargs["upx"] is False
    assert "COLLECT(" not in source
```

The helpers must expose captured positional and keyword arguments without
importing or running PyInstaller:

```python
@dataclass(frozen=True)
class CapturedCall:
    args: tuple[object, ...]
    kwargs: dict[str, object]


class FakeAnalysis:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.call = CapturedCall(args, kwargs)
        self.pure: list[object] = []
        self.scripts: list[object] = []
        self.binaries: list[object] = []
        self.datas: list[object] = []


class FakeBuildTarget:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.call = CapturedCall(args, kwargs)


def _execute_spec(filename: str) -> tuple[str, FakeAnalysis, FakeBuildTarget]:
    path = PACKAGING / filename
    source = path.read_text(encoding="utf-8")
    namespace: dict[str, object] = {
        "Analysis": FakeAnalysis,
        "PYZ": FakeBuildTarget,
        "EXE": FakeBuildTarget,
        "SPECPATH": str(PACKAGING),
    }
    exec(compile(source, str(path), "exec"), namespace)
    return (
        source,
        cast(FakeAnalysis, namespace["a"]),
        cast(FakeBuildTarget, namespace["exe"]),
    )
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest tests/test_packaging_specs.py -q
```

Expected: both cases fail because the current specs point outside the
repository and do not define the required exclusions, shared resources, names,
or EXE icons.

### Task 2: Implement both one-file spec configurations

**Files:**
- Modify: `packaging/constructor.spec`
- Modify: `packaging/player.spec`

- [ ] **Step 1: Make Constructor paths and resources explicit**

At the top of `packaging/constructor.spec`, resolve inputs from `SPECPATH`:

```python
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent.resolve()
SRC = PROJECT_ROOT / "src"
UI_RESOURCES = SRC / "epicase_ui" / "resources"
APP_ICONS = UI_RESOURCES / "app_icons"
```

Configure `Analysis` with the absolute Constructor entrypoint, `pathex`,
theme, all shared UI resources, Constructor action icons, and the Player
exclusion:

```python
a = Analysis(
    [str(SRC / "epicase_constructor" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        (
            str(SRC / "epicase_core" / "theme" / "theme.qss"),
            "epicase_core/theme",
        ),
        (str(UI_RESOURCES), "epicase_ui/resources"),
        (
            str(SRC / "epicase_constructor" / "resources" / "icons"),
            "epicase_constructor/resources/icons",
        ),
    ],
    hiddenimports=[],
    hookspath=[],
    excludes=["epicase_player"],
    noarchive=False,
)
```

Keep direct `EXE` construction without `COLLECT`, and set:

```python
name="EpiCase Constructor",
console=False,
upx=False,
icon=str(APP_ICONS / "epicase_constructor.ico"),
```

- [ ] **Step 2: Make Player paths and resources explicit**

Use the same root constants in `packaging/player.spec`. Configure the Player
entrypoint, theme, all shared UI resources, and `excludes=["epicase_constructor"]`.
Set:

```python
name="EpiCase Player",
console=False,
upx=False,
icon=str(APP_ICONS / "epicase_player.ico"),
```

Do not package Constructor action icons separately in Player.

- [ ] **Step 3: Run the focused test and verify GREEN**

Run:

```powershell
python -m pytest tests/test_packaging_specs.py -q
```

Expected: `2 passed`.

- [ ] **Step 4: Run the mandatory quality gate**

Run in order, stopping on the first failure:

```powershell
ruff check src tests
mypy src tests
pytest -q
python -m compileall -q src tests
```

Expected: every command exits with code 0.

- [ ] **Step 5: Commit the tested build configuration**

```powershell
git add tests/test_packaging_specs.py packaging/constructor.spec packaging/player.spec
git commit -m "build: configure standalone Windows executables"
```

### Task 3: Build and accept both executables

**Files:**
- Generated, ignored: `build/constructor/`, `build/player/`
- Generated, ignored: `dist/EpiCase Constructor.exe`, `dist/EpiCase Player.exe`

- [ ] **Step 1: Build Constructor from the repository root**

Run:

```powershell
pyinstaller --clean --noconfirm --distpath dist --workpath build/constructor packaging/constructor.spec
```

Expected: exit code 0 and `dist/EpiCase Constructor.exe` exists.

- [ ] **Step 2: Build Player from the repository root**

Run:

```powershell
pyinstaller --clean --noconfirm --distpath dist --workpath build/player packaging/player.spec
```

Expected: exit code 0 and `dist/EpiCase Player.exe` exists.

- [ ] **Step 3: Inspect embedded resources and Windows icons**

Run `pyi-archive_viewer -l` for both files and assert that each archive contains
`epicase_core/theme/theme.qss`, the correct application ICO, and shared brand
and hotspot resources. Constructor must also contain
`epicase_constructor/resources/icons`.

Use `[System.Drawing.Icon]::ExtractAssociatedIcon()` for each EXE and assert
that both extracted icons are non-null and have different handles.

- [ ] **Step 4: Smoke-launch each GUI**

Start each EXE with `Start-Process -PassThru -WindowStyle Hidden`, wait for
input-idle or a visible main-window handle for up to 30 seconds, and fail if
the process exits early. Stop only the exact process IDs started by this
check after successful startup.

Expected: both processes remain alive long enough to create their main window,
with no missing-module or missing-resource startup error.

### Task 4: Close PKG-1 after acceptance

**Files:**
- Modify: `TASKS.md`

- [ ] **Step 1: Mark PKG-1 complete**

Change only:

```markdown
- [ ] PKG-1 — PyInstaller, 2 EXE (theme.qss + иконки в datas) (M)
```

to:

```markdown
- [x] PKG-1 — PyInstaller, 2 EXE (theme.qss + иконки в datas) (M)
```

- [ ] **Step 2: Run the final quality gate**

Run the four quality-gate commands from Task 2 Step 4.

Expected: every command exits with code 0.

- [ ] **Step 3: Commit task completion**

```powershell
git add TASKS.md
git commit -m "docs: close PyInstaller packaging task"
```

- [ ] **Step 4: Verify the final repository state**

Run:

```powershell
git status --short
git log -4 --oneline
Get-Item 'dist/EpiCase Constructor.exe', 'dist/EpiCase Player.exe' |
    Select-Object Name, Length, LastWriteTime
```

Expected: the worktree is clean, the design/plan/build/task commits are
present, and both ignored EXE artifacts remain available under `dist/`.
