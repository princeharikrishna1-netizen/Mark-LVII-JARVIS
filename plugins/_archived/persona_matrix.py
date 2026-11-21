"""
JARVIS Plugin: Sovereign Voice & Persona Matrix (Level 9 Transcendence - 51/52)
Switches J.A.R.V.I.S. active response style between:
1) 'jarvis_classic' (Refined British Tactical AI)
2) 'rayalaseema_mass' (Kadapa Rayalaseema Telugu-English Companion)
3) 'igrs_legal' (Strict Property Registration & Legal Precision Mode)
"""
from __future__ import annotations
import json
from pathlib import Path

PERSONA_FILE = Path("memory/active_persona.json")

MODES = {
    "jarvis_classic": "Classic Tactical J.A.R.V.I.S. (Crisp, futuristic engineering precision addressing Hari).",
    "rayalaseema_mass": "Kadapa Rayalaseema Companion (Warm, energetic, royal Rayalaseema Telugu-English vibe for Hari).",
    "igrs_legal": "IGRS & Property Legal Precision Mode (Formal registration, EC, stamp duty & Legal-size formatting focus).",
}

PLUGIN = {
    "name": "persona_matrix",
    "description": (
        "Sovereign Voice & Persona Matrix. Switches JARVIS personality between 'jarvis_classic', "
        "'rayalaseema_mass', and 'igrs_legal'. "
        "Trigger on 'persona', 'switch mode', 'rayalaseema mode', or 'legal mode'."
    ),
    "tier": "core",
    "brief": "Live personality & dialect mode switcher (Classic / Rayalaseema / IGRS Legal).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'set', 'cycle', or 'status'"
            },
            "mode": {
                "type": "STRING",
                "description": "Target mode: 'jarvis_classic', 'rayalaseema_mass', or 'igrs_legal'"
            }
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    mode = (parameters.get("mode") or "").strip().lower()
    PERSONA_FILE.parent.mkdir(parents=True, exist_ok=True)

    cur = "jarvis_classic"
    if PERSONA_FILE.exists():
        try:
            cur = json.loads(PERSONA_FILE.read_text(encoding="utf-8")).get("mode", cur)
        except Exception:
            pass

    keys = list(MODES.keys())
    if act == "cycle":
        cur = keys[(keys.index(cur) + 1) % len(keys)] if cur in keys else keys[0]
        PERSONA_FILE.write_text(json.dumps({"mode": cur, "description": MODES[cur]}, indent=2), encoding="utf-8")
        reply = f"Hari, Persona Matrix cycled to [{cur}]: {MODES[cur]}"
    elif act == "set" and mode in MODES:
        cur = mode
        PERSONA_FILE.write_text(json.dumps({"mode": cur, "description": MODES[cur]}, indent=2), encoding="utf-8")
        reply = f"Hari, Persona Matrix locked to [{cur}]: {MODES[cur]}"
    else:
        reply = f"Hari, Active Persona: [{cur}] -> {MODES.get(cur, MODES['jarvis_classic'])}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
