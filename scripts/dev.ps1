# Run Electron desktop app.
Set-Location $PSScriptRoot\..\electron_app
npm install 2>$null
npm run dev
