"""
Drop-in JARVIS plugin for setting, listing, and querying female voice profiles.
"""
from __future__ import annotations

from core.tts import get_female_voices, get_current_voice, set_female_voice

PLUGIN = {
    "name": "female_voice",
    "description": (
        "Manage or select female text-to-speech voices for JARVIS. "
        "Actions: list (show available female voices), set (configure the best or a specific female voice), "
        "query (show the currently active voice)."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "enum": ["list", "set", "query"],
                "description": "Action to perform: list available voices, set a female voice, or query current voice."
            },
            "voice_name": {
                "type": "STRING",
                "description": "Optional specific voice name when setting (e.g. Aoede, Kore, Leda, Aria, Zira)."
            }
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str(parameters.get("action") or "query").strip().lower()
    voice_name = str(parameters.get("voice_name") or "").strip()

    try:
        if action == "list":
            voices = get_female_voices()
            if not voices:
                return "No female voices were detected on this system."
            preview = ", ".join(voices[:10])
            if len(voices) > 10:
                preview += f" (and {len(voices) - 10} more)"
            result_text = f"Available female voices: {preview}."

        elif action == "set":
            if voice_name:
                from memory.config_manager import update_config
                # Preserve all other settings; save only the selected TTS voice.
                update_config(tts_voice=voice_name)
                chosen = voice_name
            else:
                chosen = set_female_voice()
            result_text = f"Female voice successfully set to {chosen}."

        elif action == "query":
            current = get_current_voice()
            result_text = f"The currently active TTS voice is {current}."

        else:
            result_text = f"Unknown action '{action}' for female_voice plugin."

    except Exception as e:
        result_text = f"Sir, female_voice failed: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {result_text}")
        except Exception:
            pass

    return result_text
