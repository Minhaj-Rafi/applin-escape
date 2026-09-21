@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" save_recovery.py
) else (
  py -3 save_recovery.py
)
pause
