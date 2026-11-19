"""Switch the Gemini Live assistant voice and Custom AI Persona from a tool call.

The action loader contract calls handlers as fn(parameters=<tool args>, ...).
Keep that contract while accepting the existing gender/voice arguments and persona styles.
"""
from __future__ import annotations
from memory.config_manager import AVAILABLE_VOICES, save_voice

_GENDER_VOICES = {
    "male": ("Charon", "Puck", "Fenrir"),
    "female": ("Kore", "Aoede"),
}


def switch_voice(parameters=None, player=None, gender=None, voice="", persona="", **_context) -> str:
    """Persist a selected Gemini Live voice or switch custom AI persona and refresh the active session."""
    args = parameters if isinstance(parameters, dict) else {}
    requested_persona = str(persona or args.get("persona") or "").strip().lower()
    
    if requested_persona:
        if "rayalaseema" in requested_persona or "local" in requested_persona:
            msg = "Persona switched to Rayalaseema Slang mode, Hari! ఇక నుంచి మన లోకల్ స్టైల్‌లోనే మాట్లాడతా."
        elif "professional" in requested_persona or "strict" in requested_persona:
            msg = "Persona switched to Professional mode. Systems operating at peak efficiency, Sir."
        else:
            msg = f"Persona updated to '{requested_persona}' mode successfully, Hari."
        
        if player:
            player.write_log(f"JARVIS: {msg}")
        return msg

    requested_gender = str(gender or args.get("gender") or "").strip().lower()
    requested_voice = str(voice or args.get("voice") or "").strip()

    if requested_voice and not requested_gender:
        requested_gender = next(
            (g for g, names in _GENDER_VOICES.items()
             if any(name.lower() == requested_voice.lower() for name in names)),
            "",
        )
    if requested_gender not in _GENDER_VOICES:
        return "Choose male or female voice, or specify Kore, Aoede, Charon, Puck, or Fenrir, or a persona style."

    choices = _GENDER_VOICES[requested_gender]
    if requested_voice:
        selected = next((name for name in choices if name.lower() == requested_voice.lower()), None)
        if selected is None:
            return f"{requested_voice} is not a {requested_gender} Gemini voice. Available: {', '.join(choices)}."
    else:
        selected = choices[0]

    if selected not in AVAILABLE_VOICES:
        return f"{selected} is not enabled in this project configuration."

    save_voice(selected)
    callback = getattr(player, "on_voice_change", None) if player is not None else None
    if callable(callback):
        callback()
    return f"Gemini Live voice changed to {selected} ({requested_gender})."


TOOL = {
    "name": "switch_assistant_voice",
    "description": (
        "Switch JARVIS Gemini Live voice or custom AI persona style. "
        "Use gender='female' for Kore or gender='male' for Charon, or specify 'persona' "
        "(e.g., 'rayalaseema', 'professional') to change the response tone."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "gender": {"type": "STRING", "enum": ["male", "female"]},
            "voice": {"type": "STRING", "description": "Optional exact Gemini voice name."},
            "persona": {"type": "STRING", "description": "Optional custom persona style (e.g., rayalaseema, professional)."}
        },
    },
    "handler": switch_voice,
}