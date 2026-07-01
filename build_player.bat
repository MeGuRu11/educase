@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=python"
if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"

pushd "%ROOT%" >nul || exit /b 1
"%PYTHON%" -m PyInstaller --clean --noconfirm --distpath dist --workpath build\player packaging\player.spec
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
