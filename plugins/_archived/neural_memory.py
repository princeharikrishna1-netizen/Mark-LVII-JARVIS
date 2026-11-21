"""
JARVIS Plugin: Long-Term Neural Memory
Stores user facts, preferences, document numbers, and conversation notes permanently
in JSON storage so JARVIS can recall them across restarts and future sessions.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

FACTS_FILE = Path("memory/neural_facts.json")

PLUGIN = {
    "name": "neural_memory",
    "description": (
        "Long-Term Neural Memory Vault. Saves important facts, preferences, dates, "
        "or document details permanently and recalls them when asked. "
        "Trigger on phrases like 'remember that [fact]', 'save to memory [info]', "
        "'what do you remember about [topic]', 'recall memories', or 'forget [topic]'."
    ),
    "tier": "core",
    "brief": "Permanently store and recall user facts, preferences, and notes across sessions.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'save', 'recall', 'list', or 'delete'"
            },
            "content": {
                "type": "STRING",
                "description": "The fact to remember, or keyword to search/delete."
            },
            "category": {
                "type": "STRING",
                "description": "Optional tag like 'work', 'personal', 'system', or 'general'."
            }
        },
        "required": ["action"],
    },
}


def _load_facts() -> list[dict]:
    if not FACTS_FILE.exists():
        return []
    try:
        return json.loads(FACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _write_facts(items: list[dict]) -> None:
    FACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    FACTS_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "recall").strip().lower()
    content = (parameters.get("content") or "").strip()
    category = (parameters.get("category") or "general").strip().lower()

    try:
        facts = _load_facts()

        if act in ("save", "store", "remember", "add"):
            if not content:
                reply = "Sir, please tell me what detail you would like me to commit to long-term memory."
            else:
                facts.append({
                    "id": len(facts) + 1,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                    "category": category,
                    "fact": content,
                })
                _write_facts(facts)
                reply = f"Committed to Neural Memory, Sir [{category}]: '{content}'."

        elif act in ("delete", "forget", "remove"):
            if not content:
                reply = "Sir, specify which memory keyword you want me to erase."
            else:
                q = content.lower()
                remaining = [f for f in facts if q not in f.get("fact", "").lower()]
                removed_count = len(facts) - len(remaining)
                if removed_count == 0:
                    reply = f"Sir, no stored memory matched '{content}'."
                else:
                    _write_facts(remaining)
                    reply = f"Erased {removed_count} memory entry(ies) matching '{content}', Sir."

        elif act == "list" or not content:
            if not facts:
                reply = "Sir, your Long-Term Neural Memory vault is currently empty."
            else:
                latest = list(reversed(facts[-5:]))
                summary = " | ".join(f"[{f['category']}] {f['fact']}" for f in latest)
                reply = f"You have {len(facts)} stored memory(ies), Sir. Most recent: {summary}"

        else:
            q = content.lower()
            matches = [
                f for f in reversed(facts)
                if q in f.get("fact", "").lower() or q in f.get("category", "").lower()
            ]
            if not matches:
                reply = f"Sir, I have no long-term memory records matching '{content}'."
            else:
                top = matches[:4]
                formatted = " | ".join(f"[{m['timestamp']} - {m['category']}]: {m['fact']}" for m in top)
                reply = f"Recalled {len(matches)} memory(ies) for '{content}', Sir: {formatted}"

    except Exception as e:
        reply = f"Sir, Neural Memory error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply