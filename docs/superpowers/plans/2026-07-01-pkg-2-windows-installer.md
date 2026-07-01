# PKG-2 Windows Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one modern administrative Windows installer that installs both EpiCase applications or either application independently.

**Architecture:** Store the installer contract in one Inno Setup 6 script and expose one root batch command that first rebuilds the PyInstaller executables, reads the project version, locates `ISCC.exe`, and compiles the installer. Three fixed setup types map to two components; conditional cleanup makes the selected set authoritative on upgrades.

**Tech Stack:** Inno Setup 6.7.3, Windows batch, PyInstaller artifacts, Python 3.12, pytest.

---

## File map

- Create `packaging/installer.iss`: administrative x64 installer definition.
- Create `build_installer.bat`: reproducible EXE and installer build entrypoint.
- Create `tests/test_installer_packaging.py`: static installer and batch contract tests.
- Modify `README.md`: document the compiler prerequisite and build command.
- Modify `TASKS.md`: close PKG-2 after compile/install/uninstall acceptance.

### Task 1: Lock the installer contract with failing tests

**Files:**
- Create: `tests/test_installer_packaging.py`

- [ ] **Step 1: Add focused contract tests**

Create a test module that reads `pyproject.toml`, `packaging/installer.iss`, and
`build_installer.bat`. Assert the following exact behavior:

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "packaging" / "installer.iss"
BUILD_SCRIPT = ROOT / "build_installer.bat"


def _read_required(path: Path) -> str:
    assert path.exists()
    return path.read_text(encoding="utf-8")


def test_installer_is_modern_administrative_x64_setup() -> None:
    source = _read_required(INSTALLER)

    assert "AppId={{6A2BBD1B-1646-4D0E-92DB-21BCE0D50322}" in source
    assert "AppVersion={#AppVersion}" in source
    assert "DefaultDirName={autopf}\\EpiCase" in source
    assert "PrivilegesRequired=admin" in source
    assert "ArchitecturesAllowed=x64compatible" in source
    assert "ArchitecturesInstallIn64BitMode=x64compatible" in source
    assert "WizardStyle=modern dynamic" in source
    assert "MinVersion=10.0" in source
    assert "VersionInfoVersion={#AppVersion}" in source
    assert "VersionInfoProductName=EpiCase" in source
    assert "VersionInfoDescription=EpiCase Installer" in source
    assert 'Name: "russian"; MessagesFile: "compiler:Languages\\Russian.isl"' in source


def test_installer_has_three_fixed_component_sets() -> None:
    source = _read_required(INSTALLER)

    assert 'Name: "full"; Description: "Constructor и Player"' in source
    assert 'Name: "constructor"; Description: "Только Constructor"' in source
    assert 'Name: "player"; Description: "Только Player"' in source
    assert 'Name: "constructor"; Description: "EpiCase Constructor"; Types: full constructor' in source
    assert 'Name: "player"; Description: "EpiCase Player"; Types: full player' in source
    assert "iscustom" not in source


def test_installer_files_and_shortcuts_follow_components() -> None:
    source = _read_required(INSTALLER)

    assert 'Source: "..\\dist\\EpiCase Constructor.exe"' in source
    assert 'Source: "..\\dist\\EpiCase Player.exe"' in source
    assert "Components: constructor" in source
    assert "Components: player" in source
    assert 'Name: "{commongroup}\\EpiCase Constructor"' in source
    assert 'Name: "{commongroup}\\EpiCase Player"' in source
    assert 'Name: "{commondesktop}\\EpiCase Constructor"' in source
    assert 'Name: "{commondesktop}\\EpiCase Player"' in source
    assert "Tasks: desktopicon" in source


def test_installer_removes_deselected_components_without_touching_user_files() -> None:
    source = _read_required(INSTALLER)

    assert "UsePreviousSetupType=no" in source
    assert source.count("WizardIsComponentSelected('constructor')") == 3
    assert source.count("WizardIsComponentSelected('player')") == 3
    assert ".epicase" not in source
    assert ".epiresult" not in source


def test_installer_build_reads_project_version_and_fails_fast() -> None:
    source = _read_required(BUILD_SCRIPT)

    assert 'set "ROOT=%~dp0"' in source
    assert 'call "%ROOT%build_all.bat"' in source
    assert "tomllib.load" in source
    assert "['project']['version']" in source
    assert "if not defined APP_VERSION goto version_missing" in source
    assert "Inno Setup 6 is required" in source
    assert '"/DAppVersion=%APP_VERSION%"' in source
    assert '"packaging\\installer.iss"' in source
    assert 'set "EXIT_CODE=2"' in source
    assert 'set "EXIT_CODE=3"' in source
    assert "exit /b %EXIT_CODE%" in source
```

Keep assertions split across five tests so failures identify the broken layer.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& '.venv\Scripts\python.exe' -m pytest tests/test_installer_packaging.py -q
```

Expected: five assertion failures because `installer.iss` and
`build_installer.bat` do not exist.

### Task 2: Implement the Inno Setup definition

**Files:**
- Create: `packaging/installer.iss`

- [ ] **Step 1: Add setup identity and platform configuration**

Start the script with a required command-line version macro and stable identity:

```iss
#ifndef AppVersion
  #error AppVersion must be passed by build_installer.bat
#endif

#define AppName "EpiCase"
#define ConstructorExe "EpiCase Constructor.exe"
#define PlayerExe "EpiCase Player.exe"

[Setup]
AppId={{6A2BBD1B-1646-4D0E-92DB-21BCE0D50322}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=ВМА им. С. М. Кирова
DefaultDirName={autopf}\EpiCase
DefaultGroupName=EpiCase
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern dynamic
ShowLanguageDialog=no
OutputDir=..\dist
OutputBaseFilename=EpiCase Installer {#AppVersion}
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
UsePreviousSetupType=no
UsePreviousTasks=yes
UninstallDisplayName=EpiCase
VersionInfoVersion={#AppVersion}
VersionInfoProductVersion={#AppVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoProductName=EpiCase
VersionInfoDescription=EpiCase Installer
```

Add the Russian message file:

```iss
[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
```

- [ ] **Step 2: Define the three exact setup types and two components**

```iss
[Types]
Name: "full"; Description: "Constructor и Player"
Name: "constructor"; Description: "Только Constructor"
Name: "player"; Description: "Только Player"

[Components]
Name: "constructor"; Description: "EpiCase Constructor"; Types: full constructor; Flags: disablenouninstallwarning
Name: "player"; Description: "EpiCase Player"; Types: full player; Flags: disablenouninstallwarning
```

Do not add an `iscustom` type; this prevents a zero-component selection.

- [ ] **Step 3: Add component-scoped files and shortcuts**

```iss
[Tasks]
Name: "desktopicon"; Description: "Создать ярлыки на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked

[Files]
Source: "..\dist\{#ConstructorExe}"; DestDir: "{app}"; Flags: ignoreversion; Components: constructor
Source: "..\dist\{#PlayerExe}"; DestDir: "{app}"; Flags: ignoreversion; Components: player

[Icons]
Name: "{commongroup}\EpiCase Constructor"; Filename: "{app}\{#ConstructorExe}"; WorkingDir: "{app}"; Components: constructor
Name: "{commongroup}\EpiCase Player"; Filename: "{app}\{#PlayerExe}"; WorkingDir: "{app}"; Components: player
Name: "{commondesktop}\EpiCase Constructor"; Filename: "{app}\{#ConstructorExe}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: constructor
Name: "{commondesktop}\EpiCase Player"; Filename: "{app}\{#PlayerExe}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: player
```

- [ ] **Step 4: Delete files and shortcuts for deselected components**

Add six narrowly-scoped entries:

```iss
[InstallDelete]
Type: files; Name: "{app}\{#ConstructorExe}"; Check: not WizardIsComponentSelected('constructor')
Type: files; Name: "{commongroup}\EpiCase Constructor.lnk"; Check: not WizardIsComponentSelected('constructor')
Type: files; Name: "{commondesktop}\EpiCase Constructor.lnk"; Check: not WizardIsComponentSelected('constructor')
Type: files; Name: "{app}\{#PlayerExe}"; Check: not WizardIsComponentSelected('player')
Type: files; Name: "{commongroup}\EpiCase Player.lnk"; Check: not WizardIsComponentSelected('player')
Type: files; Name: "{commondesktop}\EpiCase Player.lnk"; Check: not WizardIsComponentSelected('player')
```

Do not use recursive directory deletion or mention `.epicase`/`.epiresult`.

### Task 3: Implement the public installer build command

**Files:**
- Create: `build_installer.bat`

- [ ] **Step 1: Add fail-fast EXE build and interpreter selection**

```bat
@echo off
setlocal

set "ROOT=%~dp0"
pushd "%ROOT%" >nul || exit /b 1

call "%ROOT%build_all.bat"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto finish

set "PYTHON=python"
if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"
```

- [ ] **Step 2: Read the authoritative project version**

```bat
set "APP_VERSION="
for /f "usebackq delims=" %%V in (`"%PYTHON%" -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION goto version_missing
```

- [ ] **Step 3: Locate Inno Setup 6 and compile**

Search `PATH`, the machine-wide 32-bit Program Files path, and the per-user
path in that order:

```bat
set "ISCC="
for %%I in (ISCC.exe) do set "ISCC=%%~$PATH:I"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LocalAppData%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC goto compiler_missing

"%ISCC%" "/DAppVersion=%APP_VERSION%" "packaging\installer.iss"
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:compiler_missing
echo Inno Setup 6 is required. Install it and rerun build_installer.bat.
set "EXIT_CODE=2"
goto finish

:version_missing
echo Could not read the project version from pyproject.toml.
set "EXIT_CODE=3"

:finish
popd
exit /b %EXIT_CODE%
```

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the focused command from Task 1.

Expected: five tests pass.

- [ ] **Step 5: Run the mandatory quality gate**

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
& '.venv\Scripts\ruff.exe' check src tests
& '.venv\Scripts\mypy.exe' src tests
& '.venv\Scripts\python.exe' -m pytest -q
& '.venv\Scripts\python.exe' -m compileall -q src tests
```

Expected: all four commands exit 0.

- [ ] **Step 6: Commit the tested installer sources**

```powershell
git add packaging/installer.iss build_installer.bat tests/test_installer_packaging.py
git commit -m "build: add selectable Windows installer"
```

### Task 4: Compile and exercise the installer

**Files:**
- Generated, ignored: `dist/EpiCase Installer 0.1.0.exe`

- [ ] **Step 1: Install the stable compiler for local development**

If `ISCC.exe` is still absent, install official stable Inno Setup 6.7.3 for the
current developer account. Do not add a downloader to the repository.

- [ ] **Step 2: Build through the public command**

Run from outside the repository root to verify `%~dp0`:

```powershell
cmd /c C:\Users\user\Desktop\Program\educase\build_installer.bat
```

Expected: both application EXEs are rebuilt, Inno Setup exits 0, and
`dist/EpiCase Installer 0.1.0.exe` exists.

- [ ] **Step 3: Inspect installer metadata**

Verify with Windows version resources that:

- product name is `EpiCase`;
- file description identifies the setup;
- product version is `0.1.0`;
- requested execution level is administrative.

- [ ] **Step 4: Exercise the three setup types**

For each `full`, `constructor`, and `player` type, run the generated installer
with `/TYPE=<type>`, install into a dedicated test directory, and verify the
exact expected EXE set. Reinstall `player` over `full` and verify Constructor
and its shortcuts are removed. Run `unins000.exe /VERYSILENT /SUPPRESSMSGBOXES`
and verify the installation directory is removed.

Because the current shell is not elevated, use an explicit UAC-approved
interactive launch for this acceptance step; do not weaken
`PrivilegesRequired=admin`.

### Task 5: Document and close PKG-2

**Files:**
- Modify: `README.md`
- Modify: `TASKS.md`

- [ ] **Step 1: Document installer build**

Add to the README build section:

```bat
rem Требуется Inno Setup 6
build_installer.bat
```

State that the output is `dist/EpiCase Installer <version>.exe` and the setup
offers both applications or either application.

- [ ] **Step 2: Mark PKG-2 complete**

Change only the PKG-2 checkbox from `[ ]` to `[x]`.

- [ ] **Step 3: Run final verification**

Run the focused tests, full quality gate, and `git diff --check`. Confirm both
application EXEs and the versioned installer remain present under `dist/`.

- [ ] **Step 4: Commit documentation and task completion**

```powershell
git add README.md TASKS.md
git commit -m "docs: close Windows installer task"
```

- [ ] **Step 5: Inspect final state**

```powershell
git status --short --branch
git log -5 --oneline
Get-ChildItem dist -Filter 'EpiCase*.exe' | Select-Object Name, Length
```

Expected: clean `main`, committed installer sources and documentation, two
application EXEs, and one versioned installer EXE.
