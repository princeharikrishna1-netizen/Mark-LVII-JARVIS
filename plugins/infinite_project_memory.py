import sqlite3, json
from datetime import datetime
from pathlib import Path

DB_PATH = Path("memory/infinite_projects.db")

TOOL = {
    "name": "infinite_project_memory",
    "description": "Tracks exact progress across all projects: where you stopped, modified files, and next steps.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "save | recall | list"},
            "project": {"type": "STRING", "description": "Project name (e.g. Mark-LVII)"},
            "stopped_at": {"type": "STRING", "description": "Current checkpoint / where you stopped"},
            "changed_files": {"type": "STRING", "description": "Comma-separated list of modified files"},
            "next_steps": {"type": "STRING", "description": "What needs to be done next"}
        },
        "required": ["action"]
    }
}

def _init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS project_state (
            project TEXT PRIMARY KEY,
            stopped_at TEXT,
            changed_files TEXT,
            next_steps TEXT,
            updated_at TEXT
        )
    """)
    con.commit()
    return con

def run(params: dict = None, **kwargs) -> str:
    params = params or {}
    action = str(params.get("action", "recall")).lower()
    proj = str(params.get("project", "Mark-LVII")).strip() or "Mark-LVII"
    con = _init_db()
    try:
        if action == "save":
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            con.execute(
                "INSERT OR REPLACE INTO project_state VALUES (?, ?, ?, ?, ?)",
                (proj, params.get("stopped_at", ""), params.get("changed_files", ""), params.get("next_steps", ""), now)
            )
            con.commit()
            return f"Infinite Project Memory: Checkpoint saved for '{proj}' at {now}."
        elif action == "list":
            rows = con.execute("SELECT project, stopped_at, updated_at FROM project_state ORDER BY updated_at DESC").fetchall()
            if not rows:
                return "Infinite Project Memory: No projects tracked yet."
            return "Tracked Projects:\n" + "\n".join(f"- {r[0]} (Last: {r[2]}): {r[1]}" for r in rows)
        else:
            row = con.execute("SELECT stopped_at, changed_files, next_steps, updated_at FROM project_state WHERE project=?", (proj,)).fetchone()
            if not row:
                return f"Infinite Project Memory: No saved state found for '{proj}'."
            return f"Project '{proj}' (Updated {row[3]}):\n- Stopped at: {row[0]}\n- Modified files: {row[1]}\n- Next steps: {row[2]}"
    finally:
        con.close()

PLUGIN = TOOL

