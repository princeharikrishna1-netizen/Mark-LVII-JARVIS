@echo off
title Stopping JARVIS Mark-LVII Pro...
taskkill /FI "WINDOWTITLE eq JARVIS Mark-LVII Pro - Hari*" /F >nul 2>&1
wmic process where "name='python.exe' and commandline like '%%main.py%%'" call terminate >nul 2>&1
echo JARVIS Mark-LVII Pro stopped cleanly, Hari.
timeout /t 2 /nobreak >nul
