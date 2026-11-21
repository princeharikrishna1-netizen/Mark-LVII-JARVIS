"""
JARVIS Plugin: Continuous Background Screen Co-Pilot Daemon (Level 11 Omniscience - 60/60)
Continuously observes ANY website/app Hari works on every 25s, logging advice and speaking short voice alerts.
"""
from __future__ import annotations
import json, threading, time
from datetime import datetime
from pathlib import Path

FEED_FILE = Path("memory/copilot_live_feed.json")
_RUNNING = False

PLUGIN = {
    "name": "copilot_daemon",
    "description": "Continuous Background Screen Co-Pilot Daemon across all websites & apps.",
    "tier": "core",
    "brief": "Background continuous screen observation & voice suggestion loop.",
    "parameters": {
        "type": "OBJECT",
        "properties": {"action": {"type": "STRING", "description": "One of: 'start', 'stop', 'feed', or 'status'"}},
        "required": ["action"],
    },
}

def _loop():
    global _RUNNING
    import plugins.live_screen_mentor as lsm
    while _RUNNING:
        try:
            res = lsm.run({"action": "observe", "speak_alert": True})
            FEED_FILE.parent.mkdir(parents=True, exist_ok=True)
            FEED_FILE.write_text(json.dumps({"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "advice": res}, indent=2), encoding="utf-8")
        except Exception:
            pass
        for _ in range(25):
            if not _RUNNING:
                break
            time.sleep(1)

def run(parameters: dict, player=None, session_memory=None) -> str:
    global _RUNNING
    act = (parameters.get("action") or "status").strip().lower()
    if act == "start":
        if not _RUNNING:
            _RUNNING = True
            threading.Thread(target=_loop, daemon=True).start()
        reply = "Hari, Live Screen Co-Pilot Daemon STARTED (Observing ANY website/app every 25s with voice alerts)."
    elif act == "stop":
        _RUNNING = False
        reply = "Hari, Live Screen Co-Pilot Daemon STOPPED."
    elif act == "feed" and FEED_FILE.exists():
        d = json.loads(FEED_FILE.read_text(encoding="utf-8"))
        reply = f"Hari, Latest Co-Pilot Observation [{d.get('timestamp')}]:\n{d.get('advice')}"
    else:
        reply = f"Hari, Live Screen Co-Pilot Daemon is {'RUNNING (Active Watch)' if _RUNNING else 'STANDBY (Ready to Start)'}."
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
