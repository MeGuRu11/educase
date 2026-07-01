# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec для Player. Сборка: pyinstaller packaging/player.spec
# Пути вычисляются от расположения spec-файла.

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).parent.resolve()
SRC = PROJECT_ROOT / "src"
UI_RESOURCES = SRC / "epicase_ui" / "resources"
APP_ICONS = UI_RESOURCES / "app_icons"

a = Analysis(
    [str(SRC / "epicase_player" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[
        (
            str(SRC / "epicase_core" / "theme" / "theme.qss"),
            "epicase_core/theme",
        ),
        (str(UI_RESOURCES), "epicase_ui/resources"),
    ],
    hiddenimports=[],
    hookspath=[],
    excludes=["epicase_constructor"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="EpiCase Player",
    console=False,
    upx=False,
    icon=str(APP_ICONS / "epicase_player.ico"),
)
