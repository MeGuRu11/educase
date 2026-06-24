# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec для Player. Сборка: pyinstaller packaging/player.spec
# Запуск из корня репозитория.

a = Analysis(
    ["../src/epicase_player/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[("../src/epicase_core/theme/theme.qss", "epicase_core/theme")],
    hiddenimports=[],
    hookspath=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="EpiCase-Player",
    console=False,
    upx=False,
)
