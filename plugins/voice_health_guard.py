"""
JARVIS Plugin: Proactive Error & Audio Watchdog (Level 6 Supreme - 34/34)
Continuously guards Windows audio endpoints, network connectivity, and runtime error resilience:
- check: Inspects Windows active audio playback/capture devices + internet DNS/HTTPS reachability
- start_guard: Runs lightweight 45s background health monitor logging anomalies without crashing main.py
"""
from __future__ import annotations
import socket
import subprocess
import threading
import time

_GUARD_ACTIVE = False
_LAST_HEALTH = {"audio": "UNKNOWN", "internet": "UNKNOWN", "checked_at": "never"}

PLUGIN = {
    "name": "voice_health_guard",
    "description": (
        "Proactive Error & Audio Watchdog. Monitors Windows audio devices and internet reachability "
        "to prevent PortAudio/network crashes and enable graceful silent fallback. "
        "Trigger on 'audio health', 'voice guard', 'mic check', or 'connection guard'."
    ),
    "tier": "core",
    "brief": "Proactive audio hardware & network resilience watchdog.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'check', 'start_guard', or 'status'"
            }
        },
        "required": ["action"],
    },
}


def _probe_health() -> dict:
    audio_state = "NO_DEVICE"
    try:
        ps = (
            "Get-CimInstance Win32_SoundDevice | Where-Object {$_.Status -eq 'OK'} | "
            "Select-Object -ExpandProperty Name"
        )
        p = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=8)
        devs = [d.strip() for d in (p.stdout or "").splitlines() if d.strip()]
        if devs:
            audio_state = f"OK ({', '.join(devs[:2])})"
    except Exception as e:
        audio_state = f"FALLBACK_SILENT ({e})"

    net_state = "OFFLINE"
    try:
        with socket.create_connection(("generativelanguage.googleapis.com", 443), timeout=4):
            net_state = "ONLINE (Gemini API Reachable)"
    except Exception:
        net_state = "DEGRADED (Offline/Firewall)"

    _LAST_HEALTH["audio"] = audio_state
    _LAST_HEALTH["internet"] = net_state
    _LAST_HEALTH["checked_at"] = time.strftime("%H:%M:%S")
    return dict(_LAST_HEALTH)


def _guard_loop() -> None:
    prev_net = ""
    while True:
        try:
            st = _probe_health()
            if prev_net and st["internet"] != prev_net:
                import plugins.episodic_briefing as eb
                eb.log_event("health_guard", f"Network state changed: {prev_net} -> {st['internet']}")
            prev_net = st["internet"]
        except Exception:
            pass
        time.sleep(45)


def start_background_guard() -> str:
    global _GUARD_ACTIVE
    if not _GUARD_ACTIVE:
        _GUARD_ACTIVE = True
        _probe_health()
        t = threading.Thread(target=_guard_loop, name="JARVIS-VoiceHealthGuard", daemon=True)
        t.start()
    return f"Hari, Voice & Network Health Guard ACTIVE ({_LAST_HEALTH['audio']} | {_LAST_HEALTH['internet']})."


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "check").strip().lower()
    try:
        if act == "start_guard":
            reply = start_background_guard()
        else:
            st = _probe_health()
            reply = (
                f"Hari, Proactive Audio & Network Guard ({'ACTIVE' if _GUARD_ACTIVE else 'ON-DEMAND'} | "
                f"Checked {st['checked_at']}): Audio={st['audio']} | Network={st['internet']}."
            )
    except Exception as e:
        reply = f"Hari, Voice Health Guard error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
