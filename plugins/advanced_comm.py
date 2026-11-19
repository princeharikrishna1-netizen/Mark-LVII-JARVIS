from __future__ import annotations

PLUGIN = {
    "name": "advanced_comm",
    "description": "Advanced Communication Synthesizer. Shapes messages into natural human-like briefings or conversational updates. Trigger on 'communicate [message] in [style] style' or 'format briefing [info]'.",
    "tier": "core",
    "brief": "Synthesize natural human-like communication tailored to context.",
    "parameters": {"type": "OBJECT", "properties": {"message": {"type": "STRING"}, "style": {"type": "STRING"}}, "required": ["message"]},
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    msg = (parameters.get("message") or "").strip()
    style = (parameters.get("style") or "conversational").strip().lower()
    if style == "executive":
        reply = f"Executive Brief, Sir: {msg} - All primary metrics remain nominal."
    elif style == "technical":
        reply = f"Technical Telemetry Readout, Sir: [{msg}] | Status=VERIFIED."
    else:
        reply = f"Here is the status update, Sir: {msg}. Ready for your next instruction."
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
