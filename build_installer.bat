@echo off
setlocal

set "ROOT=%~dp0"
pushd "%ROOT%" >nul || exit /b 1

call "%ROOT%build_all.bat"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" goto finish

set "PYTHON=python"
if exist "%ROOT%.venv\Scripts\python.exe" set "PYTHON=%ROOT%.venv\Scripts\python.exe"

set "APP_VERSION="
for /f "usebackq delims=" %%V in (`"%PYTHON%" -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION goto version_missing

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
