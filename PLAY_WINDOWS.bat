@echo off
setlocal
cd /d "%~dp0"
title Applin Escape

echo.
echo   APPLIN ESCAPE - HOMEWARD 4.2
echo   First launch sets up a private Python environment.
echo.

set "GAME_PY=py -3"
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if errorlevel 1 (
    set "GAME_PY=python"
    python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
    if errorlevel 1 goto missing_python
)

if not exist ".venv\Scripts\python.exe" (
    %GAME_PY% -m venv .venv
    if errorlevel 1 goto setup_failed
)

".venv\Scripts\python.exe" -c "import pygame; assert pygame.version.ver == '2.6.1'" >nul 2>nul
if errorlevel 1 (
    echo Installing Pygame. Internet is needed only for this first setup.
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_failed
)

".venv\Scripts\python.exe" launch.py
if errorlevel 1 (
    echo.
    echo The game stopped with an error. Please copy the message above.
    pause
)
exit /b

:missing_python
echo Python 3.10 or newer was not found.
echo Install Python with the Python launcher and pip enabled, then try again.
pause
exit /b 1

:setup_failed
echo.
echo Setup did not complete. Check the message above and your internet connection.
echo Extract the entire ZIP into a writable folder before launching.
pause
exit /b 1
