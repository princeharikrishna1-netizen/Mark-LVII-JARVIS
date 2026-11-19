@echo off
cd /d "%~dp0"
echo [JARVIS Mark-LVII] Provisioning this laptop & creating Desktop shortcuts...
python -c "import plugins.desktop_shortcuts as d; print(d.run({'action':'force_create'})); import plugins.laptop_wakeword_daemon as l; print(l.run({'action':'mute_pc'}))"
call Start_JARVIS_HUD.bat
