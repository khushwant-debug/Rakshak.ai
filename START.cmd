@echo off
REM One-Command Startup for Rakshak AI Project
REM This script installs dependencies and starts the Flask app

setlocal enabledelayedexpansion

set VENV_PATH=%~dp0.venv
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe
set PROJECT_DIR=%~dp0rakshak-ai

echo.
echo ========================================
echo   Rakshak AI - One Command Startup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "%PYTHON_EXE%" (
    echo Error: Virtual environment not found at %VENV_PATH%
    echo Please ensure Python virtual environment is set up.
    pause
    exit /b 1
)

REM Install/update dependencies
echo Installing dependencies...
"%PYTHON_EXE%" -m pip install -q -r "%PROJECT_DIR%\requirements.txt"

if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

REM Start the Flask app
echo.
echo ========================================
echo   Starting Rakshak AI Flask Server...
echo ========================================
echo.
echo The application will be available at:
echo   http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd /d "%PROJECT_DIR%"
"%PYTHON_EXE%" app.py

pause
