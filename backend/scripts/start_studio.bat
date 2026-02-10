@echo off
echo Starting AI Agent Studio (Langflow)...
set PYTHONPATH=%~dp0;%PYTHONPATH%
.\venv\Scripts\langflow run --host 0.0.0.0 --port 7860 --components-path ".\langflow_components"
pause
