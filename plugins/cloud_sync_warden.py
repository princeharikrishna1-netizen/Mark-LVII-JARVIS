"""
JARVIS Plugin: Two-Way Automatic GitHub Cloud Sync Warden
Automatically pulls latest updates on boot (so Laptop gets all PC updates automatically)
and pushes any local code updates every 10 minutes & on shutdown.
"""
from __future__ import annotations
import atexit, subprocess, threading, time

GIT_EXE = r"C:\Program Files\Git\cmd\git.exe"

PLUGIN = {
    "name": "cloud_sync_warden",
    "description": "Two-way automatic GitHub cloud sync: Auto-Pull on boot + Auto-Push every 10m & on exit.",
    "tier": "core",
    "brief": "Two-way automatic GitHub cloud sync daemon.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'sync_now', 'pull', or 'status'"}
        },
        "required": ["action"],
    },
}


def sync_pull() -> str:
    try:
        r = subprocess.run([GIT_EXE, "pull", "--rebase", "--autostash", "origin", "main"], capture_output=True, text=True, timeout=15)
        return (r.stdout or r.stderr or "Up to date").strip()
    except Exception as e:
        return f"Pull skipped: {e}"


def sync_push(msg: str = "Auto-Cloud Sync: JARVIS live snapshot") -> str:
    try:
        subprocess.run([GIT_EXE, "add", "-A"], capture_output=True, timeout=8)
        subprocess.run([GIT_EXE, "commit", "-m", msg], capture_output=True, timeout=8)
        r = subprocess.run([GIT_EXE, "push", "origin", "main"], capture_output=True, text=True, timeout=15)
        return (r.stdout or r.stderr or "Pushed").strip()
    except Exception as e:
        return f"Push skipped: {e}"


def _background_loop() -> None:
    sync_pull()
    while True:
        time.sleep(600)
        sync_push("Auto-Cloud Sync: 10-min heartbeat snapshot")


threading.Thread(target=_background_loop, daemon=True).start()
atexit.register(lambda: sync_push("Auto-Cloud Sync: JARVIS shutdown snapshot"))


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "sync_now").strip().lower()
    if act == "pull":
        reply = f"Hari, Cloud Auto-Pull complete: {sync_pull()}"
    elif act == "sync_now":
        reply = f"Hari, Two-Way Cloud Sync complete (Pull: {sync_pull()} | Push: {sync_push('Triggered Cloud Sync')})."
    else:
        reply = "Hari, Two-Way Cloud Sync Warden ONLINE (Boot Auto-Pull + 10m & Exit Auto-Push armed)."
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
