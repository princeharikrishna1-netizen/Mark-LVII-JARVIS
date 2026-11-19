"""
JARVIS Plugin: Human Understanding & Affective Analysis
Detects user emotional tone, stress, urgency, and cognitive load from interaction cues
to calibrate empathy and pacing.
"""
from __future__ import annotations

PLUGIN = {
    "name": "human_understanding",
    "description": "Human Understanding Engine. Detects emotional state, stress, urgency, or mood from user input and recommends supportive communication calibration. Trigger on 'analyze mood [text]', 'detect user emotion [input]', or 'empathy check'.",
    "tier": "core",
    "brief": "Understand human emotion, stress, and intent to calibrate responses.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'analyze_tone', or 'calibrate_empathy'"},
            "input_text": {"type": "STRING", "description": "User message or behavior cue to interpret."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    text = (parameters.get("input_text") or "").lower().strip()
    try:
        if any(w in text for w in ("urgent", "asap", "fast", "hurry", "error", "crash", "stuck", "frustrated")):
            state, pacing = "High Urgency / Elevated Stress", "Keep responses direct, calm, and action-first."
        elif any(w in text for w in ("tired", "exhausted", "sleepy", "bored", "sad", "low")):
            state, pacing = "Low Energy / Fatigue", "Use warm, supportive tone and reduce cognitive load."
        elif any(w in text for w in ("awesome", "great", "super", "happy", "excited", "build", "upgrade")):
            state, pacing = "High Momentum / Creative Focus", "Match enthusiasm with proactive technical depth."
        else:
            state, pacing = "Calm / Focused", "Maintain clear, collaborative, and balanced interaction."
        reply = f"Human Understanding Assessment, Sir: Detected state='{state}'. Interaction strategy: {pacing}"
    except Exception as e:
        reply = f"Sir, Human Understanding error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
