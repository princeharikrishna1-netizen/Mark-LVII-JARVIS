"""
JARVIS Plugin: Autonomous Action-Ask-Sleep-Wake Loop Warden (62/62)
Tracks active conversational command loop state ('ACTIVE_LISTENING' vs 'SLEEP_WAKEWORD_ONLY'),
speaks post-action confirmation ('Next em cheyamantav Hari?'), and enforces 60s silence sleep.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("memory/loop_warden_state.json")

PLUGIN = {
    "name": "autonomous_loop_warden",
    "description": (
        "Manages JARVIS continuous Action -> 'Next em cheyamantav?' -> 60s Auto-Sleep -> 'JARVIS' Wake-Word loop."
    ),
    "tier": "core",
    "brief": "Continuous voice action loop with 1-minute auto-sleep & 'JARVIS' wake-word.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'wake', 'sleep', 'stop', or 'status'"}
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if act == "wake":
        STATE_FILE.write_text(json.dumps({"state": "ACTIVE_LISTENING", "updated": now, "idle_timeout_sec": 60}, indent=2), encoding="utf-8")
        reply = "Yes Hari, I am active! Cheppandi, next em cheyamantav?"
    elif act == "sleep":
        STATE_FILE.write_text(json.dumps({"state": "SLEEP_WAKEWORD_ONLY", "updated": now, "idle_timeout_sec": 60}, indent=2), encoding="utf-8")
        reply = "Hari, 1 minute no response ? entering Sleep Mode. Say 'JARVIS' anytime to wake me up."
    elif act == "stop":
        STATE_FILE.write_text(json.dumps({"state": "STOPPED", "updated": now}, indent=2), encoding="utf-8")
        reply = "Hari, continuous action loop stopped."
    else:
        st = json.loads(STATE_FILE.read_text(encoding="utf-8")).get("state", "READY") if STATE_FILE.exists() else "READY"
        reply = f"Hari, Autonomous Loop Warden ONLINE (State: {st} | Auto-Sleep: 60s | Wake-Word: 'JARVIS')."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
