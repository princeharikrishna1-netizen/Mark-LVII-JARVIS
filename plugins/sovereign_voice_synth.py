"""
JARVIS Plugin: Sovereign Voice TTS Synthesizer (Level 10 Apotheosis - 56/56)
Uses Windows native System.Speech.Synthesis (zero external dependency) to speak JARVIS responses
directly through PC speakers on demand.
"""
from __future__ import annotations
import subprocess

PLUGIN = {
    "name": "sovereign_voice_synth",
    "description": (
        "Sovereign Voice TTS Synthesizer. Speaks text aloud on Windows 11 speakers using native "
        "System.Speech without external dependencies. "
        "Trigger on 'speak', 'say aloud', 'voice announce', or 'tts'."
    ),
    "tier": "core",
    "brief": "Zero-dependency Windows native spoken voice synthesizer.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'speak', or 'status'"
            },
            "text": {
                "type": "STRING",
                "description": "Message to speak aloud."
            }
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "speak").strip().lower()
    text = (parameters.get("text") or "Hari, Mark 57 Level 10 Apotheosis 56 of 56 systems online and ready.").strip()
    safe_txt = text.replace("'", " ").replace('"', " ")[:350]

    if act == "speak":
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Rate = 1; "
            f"$s.Speak('{safe_txt}');"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps])
        reply = f"Hari, Sovereign Voice Synth speaking aloud: '{safe_txt[:90]}...'"
    else:
        reply = "Hari, Sovereign Voice TTS Synthesizer ONLINE (Windows SAPI Neural Ready)."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
