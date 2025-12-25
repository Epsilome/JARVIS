# reset_dev_env.ps1

Write-Host "🛑 Stopping python processes to release file locks..." -ForegroundColor Yellow
Stop-Process -Name "python" -ErrorAction SilentlyContinue
Stop-Process -Name "assistant" -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

$VENV_DIR = ".venv"

if (Test-Path $VENV_DIR) {
    Write-Host "🗑️ Removing old virtual environment..." -ForegroundColor Yellow
    Remove-Item -Path $VENV_DIR -Recurse -Force
}

Write-Host "✨ Creating new virtual environment..." -ForegroundColor Green
python -m venv $VENV_DIR

Write-Host "🔌 Activating venv..." -ForegroundColor Green
& ".\$VENV_DIR\Scripts\Activate.ps1"

Write-Host "📦 Installing dependencies (Editable Mode)..." -ForegroundColor Green
python -m pip install --upgrade pip
pip install -e .

Write-Host "✅ Done! Environment reset." -ForegroundColor Cyan
Write-Host "👉 Please CLOSE this terminal and open a new one to ensure paths are refreshed." -ForegroundColor Cyan
