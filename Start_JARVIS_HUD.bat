@echo off
cd /d "%~dp0"
echo [JARVIS Cloud Sync] Checking for latest updates from GitHub...
"C:\Program Files\Git\cmd\git.exe" pull --rebase --autostash origin main 2>nul
start "JARVIS Mark-LVII" pythonw main.py
