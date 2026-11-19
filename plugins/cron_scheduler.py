"""
JARVIS Plugin: Scheduled Cron & Smart Alarms Engine (Level 6 Supreme - 32/34)
Runs persistent daily time-based schedules and countdown timers in the background:
- start_daemon: Launches background 20s tick thread checking daily HH:MM & countdown jobs
- add_daily: Schedules a recurring daily task (e.g., 08:30 -> morning_briefing, 22:30 -> night_guard)
- add_timer: Sets a one-shot countdown alarm/reminder in N minutes
- list / remove: Inspects or deletes active schedules
"""
from __future__ import annotations
import json
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

SCHED_FILE = Path("memory/cron_schedules.json")
_DAEMON_RUNNING = False
_LOCK = threading.Lock()

DEFAULT_JOBS = [
    {"id": "daily_morning", "type": "daily", "time": "08:30", "command": "morning_briefing", "label": "Morning Executive Briefing", "last_run_date": ""},
    {"id": "daily_night", "type": "daily", "time": "22:30", "command": "night_guard_backup", "label": "Night Guard & Daily Backup", "last_run_date": ""},
]

PLUGIN = {
    "name": "cron_scheduler",
    "description": (
        "Scheduled Cron & Smart Alarms Engine. Manages recurring daily HH:MM automation tasks and countdown timers. "
        "Trigger on 'schedule', 'cron', 'alarm', 'timer', 'daily task', or 'remind me in'."
    ),
    "tier": "core",
    "brief": "Background daily cron scheduler & countdown alarm engine.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'status', 'list', 'add_daily', 'add_timer', 'remove', or 'start_daemon'"
            },
            "time_or_mins": {
                "type": "STRING",
                "description": "HH:MM (24h, e.g., '09:00') for add_daily, or minutes (e.g., '15') for add_timer, or job id for remove."
            },
            "command": {
                "type": "STRING",
                "description": "Task/reminder text or routine name (e.g., 'morning_briefing', 'work_mode', 'Check CARD portal')."
            }
        },
        "required": ["action"],
    },
}


def _load_jobs() -> list[dict]:
    SCHED_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SCHED_FILE.exists():
        SCHED_FILE.write_text(json.dumps(DEFAULT_JOBS, indent=2), encoding="utf-8")
        return list(DEFAULT_JOBS)
    try:
        data = json.loads(SCHED_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else list(DEFAULT_JOBS)
    except Exception:
        return list(DEFAULT_JOBS)


def _save_jobs(jobs: list[dict]) -> None:
    SCHED_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCHED_FILE.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")


def _fire_job(job: dict) -> None:
    cmd = (job.get("command") or "").lower()
    try:
        if "morning" in cmd:
            import plugins.smart_routines as sr
            sr.run({"routine": "morning_briefing"})
        elif "night" in cmd:
            import plugins.smart_routines as sr, plugins.auto_backup as ab
            sr.run({"routine": "night_guard"})
            ab.run({"action": "backup"})
        elif "work" in cmd:
            import plugins.smart_routines as sr
            sr.run({"routine": "work_mode"})
        else:
            import plugins.episodic_briefing as eb
            eb.log_event("cron_alarm", f"Scheduled Trigger [{job.get('label', job.get('id'))}]: {job.get('command')}")
    except Exception:
        pass


def _daemon_loop() -> None:
    while True:
        try:
            now = datetime.now()
            hhmm = now.strftime("%H:%M")
            today = now.strftime("%Y-%m-%d")
            with _LOCK:
                jobs = _load_jobs()
                changed = False
                remaining = []
                for j in jobs:
                    if j.get("type") == "daily":
                        if j.get("time") == hhmm and j.get("last_run_date") != today:
                            j["last_run_date"] = today
                            changed = True
                            threading.Thread(target=_fire_job, args=(dict(j),), daemon=True).start()
                        remaining.append(j)
                    elif j.get("type") == "timer":
                        due_ts = float(j.get("due_ts", 0))
                        if now.timestamp() >= due_ts:
                            changed = True
                            threading.Thread(target=_fire_job, args=(dict(j),), daemon=True).start()
                        else:
                            remaining.append(j)
                if changed:
                    _save_jobs(remaining)
        except Exception:
            pass
        time.sleep(20)


def start_background_daemon() -> str:
    global _DAEMON_RUNNING
    if not _DAEMON_RUNNING:
        _DAEMON_RUNNING = True
        _load_jobs()
        t = threading.Thread(target=_daemon_loop, name="JARVIS-CronScheduler", daemon=True)
        t.start()
    return "Hari, Cron Scheduler daemon ACTIVE."


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    arg = (parameters.get("time_or_mins") or "").strip()
    cmd = (parameters.get("command") or "Reminder Alert").strip()

    try:
        if act == "start_daemon":
            reply = start_background_daemon()
        elif act == "add_daily":
            if ":" not in arg:
                reply = "Hari, specify time in 24-hour HH:MM format (e.g., '09:00')."
            else:
                with _LOCK:
                    jobs = _load_jobs()
                    jid = f"daily_{arg.replace(':', '')}"
                    jobs = [j for j in jobs if j.get("id") != jid]
                    jobs.append({"id": jid, "type": "daily", "time": arg, "command": cmd, "label": cmd, "last_run_date": ""})
                    _save_jobs(jobs)
                reply = f"Hari, scheduled daily cron job '{cmd}' at {arg}."
        elif act == "add_timer":
            mins = max(1, int(float(arg or "5")))
            due = datetime.now() + timedelta(minutes=mins)
            with _LOCK:
                jobs = _load_jobs()
                jid = f"timer_{int(time.time())}"
                jobs.append({"id": jid, "type": "timer", "due_ts": due.timestamp(), "due_str": due.strftime("%I:%M %p"), "command": cmd, "label": cmd})
                _save_jobs(jobs)
            reply = f"Hari, countdown alarm set for {mins} min(s) ({due.strftime('%I:%M %p')}): '{cmd}'."
        elif act == "remove":
            with _LOCK:
                jobs = _load_jobs()
                new_jobs = [j for j in jobs if j.get("id") != arg]
                _save_jobs(new_jobs)
            reply = f"Hari, removed schedule '{arg}' ({len(new_jobs)} active remaining)."
        else:
            jobs = _load_jobs()
            desc = [
                f"{j['id']} ({j['time'] if j['type']=='daily' else 'due ' + j.get('due_str','')} -> {j['command']})"
                for j in jobs
            ]
            reply = f"Hari, Cron Scheduler ({'RUNNING' if _DAEMON_RUNNING else 'STANDBY'} | {len(jobs)} jobs): " + (", ".join(desc) if desc else "none")
    except Exception as e:
        reply = f"Hari, Cron Scheduler error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
