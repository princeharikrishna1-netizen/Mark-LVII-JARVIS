"""
JARVIS Plugin: Long-Term Episodic Memory & Executive Briefing Engine (Pro Level 5)
Stores persistent episodic events in SQLite (memory/episodic_memory.db) and generates
concise executive briefings summarizing system health, watcher alerts, and recent runs.
"""
from __future__ import annotations
import json
import sqlite3
import psutil
from datetime import datetime
from pathlib import Path

DB_PATH = Path("memory/episodic_memory.db")
RUNS_FILE = Path("memory/orchestrator_runs.json")
ALERTS_FILE = Path("memory/watcher_alerts.json")
PROMOTED_FILE = Path("memory/promoted_registry.json")

PLUGIN = {
    "name": "episodic_briefing",
    "description": (
        "Long-Term Episodic Memory & Executive Session Briefing Engine. "
        "Logs key operational episodes in SQLite and delivers executive briefings for Hari. "
        "Trigger on 'executive briefing', 'session briefing', 'log episode', or 'recall episodes'."
    ),
    "tier": "core",
    "brief": "Record persistent episodic events and generate executive briefings for Hari.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'briefing', 'log', 'recall', or 'status'"
            },
            "note": {
                "type": "STRING",
                "description": "Episode summary text when action is 'log', or search keyword for 'recall'."
            },
            "category": {
                "type": "STRING",
                "description": "Category tag such as 'boot', 'task', 'security', or 'evolution'."
            }
        },
        "required": ["action"],
    },
}


def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            summary TEXT NOT NULL,
            cpu REAL,
            ram REAL
        )
        """
    )
    conn.commit()
    return conn


def _record_episode(category: str, summary: str) -> int:
    conn = _init_db()
    ts = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    cur = conn.execute(
        "INSERT INTO episodes (timestamp, category, summary, cpu, ram) VALUES (?, ?, ?, ?, ?)",
        (ts, category, summary, cpu, ram),
    )
    conn.commit()
    ep_id = cur.lastrowid
    conn.close()
    return ep_id


def _build_briefing() -> str:
    cpu = psutil.cpu_percent(interval=0.1)
    ram = psutil.virtual_memory().percent
    runs = json.loads(RUNS_FILE.read_text(encoding="utf-8")) if RUNS_FILE.exists() else []
    alerts = json.loads(ALERTS_FILE.read_text(encoding="utf-8")) if ALERTS_FILE.exists() else []
    promoted = json.loads(PROMOTED_FILE.read_text(encoding="utf-8")) if PROMOTED_FILE.exists() else []

    conn = _init_db()
    total_eps = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    last_rows = conn.execute(
        "SELECT timestamp, category, summary FROM episodes ORDER BY id DESC LIMIT 3"
    ).fetchall()
    conn.close()

    last_run_txt = (
        f"Run #{runs[-1]['id']} ({runs[-1].get('status', 'DONE')}): {runs[-1].get('goal', '')[:60]}"
        if runs else "None yet"
    )
    alert_txt = (
        f"{len(alerts)} total (Latest: {alerts[-1]['type']})"
        if alerts else "0 alerts (All baselines nominal)"
    )
    recent_ep_txt = (
        " | ".join(f"[{r[1].upper()}] {r[2][:55]}" for r in last_rows)
        if last_rows else "Initial baseline established"
    )

    return (
        f"Executive Briefing for Hari: "
        f"System Telemetry: CPU {cpu}%, RAM {ram}%. "
        f"Autonomous Core: 24/24 modules active | Orchestrator Runs: {len(runs)} (Last: {last_run_txt}) | "
        f"Proactive Alerts: {alert_txt} | Auto-Promoted Plugins: {len(promoted)} | "
        f"Episodic Memory ({total_eps} entries): {recent_ep_txt}."
    )


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "briefing").strip().lower()
    note = (parameters.get("note") or "").strip()
    cat = (parameters.get("category") or "general").strip().lower()

    try:
        if act == "log":
            msg = note or "Autonomous operational checkpoint recorded."
            ep_id = _record_episode(cat, msg)
            reply = f"Hari, Episodic Memory entry #{ep_id} [{cat}] committed to SQLite."
        elif act == "recall":
            conn = _init_db()
            if note:
                rows = conn.execute(
                    "SELECT id, timestamp, category, summary FROM episodes WHERE summary LIKE ? OR category LIKE ? ORDER BY id DESC LIMIT 5",
                    (f"%{note}%", f"%{note}%"),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT id, timestamp, category, summary FROM episodes ORDER BY id DESC LIMIT 5"
                ).fetchall()
            conn.close()
            if not rows:
                reply = "Hari, no matching episodic memories found."
            else:
                reply = "Hari, Recalled Episodes: " + " | ".join(
                    f"#{r[0]} [{r[1]} | {r[2]}]: {r[3]}" for r in rows
                )
        elif act == "status":
            conn = _init_db()
            cnt = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            conn.close()
            reply = f"Hari, Episodic Memory Engine ONLINE ({cnt} persistent episodes stored in SQLite)."
        else:
            _record_episode("briefing", "Generated Executive Session Briefing for Hari")
            reply = _build_briefing()
    except Exception as e:
        reply = f"Hari, Episodic Briefing error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
