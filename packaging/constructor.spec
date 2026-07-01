# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec для Constructor. Сборка: pyinstaller packaging/constructor.spec
# Пути вычисляются от расположения spec-файла.

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).parent.resolve()
SRC = PROJECT_ROOT / "src"
UI_RESOURCES = SRC / "epicase_ui" / "resources"
APP_ICONS = UI_RESOURCES / "app_icons"

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
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="EpiCase Constructor",
    console=False,
    upx=False,
    icon=str(APP_ICONS / "epicase_constructor.ico"),
)
