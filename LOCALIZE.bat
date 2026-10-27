@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PY=py"
where py >nul 2>nul
if errorlevel 1 set "PY=python"

"%PY%" scripts\menu.py %*
if errorlevel 1 pause
endlocal
