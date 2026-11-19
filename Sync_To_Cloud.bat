@echo off
cd /d "%~dp0"
"C:\Program Files\Git\cmd\git.exe" add -A
"C:\Program Files\Git\cmd\git.exe" commit -m "Auto-Cloud Sync: JARVIS Mark-LVII snapshot" 2>nul
"C:\Program Files\Git\cmd\git.exe" push origin main
echo [JARVIS] All code synced to GitHub Cloud!
