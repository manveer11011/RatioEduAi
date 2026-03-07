@echo off
REM Build AI Teacher as a Windows executable.
cd /d "%~dp0\.."
pip install -r requirements.txt -r requirements-build.txt -q 2>nul
pyinstaller AI-Teacher.spec
if %errorlevel% equ 0 (
    echo Build complete. Run: npm run run-exe
) else (
    echo Build failed.
    pause
)
