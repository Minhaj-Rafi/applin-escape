@echo off
setlocal
cd /d "%~dp0"
title Build Applin Escape for Windows
set "BUILD_PY=py -3"
py -3 -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if errorlevel 1 (
    set "BUILD_PY=python"
    python -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
    if errorlevel 1 goto failed
)
if not exist ".build-venv\Scripts\python.exe" (
    %BUILD_PY% -m venv .build-venv
    if errorlevel 1 goto failed
)
".build-venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed
".build-venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean ApplinEscape.spec
if errorlevel 1 goto failed
echo.
set "SDL_VIDEODRIVER=dummy"
set "SDL_AUDIODRIVER=dummy"
start "" /wait "dist\ApplinEscape\ApplinEscape.exe" --preview build-preview --verify-build
if errorlevel 1 goto failed
if not exist "build-preview\controls.png" goto failed
set "SDL_VIDEODRIVER="
set "SDL_AUDIODRIVER="
echo Build and bundled-asset smoke check complete. Open dist\ApplinEscape\ApplinEscape.exe
echo Share the ENTIRE dist\ApplinEscape folder, including _internal.
echo Players of that build do not need Python installed.
explorer "dist\ApplinEscape"
pause
exit /b 0
:failed
echo Build failed. Check the error above. Python 3.10+ and internet are needed to build.
pause
exit /b 1
