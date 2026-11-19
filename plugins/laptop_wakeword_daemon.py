"""
JARVIS Plugin: Hardware-Adaptive Laptop Mic & "JARVIS" Wake-Word Engine
Auto-detects if an audio input (microphone) device exists on the current machine:
- Laptop (mic present): Enables live mic input + "JARVIS" wake-word -> Action -> "Next em cheyamantav?" -> 60s sleep.
- PC (no mic present): Keeps mic muted in clean Output-only mode with zero PortAudio errors.
"""
from __future__ import annotations
import json
from pathlib import Path

CFG_FILE = Path("memory/audio_device_profile.json")

PLUGIN = {
    "name": "laptop_wakeword_daemon",
    "description": "Auto-enables live microphone & 'JARVIS' wake-word on Laptop while keeping PC muted.",
    "tier": "core",
    "brief": "Hardware-adaptive Laptop Mic & 'JARVIS' Wake-Word engine.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'detect', 'enable_laptop_mic', or 'mute_pc'"}
        },
        "required": ["action"],
    },
}


def has_microphone() -> tuple[bool, str]:
    try:
        import sounddevice as sd
        devs = sd.query_devices()
        inputs = [d["name"] for d in devs if d.get("max_input_channels", 0) > 0]
        if inputs:
            return True, inputs[0]
    except Exception:
        pass
    return False, "None"


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "detect").strip().lower()
    CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
    mic_ok, dev_name = has_microphone()

    if act == "mute_pc" or (act == "detect" and not mic_ok):
        CFG_FILE.write_text(json.dumps({"mic_enabled": False, "mode": "PC_MUTED", "device": dev_name}, indent=2), encoding="utf-8")
        reply = "Hari, PC Mode active (0 mic inputs detected -> Mic Muted, Output-only safe mode)."
    else:
        CFG_FILE.write_text(json.dumps({"mic_enabled": True, "mode": "LAPTOP_JARVIS_WAKEWORD", "device": dev_name, "wake_word": "jarvis", "sleep_sec": 60}, indent=2), encoding="utf-8")
        reply = f"Hari, Laptop Mic & 'JARVIS' Wake-Word ENABLED on [{dev_name}]! Say 'JARVIS' anytime to command."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
