"""
JARVIS Plugin: Adaptive Behavior & Regional Telugu Persona Engine (#8)
Supports instant switching across Formal JARVIS, Rayalaseema, Telangana, and
East/West Godavari Telugu slang personas, plus context-aware modes.
"""
from __future__ import annotations
import json, psutil
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("memory/adaptive_state.json")
PERSONA_CYCLE = ["formal", "rayalaseema", "telangana", "godavari"]

PLUGIN = {
    "name": "adaptive_persona",
    "description": (
        "Adaptive Behavior & Regional Telugu Persona Engine. Switches JARVIS between 'formal', "
        "'rayalaseema' (Kadapa/Rayalaseema slang), 'telangana' (Hyderabad/Telangana slang), and "
        "'godavari' (East & West Godavari sweet/respectful slang), or context modes. Trigger on "
        "'rayalaseema mode', 'telangana mode', 'godavari mode', 'formal mode', or 'change persona'."
    ),
    "tier": "core",
    "brief": "Switch JARVIS between Formal, Rayalaseema, Telangana, and Godavari slang.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'set_mode', 'toggle', 'calibrate', or 'status'"},
            "mode": {"type": "STRING", "description": "Mode: 'formal', 'rayalaseema', 'telangana', 'godavari', 'work', 'coding', 'gaming', or 'auto'."}
        },
        "required": ["action"],
    },
}

RULES = {
    "formal": (
        "PERSONA ACTIVE: Formal Mark LVII JARVIS Mode. Address Hari politely with crisp, loyal, intelligent "
        "assistance in his preferred language (English/Telugu/Hinglish)."
    ),
    "rayalaseema": (
        "PERSONA ACTIVE: Rayalaseema Slang Mode (Kadapa style). Speak to Hari like a close Rayalaseema brother/friend "
        "using natural Rayalaseema Telugu slang matching his script (e.g., '???? ???, ?????????, ??????? ?????????, "
        "?????? ??????? ??, ??????????????'). Keep technical facts 100% accurate."
    ),
    "telangana": (
        "PERSONA ACTIVE: Telangana Slang Mode (Hyderabad/Telangana style). Speak to Hari warmly like a close dost "
        "using natural Telangana Telugu slang matching his script (e.g., '?????? ???, ?????? ????, ???? ????? ???????, "
        "??????????, ?? ????? ?????, ?????????'). Keep technical facts 100% accurate."
    ),
    "godavari": (
        "PERSONA ACTIVE: East & West Godavari Slang Mode (Konaseema/Rajahmundry/Bhimavaram style). Speak to Hari "
        "with signature Godavari warmth, sweet humor, and respectful '???? / ?????? / ????? ??? ????' flair "
        "(e.g., '????? ??? ????, ??? ???????? ????, ????? ????????? ?????, ??????? ????'). Keep technical facts 100% accurate."
    ),
    "high_load_concise": "Ultra-brief responses; defer heavy background scans.",
    "night_quiet": "Calm, concise tone; suppress non-critical alerts.",
    "work_precision": "High-accuracy, structured outputs optimized for registration & system automation tasks.",
    "gaming": "Minimal overlay interruptions; prioritize low latency for BGMI.",
    "coding": "Technical depth with direct code blocks and diagnostics.",
    "balanced_companion": "Warm, proactive assistance with standard telemetry.",
}

REPLIES = {
    "formal": "Formal JARVIS protocol restored, Hari. All systems operating at standard precision.",
    "rayalaseema": "???? ???! ??????? ???? ??? ?????? ????? ? ?? ????? ?? ??? ?????? ???? ??????? ??????????????!",
    "telangana": "?? ??? ????! ??????? ???? ???? ?????? ? ?? ??????? ?? ??????? ????? ??????????????!",
    "godavari": "????? ??? ????! ??????? (?????? & ?????? ???????) ???? ??? ???????? ? ?? ????????, ?????? ????? ????????? ?????!",
}


def get_current_mode() -> str:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("mode", "formal")
        except Exception:
            pass
    return "formal"


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "calibrate").strip().lower()
    mode = (parameters.get("mode") or "auto").strip().lower()
    if "east" in mode or "west" in mode or "godavari" in mode:
        mode = "godavari"
    elif "telangana" in mode or "hyd" in mode:
        mode = "telangana"
    elif "rayala" in mode or "kadapa" in mode:
        mode = "rayalaseema"

    try:
        cur = get_current_mode()
        if act == "toggle":
            idx = PERSONA_CYCLE.index(cur) if cur in PERSONA_CYCLE else 0
            chosen = PERSONA_CYCLE[(idx + 1) % len(PERSONA_CYCLE)]
        elif act == "set_mode" and mode != "auto":
            chosen = mode
        elif act == "status":
            chosen = cur
        else:
            hour = datetime.now().hour
            cpu = psutil.cpu_percent(interval=0.1)
            if cur in PERSONA_CYCLE:
                chosen = cur
            elif cpu > 80:
                chosen = "high_load_concise"
            elif hour >= 22 or hour < 6:
                chosen = "night_quiet"
            elif 9 <= hour <= 18:
                chosen = "work_precision"
            else:
                chosen = "balanced_companion"

        guideline = RULES.get(chosen, RULES["formal"])
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps({
            "mode": chosen,
            "guideline": guideline,
            "updated": datetime.now().strftime("%Y-%m-%d %I:%M %p")
        }, indent=2, ensure_ascii=False), encoding="utf-8")

        reply = REPLIES.get(chosen, f"Adaptive persona calibrated to '{chosen}' mode, Hari.")
    except Exception as e:
        reply = f"Adaptive persona error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
