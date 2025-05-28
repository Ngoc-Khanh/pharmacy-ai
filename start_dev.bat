@echo off
echo Starting FastAPI Development Server...
echo.
echo Virtual environment activated
echo.
call .\venv\Scripts\activate.bat
echo.
echo Installing/updating dependencies...
pip install -r requirements.txt
echo.
echo Starting server on http://127.0.0.1:8000
echo Press Ctrl+C to stop the server
echo.
uvicorn main:app --reload --host 127.0.0.1 --port 8000
