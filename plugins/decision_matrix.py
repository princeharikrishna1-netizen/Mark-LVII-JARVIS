from __future__ import annotations
import psutil

PLUGIN = {
    "name": "decision_matrix",
    "description": "Independent Decision Engine. Scores urgency, risk, and system load to make real-time situational decisions. Trigger on 'make decision on [situation]' or 'evaluate situation [context]'.",
    "tier": "core",
    "brief": "Make real-time situational decisions using weighted scoring.",
    "parameters": {"type": "OBJECT", "properties": {"situation": {"type": "STRING"}, "urgency": {"type": "STRING"}}, "required": ["situation"]},
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    sit = (parameters.get("situation") or "standard operation").strip()
    urg = (parameters.get("urgency") or "medium").strip().lower()
    cpu = psutil.cpu_percent(interval=0.1)
    score = round(({"low": 30, "medium": 60, "high": 90}.get(urg, 60) * 0.6) + (max(10, 100 - cpu) * 0.4), 1)
    verdict = "PROCEED IMMEDIATELY" if score >= 70 else ("PROCEED WITH CHECKPOINTS" if score >= 45 else "DEFER & QUEUE")
    reply = f"Independent Decision for '{sit}', Hari [Score: {score}/100, CPU: {cpu}%]: {verdict}."
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
