@echo off
REM Run the built AI Teacher executable.
cd /d "%~dp0\.."
if not exist "dist\AI-Teacher.exe" (
    echo Executable not found. Run: npm run build
    pause
    exit /b 1
)
start "" "dist\AI-Teacher.exe"
