from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

MODEL_FILE = Path("memory/adaptive_models.json")
PLUGIN = {
    "name": "advanced_learning",
    "description": "Advanced Learning Engine. Adapts operational heuristics to new situations and workloads. Trigger on 'adapt to situation [context]', 'update learning profile [rule]', or 'learning status'.",
    "tier": "core",
    "brief": "Adapt operational heuristics dynamically to new situations.",
    "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "situation": {"type": "STRING"}, "adjustment": {"type": "STRING"}}, "required": ["action"]},
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "adapt").strip().lower()
    sit = (parameters.get("situation") or "general_runtime").strip()
    adj = (parameters.get("adjustment") or "Optimize latency and accuracy").strip()
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    prof = json.loads(MODEL_FILE.read_text(encoding="utf-8")) if MODEL_FILE.exists() else {}
    if act == "status":
        reply = f"Advanced Learning Engine: {len(prof)} adaptive profile(s) active, Sir."
    else:
        prof[sit] = {"adjustment": adj, "confidence": min(0.99, prof.get(sit, {}).get("confidence", 0.75) + 0.05), "updated": datetime.now().strftime("%Y-%m-%d %I:%M %p")}
        MODEL_FILE.write_text(json.dumps(prof, indent=2), encoding="utf-8")
        reply = f"Advanced Learning adapted to '{sit}' (Confidence: {int(prof[sit]['confidence']*100)}%), Sir."
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
