@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "INVENTORY_SOURCE=D:\Lily\Ankarsrum\Company Knowledge Hub"
set "INVENTORY_OUTPUT=%USERPROFILE%\OneDrive\Video"
if not exist "%INVENTORY_SOURCE%\" (
    echo Source folder not found: %INVENTORY_SOURCE%
    pause
    exit /b 1
)
if not exist "%INVENTORY_OUTPUT%\" (
    echo Report folder not found: %INVENTORY_OUTPUT%
    echo Choose an existing report folder outside the source by editing INVENTORY_OUTPUT in this launcher.
    pause
    exit /b 1
)
set "INVENTORY_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%INVENTORY_PYTHON%" set "INVENTORY_PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%INVENTORY_PYTHON%" goto run
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 is required. Install Python from https://www.python.org/downloads/windows/
    echo Then double-click inventory-windows.cmd again. Video tools and API keys are not required.
    pause
    exit /b 1
)
set "INVENTORY_PYTHON="
:run
for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss-fffffff"') do set "INVENTORY_STAMP=%%T"
if not defined INVENTORY_STAMP (
    echo Could not generate a unique report name. Nothing was scanned.
    pause
    exit /b 1
)
set "INVENTORY_REPORT=%INVENTORY_OUTPUT%\motor-media-inventory-%INVENTORY_STAMP%.csv"
echo Source: %INVENTORY_SOURCE%
echo New report: %INVENTORY_REPORT%
echo Only metadata will be read. Source files will not be changed.
if defined INVENTORY_PYTHON (
    "%INVENTORY_PYTHON%" media_inventory.py --source "%INVENTORY_SOURCE%" --output "%INVENTORY_REPORT%"
) else (
    py -3 media_inventory.py --source "%INVENTORY_SOURCE%" --output "%INVENTORY_REPORT%"
)
set "INVENTORY_RESULT=%ERRORLEVEL%"
if "%INVENTORY_RESULT%"=="0" explorer.exe /select,"%INVENTORY_REPORT%"
if not "%INVENTORY_RESULT%"=="0" echo Review the messages above. Do not assume the inventory is complete.
pause
exit /b %INVENTORY_RESULT%
