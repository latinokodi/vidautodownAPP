@echo off
setlocal
title VidAutoDown Launcher
color 0A

cd /d "%~dp0"

echo ============================================
echo    VidAutoDown Setup ^& Launch
echo ============================================

REM 1. Backend Setup
echo [Setup] Checking backend environment...
if not exist "backend\venv" (
    echo [Setup] Creating Python virtual environment...
    python -m venv backend\venv
    if errorlevel 1 (
        echo [Error] Failed to create venv. Is Python installed and in your PATH?
        pause
        goto :eof
    )
)

echo [Setup] Installing/Updating backend dependencies...
if exist "backend\venv\Scripts\python.exe" (
    "backend\venv\Scripts\python.exe" -m pip install --upgrade pip
    "backend\venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
) else (
    echo [Error] Python executable not found in venv!
    pause
    goto :eof
)

REM 2. Frontend Setup
echo.
echo [Setup] Checking frontend dependencies...
if not exist "frontend\node_modules" (
    echo [Setup] Installing frontend dependencies...
    cd frontend
    call npm install
    if errorlevel 1 (
        echo [Error] npm install failed. Is Node.js installed?
        cd ..
        pause
        goto :eof
    )
    cd ..
)

REM 3. Launch
echo.
echo [Launch] Starting Application...
echo ============================================

if exist "backend\venv\Scripts\python.exe" (
    "backend\venv\Scripts\python.exe" run_all.py
) else (
    echo [Error] Cannot find python interpreter to run orchestrator.
)

if errorlevel 1 (
    echo.
    echo [Error] Application crashed or exited with an error.
)

echo.
echo [Info] Application process finished.
pause
