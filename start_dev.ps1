# PowerShell script để khởi động FastAPI development server
Write-Host "Starting Pharmacy AI FastAPI Backend..." -ForegroundColor Green
Write-Host ""

# Kích hoạt virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Cài đặt/cập nhật dependencies
Write-Host "Installing/updating dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

Write-Host ""
Write-Host "Starting FastAPI server on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Red
Write-Host ""

# Khởi động server
uvicorn main:app --reload --host 127.0.0.1 --port 5000
