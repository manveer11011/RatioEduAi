# Build AI Teacher as a Windows executable.
Set-Location $PSScriptRoot\..
pip install -r requirements.txt -r requirements-build.txt -q 2>$null
pyinstaller AI-Teacher.spec
if ($LASTEXITCODE -eq 0) { Write-Host "Build complete. Run: npm run run-exe" }
