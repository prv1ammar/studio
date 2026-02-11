@echo off
echo 🚀 Preparation de AI Agent Studio...

:: 1. Backend Setup
echo 🐍 Configuration du Backend Python...
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

:: 2. Frontend Setup
echo ⚛️ Configuration du Frontend React...
cd studio
npm install
cd ..

:: 3. Lancement
echo 🌟 Tout est prêt ! Lancement des serveurs...
start cmd /k "call venv\Scripts\activate && python -m uvicorn backend.app.api.main:app --host 0.0.0.0 --port 8001"
start cmd /k "cd studio && npm run dev"

echo ✅ Le Studio est disponible sur http://localhost:5173
pause
