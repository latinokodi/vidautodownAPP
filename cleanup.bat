@echo off
echo Killing VidAutoDown processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul

echo.
echo Deleting stale lock files...
if exist "frontend\.next\dev\lock" (
    del "frontend\.next\dev\lock"
    echo Removed frontend lock file.
)

echo.
echo Done. cleanup complete.
pause
