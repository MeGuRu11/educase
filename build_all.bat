@echo off
setlocal

call "%~dp0build_constructor.bat"
if errorlevel 1 exit /b %ERRORLEVEL%

call "%~dp0build_player.bat"
exit /b %ERRORLEVEL%
