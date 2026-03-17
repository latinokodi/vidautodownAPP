@echo off
setlocal
title Run VidAutoDown
color 0A

cd /d "%~dp0"

REM Check if valid venv exists (for Windows cmd)
if not exist "venv\Scripts\activate.bat" (
    if exist "venv" (
        echo ============================================
        echo    Invalid virtual environment detected.
        echo    Recreating venv for Windows...
        echo ============================================
        rmdir /s /q "venv"
    ) else (
        echo ============================================
        echo    Creating virtual environment...
        echo ============================================
    )

    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

REM Activate venv
call "venv\Scripts\activate.bat"
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/Update dependencies
echo ============================================
echo    Updating dependencies...
echo ============================================
python -m pip install --upgrade pip
pip install --upgrade -r requirements.txt

REM Ensure yt-dlp is latest (critical for video downloads)
echo ============================================
echo    Updating yt-dlp to latest...
echo ============================================
pip install --upgrade yt-dlp

REM Check for aria2c
if not exist "venv\Scripts\aria2c.exe" (
    echo ============================================
    echo    Downloading aria2c...
    echo ============================================
    powershell -Command "$url = 'https://github.com/aria2/aria2/releases/download/release-1.37.0/aria2-1.37.0-win-64bit-build1.zip'; $out = 'aria2.zip'; Invoke-WebRequest -Uri $url -OutFile $out; Expand-Archive -Path $out -DestinationPath .; Move-Item -Path 'aria2-1.37.0-win-64bit-build1\aria2c.exe' -Destination 'venv\Scripts\aria2c.exe'; Remove-Item -Path $out -Force; Remove-Item -Path 'aria2-1.37.0-win-64bit-build1' -Recurse -Force"
    if exist "venv\Scripts\aria2c.exe" (
        echo    aria2c installed successfully.
    ) else (
        echo    WARNING: Failed to install aria2c.
    )
)

REM Check for PhantomJS (required for some sites like Pornhub model pages)
if not exist "venv\Scripts\phantomjs.exe" (
    echo ============================================
    echo    Downloading PhantomJS...
    echo ============================================
    powershell -Command "$url = 'https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-windows.zip'; $out = 'phantomjs.zip'; Invoke-WebRequest -Uri $url -OutFile $out; Expand-Archive -Path $out -DestinationPath .; Move-Item -Path 'phantomjs-2.1.1-windows\bin\phantomjs.exe' -Destination 'venv\Scripts\phantomjs.exe'; Remove-Item -Path $out -Force; Remove-Item -Path 'phantomjs-2.1.1-windows' -Recurse -Force"
    if exist "venv\Scripts\phantomjs.exe" (
        echo    PhantomJS installed successfully.
    ) else (
        echo    WARNING: Failed to install PhantomJS. Some sites may not work.
    )
)

echo ============================================
echo    Starting VidAutoDown (WebView)...
echo ============================================
python vidautodown_webview.py

endlocal
pause
