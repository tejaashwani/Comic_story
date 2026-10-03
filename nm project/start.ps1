# ComicCraft PowerShell Launch Script
Write-Host "===================================================" -ForegroundColor Yellow
Write-Host "  Starting ComicCraft AI Graphic Novel Studio..." -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "[Copying .env.example to .env...]" -ForegroundColor Gray
    Copy-Item ".env.example" ".env"
}

$pyCmd = "py"
try {
    $null = Get-Command py -ErrorAction Stop
} catch {
    $pyCmd = "python"
}

Write-Host "Launching server on http://127.0.0.1:8000 using $pyCmd..." -ForegroundColor Green
& $pyCmd run.py
