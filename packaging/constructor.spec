# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec для Constructor. Сборка: pyinstaller packaging/constructor.spec
# Запуск из корня репозитория.

a = Analysis(
    ["../src/epicase_constructor/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("../src/epicase_core/theme/theme.qss", "epicase_core/theme"),
        ("../src/epicase_constructor/resources/icons", "epicase_constructor/resources/icons"),
    ],
    hiddenimports=[],
    hookspath=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="EduCase-Constructor",
    console=False,       # GUI: без консольного окна
    upx=False,
)
