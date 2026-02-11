@echo off
echo STARTING BACKEND...
start "Backend" cmd /k "venv\Scripts\activate && python -m uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8001"
echo STARTING FRONTEND...
cd studio
start "Frontend" cmd /k "npm run dev -- --host"
echo DONE.
