"""
JARVIS Plugin: Holographic Knowledge Graph & Relational Entity Memory (Level 9 Transcendence - 50/52)
Stores typed (Subject -> Relation -> Object) facts in SQLite (memory/knowledge_graph.db)
so Hari can link survey numbers, EC applications, hardware nodes, and project milestones.
"""
from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path

KG_DB = Path("memory/knowledge_graph.db")

PLUGIN = {
    "name": "knowledge_graph",
    "description": (
        "Holographic Knowledge Graph & Entity Memory. Links entities, survey numbers, registration files, "
        "and system specs in a persistent relational graph. "
        "Trigger on 'knowledge graph', 'link entity', 'graph query', or 'remember relation'."
    ),
    "tier": "core",
    "brief": "Persistent relational entity & fact graph in SQLite.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'add', 'query', or 'status'"
            },
            "subject": {"type": "STRING", "description": "Source entity name"},
            "relation": {"type": "STRING", "description": "Relationship label"},
            "target": {"type": "STRING", "description": "Target entity or value"}
        },
        "required": ["action"],
    },
}


def _db() -> sqlite3.Connection:
    KG_DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(KG_DB))
    c.execute(
        "CREATE TABLE IF NOT EXISTS edges (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, subj TEXT, rel TEXT, obj TEXT)"
    )
    c.commit()
    return c


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    subj = (parameters.get("subject") or "").strip()
    rel = (parameters.get("relation") or "linked_to").strip()
    obj = (parameters.get("target") or "").strip()

    c = _db()
    if act == "add" and subj and obj:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO edges (ts, subj, rel, obj) VALUES (?, ?, ?, ?)", (ts, subj, rel, obj))
        c.commit()
        reply = f"Hari, Knowledge Graph edge locked: [{subj}] --({rel})--> [{obj}]."
    elif act == "query":
        q = subj or obj
        rows = c.execute(
            "SELECT subj, rel, obj, ts FROM edges WHERE subj LIKE ? OR obj LIKE ? OR rel LIKE ? ORDER BY id DESC LIMIT 8",
            (f"%{q}%", f"%{q}%", f"%{q}%"),
        ).fetchall()
        if rows:
            txt = "; ".join(f"{r[0]} -[{r[1]}]-> {r[2]}" for r in rows)
            reply = f"Hari, Knowledge Graph Matches ({len(rows)}): {txt}"
        else:
            reply = f"Hari, no Knowledge Graph edges found matching '{q}'."
    else:
        cnt = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        reply = f"Hari, Holographic Knowledge Graph ONLINE ({cnt} relational edges indexed)."
    c.close()

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
