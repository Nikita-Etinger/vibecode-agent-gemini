@echo off
chcp 65001 > nul
title Local Agent Zero-Click Bridge

echo ====================================================
echo    Local Agent Zero-Click Bridge (Windows 11)       
echo ====================================================
echo.

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ and add it to system PATH.
    pause
    exit /b 1
)

echo [*] Checking dependencies...
python -m pip install -q -r requirements.txt

echo [*] Starting GUI Agent and API Bridge...
python agent_gui.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Agent stopped with an error.
    pause
)
