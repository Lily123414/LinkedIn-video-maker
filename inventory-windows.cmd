@echo off
setlocal
cd /d "%~dp0"
echo Read-only media inventory. Python is not required.
echo Source: D:\Lily\Ankarsrum\Company Knowledge Hub
echo Report folder: %USERPROFILE%\Downloads
echo Only a new CSV will be written; source files will not be changed.
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File "%~dp0inventory-windows.ps1"
set "INVENTORY_RESULT=%ERRORLEVEL%"
if not "%INVENTORY_RESULT%"=="0" (
    echo Review the message above. Do not assume the inventory is complete.
)
pause
exit /b %INVENTORY_RESULT%
