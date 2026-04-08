@echo off
setlocal EnableDelayedExpansion

REM VidAutoDown - Windows Startup Script
REM Creates venv, installs dependencies, and starts the application

cd /d "%~dp0"

echo ========================================
echo VidAutoDown - Video Downloader
echo ========================================
echo.

REM Kill any process using port 8765 (backend port)
echo Checking for existing backend process...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8765 ^| findstr LISTENING') do (
    echo Killing process %%a on port 8765...
    taskkill /F /PID %%a >nul 2>&1
)
echo.

REM Check if venv exists and is valid
if not exist "venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    if exist "venv" rd /s /q "venv"
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Please make sure Python 3.10+ is installed.
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

REM Install Python dependencies
echo Installing Python dependencies...
venv\Scripts\python.exe -m pip install --quiet --upgrade pip --disable-pip-version-check
venv\Scripts\python.exe -m pip install --quiet --disable-pip-version-check -r backend\requirements.txt
if errorlevel 1 (
    echo Failed to install Python dependencies.
    pause
    exit /b 1
)
echo Python dependencies installed.

echo Updating yt-dlp to latest version...
venv\Scripts\python.exe -m pip install --quiet --upgrade yt-dlp
echo.

REM Check Node.js
where node >nul 2>nul
if errorlevel 1 (
    echo Node.js not found. Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo Failed to install Node.js dependencies.
        pause
        exit /b 1
    )
    echo Node.js dependencies installed.
    echo.
)

REM Build frontend if not exists
if not exist "dist" (
    echo Building frontend...
    call npm run build
    if errorlevel 1 (
        echo Failed to build frontend.
        pause
        exit /b 1
    )
    echo Frontend built.
    echo.
)

REM Check for yt-dlp
where yt-dlp >nul 2>nul
if errorlevel 1 (
    echo WARNING: yt-dlp not found in PATH.
    echo It will be installed from requirements.txt.
    echo.
)

echo Starting VidAutoDown...
echo.

REM Start Electron
call npm start

endlocal