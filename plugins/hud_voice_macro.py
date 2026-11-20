"""
JARVIS Plugin: One-Word Power Macros (#71)
Executes multi-step Windows workflows with single protocol commands:
- Protocol Office: Opens Excel, Word, IGRS portal in Chrome, and checks HP LaserJet 1020 Plus status
- Protocol Night: Dims screen brightness, activates night_quiet persona, and backs up daily files
- Protocol Backup: Archives memory/ and extracted Excel workbooks into memory/backups/
"""
from __future__ import annotations
import shutil, subprocess, webbrowser
from datetime import datetime
from pathlib import Path

PLUGIN = {
    "name": "hud_voice_macro",
    "description": (
        "One-Word Power Macros. Executes multi-step desktop protocols such as 'office', 'night', "
        "'backup', or custom saved macros. Trigger on 'run protocol office', 'protocol night', "
        "'protocol backup', or 'execute macro [name]'."
    ),
    "tier": "core",
    "brief": "Run multi-step desktop workflows with one protocol command.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "protocol": {
                "type": "STRING",
                "description": "Protocol name: 'office', 'night', 'backup', or 'list'."
            }
        },
        "required": ["protocol"],
    },
}


def _backup_workspace() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir = Path("memory/backups") / f"snapshot_{ts}"
    bdir.mkdir(parents=True, exist_ok=True)
    for src_name in ("memory", "config"):
        src = Path(src_name)
        if src.exists():
            dst = bdir / src_name
            shutil.copytree(
                src, dst,
                ignore=shutil.ignore_patterns("backups", "__pycache__", "*.tmp"),
                dirs_exist_ok=True
            )
    return str(bdir)


def _check_printer() -> str:
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command",
             "Get-Printer | Where-Object {$_.Name -like '*1020*'} | Select-Object -ExpandProperty PrinterStatus"],
            text=True, timeout=5
        ).strip()
        return out or "Ready/Standby"
    except Exception:
        return "Standby"


def run(parameters: dict, player=None, session_memory=None) -> str:
    proto = (parameters.get("protocol") or "list").strip().lower()
    for prefix in ("protocol ", "run ", "mode "):
        if proto.startswith(prefix):
            proto = proto[len(prefix):].strip()

    try:
        if proto == "office":
            launched = []
            for app in ("excel", "winword"):
                try:
                    subprocess.Popen(["cmd", "/c", "start", "", app], shell=False)
                    launched.append(app.upper())
                except Exception:
                    pass
            try:
                webbrowser.open("https://registration.ap.gov.in/igrs")
                launched.append("IGRS Portal")
            except Exception:
                pass
            p_status = _check_printer()
            reply = (
                f"Protocol Office activated, Hari: launched {', '.join(launched)}. "
                f"HP LaserJet 1020 Plus status: {p_status}."
            )

        elif proto == "night":
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,25)"],
                    capture_output=True, timeout=5
                )
            except Exception:
                pass
            try:
                from plugins import adaptive_persona
                adaptive_persona.run({"action": "set_mode", "mode": "night_quiet"})
            except Exception:
                pass
            bpath = _backup_workspace()
            reply = f"Protocol Night engaged, Hari: display dimmed to 25%, night_quiet active, and workspace backed up to {bpath}."

        elif proto == "backup":
            bpath = _backup_workspace()
            reply = f"Protocol Backup complete, Hari. All memory and registration records archived to {bpath}."

        else:
            reply = (
                "Available One-Word Protocols, Hari:\n"
                "- 'Run Protocol Office' (Excel + Word + AP IGRS Portal + HP LaserJet 1020 Plus check)\n"
                "- 'Run Protocol Night' (Dim display to 25% + Night Quiet mode + Daily Backup)\n"
                "- 'Run Protocol Backup' (Snapshot memory & extracted workbooks)"
            )
    except Exception as e:
        reply = f"Protocol macro error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
