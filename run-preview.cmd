@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
    echo Double-click setup-windows.cmd first.
    pause
    exit /b 1
)
.venv\Scripts\python.exe windows_preview.py --output "%USERPROFILE%\OneDrive\Video"
if errorlevel 1 (
    echo Preview failed. Keep the error message above for troubleshooting.
    pause
    exit /b 1
)
pause
