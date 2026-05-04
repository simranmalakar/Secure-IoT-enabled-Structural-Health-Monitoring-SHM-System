@echo off
title Secure IoT SHM System — Setup
color 0A

echo.
echo ============================================
echo   Secure IoT SHM System — Windows Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo         Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Install dependencies
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo       Done.
echo.

:: Generate TLS certs
echo [2/4] Generating TLS certificates...
python generate_certs.py
echo.

:: Check Mosquitto
echo [3/4] Checking Mosquitto...
mosquitto -h >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Mosquitto not found in PATH.
    echo           Download from: https://mosquitto.org/download/
    echo           After installing, add to PATH and restart this script.
    echo.
    echo           Alternatively, start Mosquitto manually:
    echo           mosquitto -c broker\mosquitto.conf
    echo.
) else (
    echo       Mosquitto found.
)
echo.

:: Instructions
echo [4/4] Setup Complete!
echo.
echo ============================================
echo   HOW TO RUN (open 4 terminals):
echo ============================================
echo.
echo   Terminal 1 — MQTT Broker:
echo     mosquitto -c broker\mosquitto.conf
echo.
echo   Terminal 2 — Gateway:
echo     python -m gateway.gateway
echo.
echo   Terminal 3 — API Server:
echo     uvicorn backend.main:app --reload --port 8000
echo.
echo   Terminal 4 — Sensor Simulator:
echo     python -m sensor_simulator.simulator
echo.
echo   Dashboard:
echo     http://localhost:8000/dashboard
echo     Login: admin / shm@secure2024
echo.
echo ============================================
echo.

pause
