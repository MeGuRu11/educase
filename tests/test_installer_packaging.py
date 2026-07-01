"""Контракт современного Windows-установщика EpiCase."""

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
    assert (
        'Name: "constructor"; Description: "EpiCase Constructor"; '
        "Types: full constructor"
    ) in source
    assert (
        'Name: "player"; Description: "EpiCase Player"; Types: full player'
    ) in source
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
    assert 'for /f "delims=" %%V in (\'^""%PYTHON%" -c ' in source
    assert '^"\') do set "APP_VERSION=%%V"' in source
    assert "usebackq" not in source
    assert "if not defined APP_VERSION goto version_missing" in source
    assert "Inno Setup 6 is required" in source
    assert '"/DAppVersion=%APP_VERSION%"' in source
    assert '"packaging\\installer.iss"' in source
    assert 'set "EXIT_CODE=2"' in source
    assert 'set "EXIT_CODE=3"' in source
    assert "exit /b %EXIT_CODE%" in source
