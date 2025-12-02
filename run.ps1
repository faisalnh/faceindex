# FaceIndex Local - Windows PowerShell Run Script
# This script sets up the environment and runs the application

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment"
        Write-Host "Please ensure Python 3.8+ is installed and in PATH"
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to activate virtual environment"
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser"
    exit 1
}

# Install/update dependencies if requirements.txt exists and is newer than last install
if (Test-Path "requirements.txt") {
    $requirementsTime = (Get-Item "requirements.txt").LastWriteTime
    $markerFile = "venv\.requirements_installed"

    if (-not (Test-Path $markerFile) -or (Get-Item $markerFile).LastWriteTime -lt $requirementsTime) {
        Write-Host "Installing dependencies..."
        pip install -r requirements.txt
        if ($LASTEXITCODE -eq 0) {
            New-Item -ItemType File -Path $markerFile -Force | Out-Null
        }
    }
}

# Run the application
Write-Host "Starting FaceIndex Local..."
python main.py
