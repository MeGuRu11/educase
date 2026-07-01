"""Контракт Windows-сборок PyInstaller и пользовательских batch-скриптов."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGING = ROOT / "packaging"
APP_ICONS = SRC / "epicase_ui" / "resources" / "app_icons"


@dataclass(frozen=True)
class CapturedCall:
    """Аргументы одного вызова конструктора из spec-файла."""

    args: tuple[object, ...]
    kwargs: dict[str, object]


class FakeAnalysis:
    """Минимальный заменитель PyInstaller Analysis для проверки конфигурации."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.call = CapturedCall(args, kwargs)
        self.pure: list[object] = []
        self.scripts: list[object] = []
        self.binaries: list[object] = []
        self.datas: list[object] = []


class FakeBuildTarget:
    """Минимальный заменитель PyInstaller PYZ и EXE."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        self.call = CapturedCall(args, kwargs)


@dataclass(frozen=True)
class ExpectedSpec:
    """Ожидаемый контракт одного приложения."""

    filename: str
    entrypoint: str
    excluded_package: str
    executable_name: str
    icon_name: str
    data_files: frozenset[tuple[str, str]]


EXPECTED_SPECS = (
    ExpectedSpec(
        filename="constructor.spec",
        entrypoint="epicase_constructor/__main__.py",
        excluded_package="epicase_player",
        executable_name="EpiCase Constructor",
        icon_name="epicase_constructor.ico",
        data_files=frozenset(
            {
                ("src/epicase_core/theme/theme.qss", "epicase_core/theme"),
                ("src/epicase_ui/resources", "epicase_ui/resources"),
                (
                    "src/epicase_constructor/resources/icons",
                    "epicase_constructor/resources/icons",
                ),
            }
        ),
    ),
    ExpectedSpec(
        filename="player.spec",
        entrypoint="epicase_player/__main__.py",
        excluded_package="epicase_constructor",
        executable_name="EpiCase Player",
        icon_name="epicase_player.ico",
        data_files=frozenset(
            {
                ("src/epicase_core/theme/theme.qss", "epicase_core/theme"),
                ("src/epicase_ui/resources", "epicase_ui/resources"),
            }
        ),
    ),
)


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


@pytest.mark.parametrize("expected", EXPECTED_SPECS)
def test_spec_builds_one_file_gui_with_expected_resources(
    expected: ExpectedSpec,
) -> None:
    source, analysis, executable = _execute_spec(expected.filename)
    expected_entrypoint = SRC / expected.entrypoint
    expected_datas = {
        (str(ROOT / source_path), destination)
        for source_path, destination in expected.data_files
    }

    assert analysis.call.args[0] == [str(expected_entrypoint)]
    assert analysis.call.kwargs["pathex"] == [str(SRC)]
    assert analysis.call.kwargs["excludes"] == [expected.excluded_package]

    datas = cast(list[tuple[str, str]], analysis.call.kwargs["datas"])
    assert set(datas) == expected_datas
    assert all(Path(path).exists() for path, _ in datas)

    icon = Path(cast(str, executable.call.kwargs["icon"]))
    assert icon == APP_ICONS / expected.icon_name
    assert icon.exists()
    assert executable.call.kwargs["name"] == expected.executable_name
    assert executable.call.kwargs["console"] is False
    assert executable.call.kwargs["upx"] is False
    assert "COLLECT(" not in source


@pytest.mark.parametrize(
    ("filename", "spec_filename", "work_directory"),
    (
        ("build_constructor.bat", "constructor.spec", "build\\constructor"),
        ("build_player.bat", "player.spec", "build\\player"),
    ),
)
def test_individual_batch_build_is_location_independent(
    filename: str,
    spec_filename: str,
    work_directory: str,
) -> None:
    path = ROOT / filename
    assert path.exists()
    source = path.read_text(encoding="utf-8")

    assert 'set "ROOT=%~dp0"' in source
    assert ".venv\\Scripts\\python.exe" in source
    assert 'pushd "%ROOT%"' in source
    assert '"%PYTHON%" -m PyInstaller --clean --noconfirm' in source
    assert "--distpath dist" in source
    assert f"--workpath {work_directory}" in source
    assert f"packaging\\{spec_filename}" in source
    assert "exit /b %EXIT_CODE%" in source


def test_build_all_batch_calls_both_builds_and_stops_on_first_error() -> None:
    path = ROOT / "build_all.bat"
    assert path.exists()
    source = path.read_text(encoding="utf-8")
    constructor_call = 'call "%~dp0build_constructor.bat"'
    player_call = 'call "%~dp0build_player.bat"'

    assert source.index(constructor_call) < source.index(player_call)
    assert "if errorlevel 1 exit /b %ERRORLEVEL%" in source
    assert source.rstrip().endswith("exit /b %ERRORLEVEL%")
