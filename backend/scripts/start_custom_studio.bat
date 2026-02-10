@echo off
echo Starting Custom AI Studio...

:: Start Backend
start cmd /k "echo Starting Backend Engine... && .\venv\Scripts\python -m uvicorn backend.main:app --port 8001 --reload"

:: Start Frontend
start cmd /k "echo Starting Frontend Studio... && cd studio && npm run dev"

echo Backend: http://localhost:8001
echo Frontend: http://localhost:5173
pause
