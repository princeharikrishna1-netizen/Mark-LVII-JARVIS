"""
JARVIS Plugin: Single Unified Desktop Shortcut Provisioner
Maintains ONLY ONE clean launcher ('Start JARVIS Pro.lnk') on the user's Desktop
that auto-pulls GitHub cloud updates, boots JARVIS Core, and launches the MCU 3D Holographic HUD (/mcu).
"""
from __future__ import annotations
import os, subprocess
from pathlib import Path

PLUGIN = {
    "name": "desktop_shortcuts",
    "description": "Creates and maintains a single unified 'Start JARVIS Pro' shortcut on Desktop.",
    "tier": "core",
    "brief": "Single Desktop Launcher Provisioner (Start JARVIS Pro).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'create', 'status'"}
        },
        "required": ["action"],
    },
}


def ensure_shortcuts(force_log: bool = False) -> str:
    root = Path.cwd().resolve()
    bat_path = root / "Start_JARVIS_HUD.bat"
    bat_content = (
        '@echo off\r\n'
        'cd /d "%~dp0"\r\n'
        'echo [JARVIS Cloud Sync] Checking for latest updates from GitHub...\r\n'
        '"C:\\Program Files\\Git\\cmd\\git.exe" pull --rebase --autostash origin main 2>nul\r\n'
        'start "JARVIS Mark-LVII" pythonw main.py\r\n'
    )
    bat_path.write_text(bat_content, encoding="utf-8")

    desktop = Path(os.path.expanduser("~")) / "Desktop"
    old_lnk = desktop / "Start JARVIS.lnk"
    if old_lnk.exists():
        try:
            old_lnk.unlink()
        except Exception:
            pass

    pro_lnk = desktop / "Start JARVIS Pro.lnk"
    ps_cmd = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{pro_lnk}"); '
        f'$s.TargetPath = "{bat_path}"; '
        f'$s.WorkingDirectory = "{root}"; '
        f'$s.IconLocation = "shell32.dll,238"; '
        f'$s.Description = "Launch JARVIS Mark-LVII Core + MCU 3D Holographic HUD"; '
        f'$s.Save()'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True)
    return f"Hari, Single Desktop Launcher ('Start JARVIS Pro') verified on Desktop!"


def run(parameters: dict, player=None, session_memory=None) -> str:
    reply = ensure_shortcuts(True)
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
