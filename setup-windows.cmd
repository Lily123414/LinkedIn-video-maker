@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 is required. Installing from the Windows package manager...
    winget install --id Python.Python.3.12 --exact --source winget --scope user --accept-source-agreements --accept-package-agreements
    echo Close this window, then double-click setup-windows.cmd again.
    pause
    exit /b 1
)
py -3.12 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m playwright install chromium
if errorlevel 1 goto fail
where ffmpeg >nul 2>&1
if errorlevel 1 (
    winget install --id Gyan.FFmpeg --exact --source winget --accept-source-agreements --accept-package-agreements
)
.venv\Scripts\python.exe -c "from windows_preview import find_ffmpeg; find_ffmpeg()"
if errorlevel 1 goto fail
echo Setup finished. Double-click run-preview.cmd to make your video.
pause
exit /b 0
:fail
echo Setup failed. Keep this error message for troubleshooting.
pause
exit /b 1
