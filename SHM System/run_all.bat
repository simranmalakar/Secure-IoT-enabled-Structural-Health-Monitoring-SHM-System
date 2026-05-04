@echo off
title SHM System — Launcher
color 0B

echo.
echo ============================================
echo   Secure IoT SHM System — Launching All
echo ============================================
echo.

:: Check Mosquitto
mosquitto -h >nul 2>&1
if errorlevel 1 (
    echo [!] Mosquitto not found in PATH.
    echo     Download from: https://mosquitto.org/download/
    echo     Install and add to PATH, then re-run this script.
    echo.
    echo     Continuing without Mosquitto - using default broker...
    echo.
) else (
    echo [1/4] Starting Mosquitto MQTT Broker...
    start "MQTT Broker" cmd /k "cd /d %~dp0 && mosquitto -c broker\mosquitto.conf"
    timeout /t 2 /nobreak >nul
)

echo [2/4] Starting Gateway (Edge Computing)...
start "SHM Gateway" cmd /k "cd /d %~dp0 && python -m gateway.gateway"
timeout /t 2 /nobreak >nul

echo [3/4] Starting FastAPI Backend...
start "SHM API Server" cmd /k "cd /d %~dp0 && uvicorn backend.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

echo [4/4] Starting Sensor Simulator...
start "SHM Sensors" cmd /k "cd /d %~dp0 && python -m sensor_simulator.simulator"
timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo   All services launched!
echo ============================================
echo.
echo   Dashboard:  http://localhost:8000/dashboard
echo   API Docs:   http://localhost:8000/docs
echo   Login:      admin / shm@secure2024
echo.
echo   Each service runs in its own window.
echo   Close this window anytime — services keep running.
echo   To stop all: close each service window individually.
echo.

:: Auto-open dashboard in browser
timeout /t 2 /nobreak >nul
start http://localhost:8000/dashboard

pause
