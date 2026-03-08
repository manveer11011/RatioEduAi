@echo off
REM Run Electron desktop app.
cd /d "%~dp0\..\electron_app"
npm install 2>nul
npm run dev
