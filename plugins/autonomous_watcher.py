"""
JARVIS Plugin: Proactive Event Watcher (Level 4 Autonomous Trigger)
Continuously monitors CPU/RAM spikes and new LAN devices in a background thread,
automatically triggering master_orchestrator & security_sentinel without manual prompts.
"""
from __future__ import annotations
import importlib.util
import json
import re
import subprocess
import threading
import time
import psutil
from datetime import datetime
from pathlib import Path

ALERTS_FILE = Path("memory/watcher_alerts.json")
PLUGINS_DIR = Path("plugins")

PLUGIN = {
    "name": "autonomous_watcher",
    "description": (
        "Proactive Autonomous Event Watcher. Monitors CPU/RAM thresholds and local LAN devices "
        "in the background, auto-triggering master_orchestrator on anomalies. "
        "Trigger on 'start watcher', 'stop watcher', 'watcher status', or 'watcher alerts'."
    ),
    "tier": "core",
    "brief": "Proactively monitor CPU/RAM spikes and new LAN devices with auto-orchestration.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'start', 'stop', 'status', 'alerts', or 'scan_now'"
            },
            "cpu_limit": {
                "type": "INTEGER",
                "description": "CPU percent threshold to auto-trigger orchestration (default 85)."
            },
            "ram_limit": {
                "type": "INTEGER",
                "description": "RAM percent threshold to auto-trigger orchestration (default 85)."
            }
        },
        "required": ["action"],
    },
}

_STATE = {
    "running": False,
    "thread": None,
    "cpu_limit": 85,
    "ram_limit": 85,
    "known_ips": set(),
    "last_trigger_ts": 0.0,
    "checks_done": 0,
}


def _invoke(name: str, params: dict) -> str:
    fpath = PLUGINS_DIR / f"{name}.py"
    if not fpath.exists():
        return f"[{name}: missing]"
    try:
        spec = importlib.util.spec_from_file_location(name, fpath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return str(mod.run(params))
    except Exception as e:
        return f"[{name} error: {e}]"


def _get_lan_ips() -> set[str]:
    try:
        out = subprocess.check_output(["arp", "-a"], text=True, timeout=4, errors="ignore")
        return set(re.findall(r"\b10\.90\.58\.\d+\b|\b192\.168\.\d+\.\d+\b", out))
    except Exception:
        return set()


def _log_alert(kind: str, detail: str, player=None) -> None:
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        items = json.loads(ALERTS_FILE.read_text(encoding="utf-8")) if ALERTS_FILE.exists() else []
    except Exception:
        items = []
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
        "type": kind,
        "detail": detail,
    }
    items.append(entry)
    ALERTS_FILE.write_text(json.dumps(items[-50:], indent=2, ensure_ascii=False), encoding="utf-8")
    if player:
        try:
            player.write_log(f"JARVIS [PROACTIVE ALERT]: {detail}")
        except Exception:
            pass


def _evaluate_once(player=None, force_report: bool = False) -> str:
    _STATE["checks_done"] += 1
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    current_ips = _get_lan_ips()

    if not _STATE["known_ips"] and current_ips:
        _STATE["known_ips"] = set(current_ips)

    new_ips = current_ips - _STATE["known_ips"]
    if new_ips:
        _STATE["known_ips"].update(new_ips)
        sec = _invoke("security_sentinel", {"action": "scan"})
        msg = f"Hari, new LAN device(s) detected: {', '.join(sorted(new_ips))}. Auto-ran Security Sentinel: {sec}"
        _log_alert("NEW_LAN_DEVICE", msg, player)
        return msg

    now = time.time()
    if (cpu >= _STATE["cpu_limit"] or ram >= _STATE["ram_limit"]) and (now - _STATE["last_trigger_ts"] > 300):
        _STATE["last_trigger_ts"] = now
        orch = _invoke("master_orchestrator", {
            "action": "orchestrate",
            "goal": f"Auto-mitigate resource spike (CPU {cpu}%, RAM {ram}%)",
            "urgency": "high",
        })
        msg = f"Hari, resource threshold exceeded (CPU {cpu}%, RAM {ram}%). Auto-triggered Master Orchestrator: {orch}"
        _log_alert("RESOURCE_SPIKE", msg, player)
        return msg

    if force_report:
        return (
            f"Hari, Proactive Watcher check #{_STATE['checks_done']} nominal: "
            f"CPU {cpu}% (limit {_STATE['cpu_limit']}%), RAM {ram}% (limit {_STATE['ram_limit']}%), "
            f"Tracked LAN IPs: {len(_STATE['known_ips'])}."
        )
    return ""


def _watch_loop(player=None) -> None:
    while _STATE["running"]:
        try:
            _evaluate_once(player=player, force_report=False)
        except Exception:
            pass
        for _ in range(30):
            if not _STATE["running"]:
                break
            time.sleep(1)


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    if parameters.get("cpu_limit"):
        _STATE["cpu_limit"] = int(parameters["cpu_limit"])
    if parameters.get("ram_limit"):
        _STATE["ram_limit"] = int(parameters["ram_limit"])

    try:
        if act == "start":
            if _STATE["running"]:
                reply = f"Hari, Proactive Watcher is already active (Checks completed: {_STATE['checks_done']})."
            else:
                _STATE["running"] = True
                t = threading.Thread(target=_watch_loop, args=(player,), daemon=True)
                _STATE["thread"] = t
                t.start()
                baseline = _evaluate_once(player=player, force_report=True)
                reply = f"Proactive Event Watcher STARTED (30s interval). {baseline}"

        elif act == "stop":
            _STATE["running"] = False
            reply = "Hari, Proactive Event Watcher stopped."

        elif act == "scan_now":
            reply = _evaluate_once(player=player, force_report=True)

        elif act == "alerts":
            if not ALERTS_FILE.exists():
                reply = "Hari, no proactive alerts triggered yet - all baselines clean."
            else:
                items = json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
                recent = list(reversed(items[-3:]))
                reply = "Recent Proactive Alerts, Hari: " + " | ".join(
                    f"[{a['timestamp']}] {a['type']}: {a['detail']}" for a in recent
                )
        else:
            state_txt = "ACTIVE" if _STATE["running"] else "STANDBY"
            reply = (
                f"Hari, Proactive Watcher [{state_txt}]: Checks={_STATE['checks_done']}, "
                f"Thresholds=(CPU>{_STATE['cpu_limit']}%, RAM>{_STATE['ram_limit']}%), "
                f"Known LAN IPs={len(_STATE['known_ips'])}."
            )
    except Exception as e:
        reply = f"Hari, Proactive Watcher error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
