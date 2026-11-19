"""
JARVIS Plugin: Cross-Machine Desktop Shortcut Auto-Provisioner
Automatically creates 'Start JARVIS.lnk' and 'Start JARVIS Pro.lnk' on the current Windows machine's
Desktop pointing directly to this repository's local path (works on any laptop or PC after git clone).
"""
from __future__ import annotations
import subprocess
from pathlib import Path

PLUGIN = {
    "name": "desktop_shortcuts",
    "description": "Auto-creates 'Start JARVIS' and 'Start JARVIS Pro' shortcuts on any laptop/PC Desktop.",
    "tier": "core",
    "brief": "Auto-provisions Desktop launch shortcuts on any Windows machine.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'ensure', 'force_create', or 'status'"}
        },
        "required": ["action"],
    },
}


def ensure_shortcuts(force: bool = False) -> str:
    repo_dir = Path(".").resolve()
    bat_file = repo_dir / "Start_JARVIS_HUD.bat"
    if not bat_file.exists():
        bat_file.write_text(
            '@echo off\r\ncd /d "%~dp0"\r\n"C:\\Program Files\\Git\\cmd\\git.exe" pull --rebase --autostash origin main 2>nul\r\nstart "JARVIS Mark-LVII Core" python main.py\r\n'
            'timeout /t 3 /nobreak >nul\r\nstart "" "http://127.0.0.1:8000/mcu"\r\n',
            encoding="utf-8",
        )

    ps = (
        "$ws = New-Object -ComObject WScript.Shell; "
        "$desk = [Environment]::GetFolderPath('Desktop'); "
        "$created = @(); "
        "foreach ($name in @('Start JARVIS.lnk', 'Start JARVIS Pro.lnk')) { "
        "  $lnk = Join-Path $desk $name; "
        f"  $need = {'$true' if force else '$false'}; "
        "  if (-not (Test-Path $lnk)) { $need = $true } "
        "  else { "
        "    $existing = $ws.CreateShortcut($lnk); "
        f"    if ($existing.TargetPath -ne '{bat_file}') {{ $need = $true }} "
        "  } "
        "  if ($need) { "
        "    $sc = $ws.CreateShortcut($lnk); "
        f"    $sc.TargetPath = '{bat_file}'; "
        f"    $sc.WorkingDirectory = '{repo_dir}'; "
        "    $sc.IconLocation = 'shell32.dll,21'; "
        "    $sc.Description = 'Launch JARVIS Mark-LVII (62/62 Omniscience + Autonomous HUD)'; "
        "    $sc.Save(); "
        "    $created += $name; "
        "  } "
        "} "
        "if ($created.Count -gt 0) { Write-Output ('Created/Updated: ' + ($created -join ', ')) } "
        "else { Write-Output 'Verified on Desktop' }"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=10)
    return (r.stdout or r.stderr or "OK").strip()


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "ensure").strip().lower()
    res = ensure_shortcuts(force=(act == "force_create"))
    reply = f"Hari, Desktop Shortcuts ({res}) -> Ready on this machine's Desktop!"
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
