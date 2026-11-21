"""
JARVIS Plugin: Smart Screen Data Harvester (Level 11 Omniscience - 58/60)
Extracts structured key-value fields from ANY visible website, PDF, table, or form into memory/harvested_data.json.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

HARVEST_FILE = Path("memory/harvested_data.json")

PLUGIN = {
    "name": "screen_data_harvester",
    "description": "Smart Screen Data Harvester for ANY website, PDF, or form.",
    "tier": "core",
    "brief": "Extracts structured fields from any screen/site for instant auto-typing.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'harvest', 'show', or 'save_custom'"},
            "custom_fields": {"type": "STRING", "description": "Optional comma-separated values dictated by Hari."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "harvest").strip().lower()
    custom = (parameters.get("custom_fields") or "").strip()
    HARVEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    if act == "save_custom" and custom:
        items = [x.strip() for x in custom.split(",") if x.strip()]
        HARVEST_FILE.write_text(json.dumps({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "Hari_Dictated", "values": items}, indent=2), encoding="utf-8")
        reply = f"Hari, saved {len(items)} dictated field(s) ready for Auto-Data Entry: {items}"
    elif act == "show" and HARVEST_FILE.exists():
        d = json.loads(HARVEST_FILE.read_text(encoding="utf-8"))
        reply = f"Hari, Harvested Data Buffer ({d.get('timestamp')}): {d.get('values')}"
    else:
        import plugins.live_screen_mentor as lsm
        key = lsm._get_key()
        if not key:
            reply = "Hari, Gemini API key missing for Screen Data Harvester."
        else:
            shot = lsm._capture_screen()
            prompt = (
                "Extract all key form/table/website/document values visible on this screen as a clean JSON array of strings "
                "in logical tab-entry order. Return ONLY the raw JSON array, no markdown."
            )
            raw = lsm._vision_analyze(shot, prompt, key).replace("```json", "").replace("```", "").strip()
            try:
                vals = json.loads(raw)
                if not isinstance(vals, list):
                    vals = [str(vals)]
            except Exception:
                vals = [line.strip("-? ") for line in raw.splitlines() if line.strip()][:12]
            HARVEST_FILE.write_text(json.dumps({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "Screen_Vision_OCR", "values": vals}, indent=2), encoding="utf-8")
            reply = f"Hari, Screen Data Harvester extracted {len(vals)} field(s): {vals[:8]}"
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
