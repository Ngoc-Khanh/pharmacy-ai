@echo off
echo Khoi dong FastAPI Development Server...
echo.
echo Virtual environment da kich hoat
echo.
call .\venv\Scripts\activate.bat
echo.
echo Cai dat/cap nhat dependencies...
pip install -r requirements.txt
echo.
echo Khoi dong server tai http://127.0.0.1:8000
echo Nhan Ctrl+C de dung server
echo.
uvicorn main:app --reload --host 127.0.0.1 --port 8000
