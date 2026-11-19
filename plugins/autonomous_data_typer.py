"""
JARVIS Plugin: Autonomous Human-Like Data Entry Bot (Level 11 Omniscience - 59/60)
Enters Hari's dictated data or harvested screen fields into ANY active website form, Excel sheet, or app with TAB progression.
"""
from __future__ import annotations
import json, subprocess, time
from pathlib import Path

HARVEST_FILE = Path("memory/harvested_data.json")

PLUGIN = {
    "name": "autonomous_data_typer",
    "description": "Autonomous Human-Like Data Entry Bot for ANY website form, Excel, or app.",
    "tier": "core",
    "brief": "Auto-types dictated or harvested fields into any active window with TAB progression.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'type_harvested', 'type_custom', or 'status'"},
            "data": {"type": "STRING", "description": "Comma-separated values to type in sequence."},
            "delay_sec": {"type": "INTEGER", "description": "Seconds to wait before typing (default 3)."}
        },
        "required": ["action"],
    },
}

def _escape_sendkeys(val: str) -> str:
    for ch in ("+", "^", "%", "~", "(", ")", "{", "}", "[", "]"):
        val = val.replace(ch, "{" + ch + "}")
    return val

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    raw_data = (parameters.get("data") or "").strip()
    delay = int(parameters.get("delay_sec") or 3)
    if act == "status":
        cnt = len(json.loads(HARVEST_FILE.read_text(encoding="utf-8")).get("values", [])) if HARVEST_FILE.exists() else 0
        reply = f"Hari, Autonomous Data Entry Bot ONLINE ({cnt} harvested field(s) staged in buffer)."
    else:
        if act == "type_custom" and raw_data:
            values = [v.strip() for v in raw_data.split(",") if v.strip()]
        elif HARVEST_FILE.exists():
            values = json.loads(HARVEST_FILE.read_text(encoding="utf-8")).get("values", [])
        else:
            values = []
        if not values:
            reply = "Hari, no data provided or harvested yet. Use 'harvest' or pass 'type: val1, val2'."
        else:
            time.sleep(max(1, min(delay, 8)))
            ps_lines = ["Add-Type -AssemblyName System.Windows.Forms"]
            for idx, v in enumerate(values):
                esc = _escape_sendkeys(str(v)).replace("'", "''")
                ps_lines.append(f"[System.Windows.Forms.SendKeys]::SendWait('{esc}')")
                ps_lines.append("Start-Sleep -Milliseconds 220")
                if idx < len(values) - 1:
                    ps_lines.append("[System.Windows.Forms.SendKeys]::SendWait('{TAB}')")
                    ps_lines.append("Start-Sleep -Milliseconds 180")
            subprocess.run(["powershell", "-NoProfile", "-Command", "; ".join(ps_lines)], capture_output=True, timeout=25)
            reply = f"Hari, Autonomous Data Entry COMPLETE: Typed {len(values)} field(s) with TAB progression!"
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
