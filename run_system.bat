@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "LLAMA_SERVER=%PROJECT_ROOT%llama\llama-b7108-bin-win-cpu-x64\llama-server.exe"
set "MODEL_PATH=%PROJECT_ROOT%models\qwen2.5-3b-instruct-q4_k_m.gguf"

echo [INFO] Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [INFO] Starting Llama Server...
start "Llama Server" /min "%LLAMA_SERVER%" -m "%MODEL_PATH%" -c 2048 --port 8080

echo [INFO] Waiting for server to initialize (10 seconds)...
timeout /t 10 /nobreak >nul

echo [INFO] Starting FastAPI Server...
start http://localhost:8081
python -m uvicorn api:app --host 127.0.0.1 --port 8081

echo [INFO] Shutting down...
taskkill /F /IM llama-server.exe >nul 2>&1
pause
endlocal
