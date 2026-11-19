"""
JARVIS Plugin: Adaptive Behavior Engine (#8)
Dynamically calibrates response style, verbosity, and alert priority based on
time of day, system CPU/RAM load, and current user activity mode.
"""
from __future__ import annotations
import json, psutil
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("memory/adaptive_state.json")

PLUGIN = {
    "name": "adaptive_persona",
    "description": "Adaptive Behavior Engine. Adjusts JARVIS behavior mode (work, coding, gaming, night_quiet, high_load) based on context and system load. Trigger on 'adapt behavior to [mode]', 'auto calibrate behavior', or 'check adaptive mode'.",
    "tier": "core",
    "brief": "Adapt JARVIS tone, verbosity, and priority to your current situation.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'calibrate', 'set_mode', or 'status'"},
            "mode": {"type": "STRING", "description": "Optional mode: 'work', 'coding', 'gaming', 'night_quiet', or 'auto'."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "calibrate").strip().lower()
    mode = (parameters.get("mode") or "auto").strip().lower()
    try:
        hour = datetime.now().hour
        cpu = psutil.cpu_percent(interval=0.1)
        if act == "set_mode" and mode != "auto":
            chosen = mode
        elif cpu > 80:
            chosen = "high_load_concise"
        elif hour >= 22 or hour < 6:
            chosen = "night_quiet"
        elif 9 <= hour <= 18:
            chosen = "work_precision"
        else:
            chosen = "balanced_companion"

        rules = {
            "high_load_concise": "Ultra-brief responses; defer heavy background scans.",
            "night_quiet": "Calm, concise tone; suppress non-critical alerts.",
            "work_precision": "High-accuracy, structured outputs optimized for coding & system automation tasks.",
            "gaming": "Minimal overlay interruptions; prioritize low latency.",
            "coding": "Technical depth with direct code blocks and diagnostics.",
            "balanced_companion": "Warm, proactive assistance with standard telemetry.",
        }
        guideline = rules.get(chosen, rules["balanced_companion"])
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({"mode": chosen, "guideline": guideline, "updated": datetime.now().strftime("%Y-%m-%d %I:%M %p")}, indent=2), encoding="utf-8")
        reply = f"Adaptive Behavior calibrated to '{chosen}' (CPU {cpu}%), Sir. Policy: {guideline}"
    except Exception as e:
        reply = f"Sir, Adaptive Behavior error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
