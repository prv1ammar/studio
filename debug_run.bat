@echo off
echo ===================================================
echo     TYBOO STUDIO - POWER LAUNCHER 🚀
echo ===================================================
echo.

echo [1/3] Checking Backend & Installing Dependencies...
if not exist "venv\Scripts\python.exe" (
    echo Python venv not found! Creating one...
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
if exist "backend\requirements_extra.txt" pip install -r backend\requirements_extra.txt

echo [2/3] Starting Backend (Port 8001)...
start "Tyboo Backend" cmd /k "venv\Scripts\activate && python -m uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8001 --reload"

echo [3/3] Starting Frontend (Port 5173)...
cd studio
if not exist "node_modules" (
    echo Installing Frontend Dependencies...
    call npm install
)
start "Tyboo Frontend" cmd /k "npm run dev"

echo.
echo ===================================================
echo     SERVERS DEPLOYED!
echo.
echo     STUDIO URL: http://localhost:5173
echo     BACKEND URL: http://localhost:8001
echo.
echo     Keep both terminal windows OPEN.
echo ===================================================
pause
