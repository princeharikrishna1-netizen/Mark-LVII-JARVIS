@echo off
cd /d "%~dp0"
start "JARVIS Mark-LVII Core" python main.py
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000/autonomous"
