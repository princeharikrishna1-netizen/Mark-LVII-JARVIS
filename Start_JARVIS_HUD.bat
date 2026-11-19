@echo off
cd /d "%~dp0"
echo [JARVIS Cloud Sync] Checking for latest updates from GitHub...
"C:\Program Files\Git\cmd\git.exe" pull --rebase --autostash origin main 2>nul
start "JARVIS Mark-LVII Core" python main.py
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000/mcu"
