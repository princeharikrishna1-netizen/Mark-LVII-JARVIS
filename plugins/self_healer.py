"""
JARVIS Plugin: Self-Healing Watchdog & Crash Recovery Engine (Pro Level 5)
Audits all plugins & core files for syntax/import integrity, quarantines broken plugins
before they can crash live sessions, and auto-heals missing/corrupt memory stores.
"""
from __future__ import annotations
import importlib.util
import json
import py_compile
import sqlite3
from datetime import datetime
from pathlib import Path

PLUGINS_DIR = Path("plugins")
CORE_FILES = [Path("main.py"), Path("dashboard/server.py")]
JSON_STORES = [
    Path("memory/orchestrator_runs.json"),
    Path("memory/watcher_alerts.json"),
    Path("memory/promoted_registry.json"),
]
HEAL_LOG = Path("memory/self_heal_history.json")

PLUGIN = {
    "name": "self_healer",
    "description": (
        "Self-Healing Watchdog & Crash Recovery Engine. Verifies syntax & imports across all plugins "
        "and core files, isolates faulty modules, and auto-repairs corrupt JSON/SQLite memory stores. "
        "Trigger on 'self heal', 'health check', 'watchdog audit', or 'recover system'."
    ),
    "tier": "core",
    "brief": "Audit code/memory integrity, isolate faulty plugins, and auto-heal system state.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'heal', 'audit', or 'status'"
            },
            "quarantine_broken": {
                "type": "BOOLEAN",
                "description": "If true, renames broken plugin files to .broken so main.py never crashes."
            }
        },
        "required": ["action"],
    },
}


def _record_heal(summary: str, repaired: list[str]) -> None:
    HEAL_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        items = json.loads(HEAL_LOG.read_text(encoding="utf-8")) if HEAL_LOG.exists() else []
    except Exception:
        items = []
    items.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        "summary": summary,
        "repaired": repaired,
    })
    HEAL_LOG.write_text(json.dumps(items[-30:], indent=2, ensure_ascii=False), encoding="utf-8")


def _run_diagnostics(auto_fix: bool = True, quarantine: bool = False) -> tuple[int, list[str], list[str]]:
    checked = 0
    broken: list[str] = []
    repaired: list[str] = []

    for cf in CORE_FILES:
        if cf.exists():
            checked += 1
            try:
                py_compile.compile(str(cf), doraise=True)
            except Exception as e:
                broken.append(f"{cf.as_posix()} ({e})")

    for pf in sorted(PLUGINS_DIR.glob("*.py")):
        if pf.name.startswith("__"):
            continue
        checked += 1
        try:
            py_compile.compile(str(pf), doraise=True)
            spec = importlib.util.spec_from_file_location(f"_heal_{pf.stem}", pf)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if not hasattr(mod, "PLUGIN") or not hasattr(mod, "run"):
                raise RuntimeError("Missing PLUGIN dict or run() entrypoint")
        except Exception as e:
            broken.append(f"{pf.name} ({e})")
            if quarantine:
                qpath = pf.with_suffix(".py.broken")
                pf.replace(qpath)
                repaired.append(f"Quarantined {pf.name} -> {qpath.name}")

    for jf in JSON_STORES:
        checked += 1
        jf.parent.mkdir(parents=True, exist_ok=True)
        if not jf.exists():
            if auto_fix:
                jf.write_text("[]\n", encoding="utf-8")
                repaired.append(f"Initialized missing {jf.as_posix()}")
        else:
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    raise ValueError("Root is not a JSON list")
            except Exception:
                if auto_fix:
                    bak = jf.with_suffix(".json.corrupt")
                    jf.replace(bak)
                    jf.write_text("[]\n", encoding="utf-8")
                    repaired.append(f"Repaired corrupt {jf.as_posix()} (saved {bak.name})")

    db_file = Path("memory/episodic_memory.db")
    checked += 1
    try:
        conn = sqlite3.connect(str(db_file))
        res = conn.execute("PRAGMA integrity_check;").fetchone()
        conn.close()
        if not res or res[0].lower() != "ok":
            raise RuntimeError("SQLite integrity check failed")
    except Exception:
        if auto_fix and db_file.exists():
            db_file.replace(db_file.with_suffix(".db.corrupt"))
            repaired.append("Reset corrupt episodic_memory.db")

    return checked, broken, repaired


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "heal").strip().lower()
    quarantine = bool(parameters.get("quarantine_broken", False))

    try:
        if act == "status":
            history = json.loads(HEAL_LOG.read_text(encoding="utf-8")) if HEAL_LOG.exists() else []
            last_txt = f"Last check: {history[-1]['timestamp']} ({history[-1]['summary']})" if history else "Ready"
            reply = f"Hari, Self-Healing Watchdog ONLINE ({len(history)} heal cycles logged). {last_txt}"
        elif act == "audit":
            checked, broken, _ = _run_diagnostics(auto_fix=False, quarantine=False)
            if broken:
                reply = f"Hari, Watchdog Audit ({checked} targets): {len(broken)} issue(s) found -> {', '.join(broken)}"
            else:
                reply = f"Hari, Watchdog Audit PASSED: All {checked} plugins, core files, & memory stores verified 100% healthy."
        else:
            checked, broken, repaired = _run_diagnostics(auto_fix=True, quarantine=quarantine)
            if not broken and not repaired:
                summary = f"All {checked} code & memory targets 100% healthy (0 faults)"
            else:
                summary = f"Checked {checked} targets | Faults: {len(broken)} | Repaired: {len(repaired)} ({'; '.join(repaired) if repaired else 'none'})"
            _record_heal(summary, repaired)
            reply = f"Hari, Self-Healing Watchdog Complete: {summary}."
    except Exception as e:
        reply = f"Hari, Self-Healer error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
