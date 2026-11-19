"""
JARVIS Plugin: Autonomous Thinking Engine (#1)
"""
from __future__ import annotations
import json, psutil
from datetime import datetime
from pathlib import Path

DECISIONS_FILE = Path("memory/autonomous_decisions.json")
LESSONS_FILE = Path("memory/lessons.json")

PLUGIN = {
    "name": "autonomous_mind",
    "description": "Autonomous Thinking Engine. Analyzes goals, weighs risks, consults past lessons, and decides optimal actions. Trigger on 'think autonomously about [goal]', 'decide what to do for [task]', or 'check autonomous decisions'.",
    "tier": "core",
    "brief": "Independently analyze goals, weigh risks, and decide optimal action paths.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'decide', 'history', or 'evaluate_risk'"},
            "goal": {"type": "STRING", "description": "The objective or situation to evaluate."}
        },
        "required": ["action"],
    },
}

def _load_json(path: Path) -> list:
    if not path.exists(): return []
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return []

def _save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "decide").strip().lower()
    goal = (parameters.get("goal") or "").strip()
    try:
        decisions = _load_json(DECISIONS_FILE)
        if act == "history":
            if not decisions:
                reply = "Sir, Autonomous Mind has no logged decisions yet."
            else:
                recent = list(reversed(decisions[-4:]))
                reply = "Recent autonomous decisions, Sir: " + " | ".join(f"[{d['timestamp']}] {d['goal']} -> {d['decision']}" for d in recent)
        elif not goal:
            reply = "Sir, provide a goal for my Autonomous Thinking engine to evaluate."
        else:
            cpu = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory().percent
            lessons = _load_json(LESSONS_FILE)
            relevant = [l["lesson"] for l in lessons if any(w in l.get("lesson", "").lower() for w in goal.lower().split() if len(w) > 3)][:2]
            needs_approval = any(k in goal.lower() for k in ("delete", "remove", "format", "shutdown", "wipe", "overwrite"))
            safety_tier = "GUARDED (Requires Hari's confirmation)" if needs_approval else "AUTONOMOUS (Safe to execute)"
            decision_text = f"Target='{goal}' | CPU {cpu}%, RAM {ram}% | Mode={safety_tier}"
            decisions.append({"id": len(decisions) + 1, "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "goal": goal, "safety_tier": safety_tier, "decision": decision_text})
            _save_json(DECISIONS_FILE, decisions)
            lesson_note = f" Past lesson applied: '{relevant[0]}'." if relevant else ""
            reply = f"Autonomous evaluation complete, Sir (CPU {cpu}%, RAM {ram}%). Mode: {safety_tier}.{lesson_note}"
    except Exception as e:
        reply = f"Sir, Autonomous Mind error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
