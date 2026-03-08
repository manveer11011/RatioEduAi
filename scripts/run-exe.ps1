# Run the built AI Teacher executable.
Set-Location $PSScriptRoot\..
$exe = "dist\AI-Teacher.exe"
if (-not (Test-Path $exe)) {
    Write-Host "Executable not found. Run: npm run build"
    exit 1
}
Start-Process $exe
