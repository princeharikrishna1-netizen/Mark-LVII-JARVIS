"""
JARVIS Plugin: Self-Learning Engine (#2)
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

LESSONS_FILE = Path("memory/lessons.json")

PLUGIN = {
    "name": "self_learner",
    "description": "Self-Learning Engine. Records corrections and lessons from experience so JARVIS never repeats errors. Trigger on 'learn from this [lesson]', 'record lesson [rule]', or 'what have you learned'.",
    "tier": "core",
    "brief": "Learn from corrections and operational experience to avoid repeating mistakes.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'learn', 'recall', 'list', or 'stats'"},
            "lesson": {"type": "STRING", "description": "The rule or lesson learned."},
            "context": {"type": "STRING", "description": "Domain like 'system', 'coding', or 'general'."}
        },
        "required": ["action"],
    },
}

def _load_lessons() -> list[dict]:
    if not LESSONS_FILE.exists(): return []
    try: return json.loads(LESSONS_FILE.read_text(encoding="utf-8"))
    except Exception: return []

def _save_lessons(items: list[dict]) -> None:
    LESSONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LESSONS_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "list").strip().lower()
    lesson = (parameters.get("lesson") or "").strip()
    context = (parameters.get("context") or "general").strip().lower()
    try:
        lessons = _load_lessons()
        if act in ("learn", "record", "save", "add"):
            if not lesson:
                reply = "Hari, tell me what mistake or rule I should learn from."
            else:
                lessons.append({"id": len(lessons) + 1, "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "context": context, "lesson": lesson})
                _save_lessons(lessons)
                reply = f"Lesson internalized, Hari [{context}]: '{lesson}'."
        elif act == "recall" and lesson:
            q = lesson.lower()
            matches = [l for l in reversed(lessons) if q in l.get("lesson", "").lower() or q in l.get("context", "").lower()]
            reply = f"Found {len(matches)} lesson(s), Hari: " + " | ".join(f"[{m['context']}] {m['lesson']}" for m in matches[:4]) if matches else f"Hari, no lessons matching '{lesson}'."
        else:
            reply = f"Total {len(lessons)} lesson(s) learned, Hari. Latest: " + " | ".join(f"#{l['id']} [{l['context']}]: {l['lesson']}" for l in reversed(lessons[-5:])) if lessons else "Hari, Self-Learning ledger is currently empty."
    except Exception as e:
        reply = f"Hari, Self-Learner error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
