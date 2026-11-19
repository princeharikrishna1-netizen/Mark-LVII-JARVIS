"""
JARVIS Plugin: Multi-Device Smart Routines Automation Engine (Pro Level 6)
Executes multi-step coordinated routines across Windows 11 PC, Android Mobile, and JARVIS core:
- work_mode: PC diagnostics + mobile mute + episodic checkpoint
- night_guard: 24/7 watcher + self-healer + log rotation + self-promoter
- morning_briefing: Executive briefing + mobile battery/notifications + network check
- gaming_mode: Resource audit + mobile BGMI launch + watcher guard
"""
from __future__ import annotations

PLUGIN = {
    "name": "smart_routines",
    "description": (
        "Smart Routines Automation Engine. Runs coordinated multi-step workflows across PC and Android mobile: "
        "'work_mode', 'night_guard', 'morning_briefing', and 'gaming_mode'. "
        "Trigger on 'work mode', 'night guard', 'morning routine', 'gaming mode', or 'run routine'."
    ),
    "tier": "core",
    "brief": "Execute multi-device smart routines (Work Mode, Night Guard, Morning Briefing, Gaming Mode).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "routine": {
                "type": "STRING",
                "description": "One of: 'work_mode', 'night_guard', 'morning_briefing', 'gaming_mode', or 'list'"
            }
        },
        "required": ["routine"],
    },
}


def _safe_call(mod_name: str, params: dict) -> str:
    try:
        mod = __import__(f"plugins.{mod_name}", fromlist=["run"])
        return str(mod.run(params))
    except Exception as e:
        return f"[{mod_name}: {e}]"


def run(parameters: dict, player=None, session_memory=None) -> str:
    raw = (parameters.get("routine") or "list").strip().lower().replace(" ", "_")

    if raw in ("list", "status", "help"):
        reply = (
            "Hari, Available Smart Routines (4): "
            "1) work_mode (PC diagnostics + Mute Android + Episodic log) | "
            "2) night_guard (24/7 Watcher + Self-Healer + Log Rotation + Auto-Promote) | "
            "3) morning_briefing (Executive Briefing + Mobile Battery/Notifications) | "
            "4) gaming_mode (System check + Launch BGMI on Android)."
        )
    elif "work" in raw:
        s1 = _safe_call("master_orchestrator", {"action": "orchestrate", "goal": "PC diagnostics and workspace readiness", "urgency": "normal"})
        s2 = _safe_call("mobile_bridge", {"action": "key", "target": "mute"})
        _safe_call("episodic_briefing", {"action": "log", "category": "routine", "note": "Activated Work Mode routine"})
        reply = f"Hari, Work Mode Activated -> {s1} | Mobile: {s2}"

    elif "night" in raw or "guard" in raw:
        s1 = _safe_call("autonomous_watcher", {"action": "start"})
        s2 = _safe_call("self_healer", {"action": "heal"})
        s3 = _safe_call("log_rotation", {"action": "rotate"})
        s4 = _safe_call("self_promoter", {"action": "promote_all"})
        _safe_call("episodic_briefing", {"action": "log", "category": "routine", "note": "Activated Night Guard routine"})
        reply = f"Hari, Night Guard Mode Activated -> {s1} | {s2} | {s3} | {s4}"

    elif "morning" in raw or "brief" in raw:
        s1 = _safe_call("episodic_briefing", {"action": "briefing"})
        s2 = _safe_call("mobile_bridge", {"action": "battery"})
        s3 = _safe_call("mobile_bridge", {"action": "notifications"})
        reply = f"Hari, Morning Briefing Routine -> {s1} | {s2} | {s3}"

    elif "game" in raw or "gaming" in raw or "bgmi" in raw:
        s1 = _safe_call("log_rotation", {"action": "rotate"})
        s2 = _safe_call("mobile_bridge", {"action": "open_app", "target": "bgmi"})
        _safe_call("episodic_briefing", {"action": "log", "category": "routine", "note": "Activated Gaming Mode (BGMI)"})
        reply = f"Hari, Gaming Mode Activated -> {s1} | Mobile: {s2}"

    else:
        reply = f"Hari, unknown routine '{raw}'. Try: work_mode, night_guard, morning_briefing, or gaming_mode."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
