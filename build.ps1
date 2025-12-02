# FaceIndex Local - Windows Build Script
# Development mode only - no standalone .exe yet

Write-Host "FaceIndex Local - Windows Build Script"
Write-Host "======================================="
Write-Host ""

# Check Python version
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python not found in PATH"
    Write-Host "Please install Python 3.8+ and ensure it's added to PATH"
    exit 1
}
Write-Host "Using: $pythonVersion"

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }
Get-ChildItem -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | Remove-Item -Force

# Create/activate virtual environment
Write-Host ""
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment"
        exit 1
    }
}

Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment"
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..."
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies"
    exit 1
}

Write-Host ""
Write-Host "Build complete! Development environment ready."
Write-Host ""
Write-Host "To run the application:"
Write-Host "  .\run.ps1"
Write-Host ""
Write-Host "Note: Windows .exe builds are not yet supported."
Write-Host "For now, run the application using the PowerShell script."
