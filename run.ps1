# One-Command Startup for Rakshak AI Project
# Run with: powershell -ExecutionPolicy Bypass -File run.ps1

$venvPath = "D:/vs code/best AI project/.venv"
$pythonExe = "$venvPath/Scripts/python.exe"
$projectDir = "D:\vs code\best AI project\rakshak-ai"
$requirementsFile = "$projectDir\requirements.txt"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Rakshak AI - One Command Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python executable exists
if (-not (Test-Path $pythonExe)) {
    Write-Host "Error: Virtual environment not found at $venvPath" -ForegroundColor Red
    exit 1
}

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
& $pythonExe -m pip install -q -r $requirementsFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Start the Flask app
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Starting Rakshak AI Flask Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The application will be available at:" -ForegroundColor Green
Write-Host "  http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Set-Location $projectDir
& $pythonExe app.py

