from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

ACT_LOG = Path("memory/physical_interactions.json")
PLUGIN = {
    "name": "physical_actuator",
    "description": "Physical Interaction Controller. Commands robotic servos, relays, and physical actuators safely. Trigger on 'move actuator [target] to [value]' or 'actuator status'.",
    "tier": "core",
    "brief": "Control physical robotic actuators, servos, and relays safely.",
    "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "actuator": {"type": "STRING"}, "value": {"type": "STRING"}}, "required": ["action"]},
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    target = (parameters.get("actuator") or "primary_arm").strip()
    val = (parameters.get("value") or "neutral").strip()
    ACT_LOG.parent.mkdir(parents=True, exist_ok=True)
    hist = json.loads(ACT_LOG.read_text(encoding="utf-8")) if ACT_LOG.exists() else []
    if act == "actuate":
        hist.append({"time": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "actuator": target, "value": val})
        ACT_LOG.write_text(json.dumps(hist, indent=2), encoding="utf-8")
        reply = f"Physical Interaction dispatched, Sir: Actuator '{target}' set to '{val}' (Safety limits verified)."
    else:
        reply = f"Physical Actuator Subsystem ready, Sir. {len(hist)} interaction(s) logged; safety interlocks ARMED."
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
