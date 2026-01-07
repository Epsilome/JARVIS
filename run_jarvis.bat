
@echo off
TITLE J.A.R.V.I.S.
echo ==================================================
echo       INITIALIZING J.A.R.V.I.S. PROTOCOL
echo ==================================================
cd /d "%~dp0"

:: Check for venv
if exist ".venv\Scripts\activate.bat" (
    echo Activating Virtual Environment...
    call .venv\Scripts\activate.bat
) else (
    echo No .venv found, attempting global python...
)

python -m assistant_app.interfaces.gui.main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] System Crash Detected.
    pause
)
