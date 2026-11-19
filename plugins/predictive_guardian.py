"""
JARVIS Plugin: Predictive Analysis Guardian
Monitors RAM, CPU, and disk usage trends to detect memory leaks, thermal/load spikes,
or low storage risks before the PC slows down or crashes.
"""
from __future__ import annotations

import time
import threading
import psutil

PLUGIN = {
    "name": "predictive_guardian",
    "description": (
        "Predictive System Health & Anomaly Analysis. Monitors RAM, CPU, and Disk trends "
        "to predict slowdowns before they happen. Trigger on phrases like 'predictive check', "
        "'system health prediction', 'check system risks', or 'why might my pc slow down'."
    ),
    "tier": "core",
    "brief": "Predict system slowdowns, memory spikes, and storage bottlenecks early.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'analyze' (full risk forecast) or 'top_memory' (heavy apps)"
            }
        },
        "required": [],
    },
}

_RAM_HISTORY: list[float] = []
_LAST_ALERT_TS = 0.0


def _top_ram_processes(limit: int = 3) -> list[str]:
    procs = []
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            mem_mb = p.info["memory_info"].rss / (1024 * 1024)
            procs.append((mem_mb, p.info["name"]))
        except Exception:
            continue
    procs.sort(reverse=True)
    return [f"{name} ({mb:.0f} MB)" for mb, name in procs[:limit]]


def _run_forecast() -> str:
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)
    disk = psutil.disk_usage("C:\\")
    free_gb = disk.free / (1024 ** 3)

    risks = []
    if ram.percent >= 82:
        risks.append(f"High RAM pressure ({ram.percent}% used) — risk of UI lag.")
    elif len(_RAM_HISTORY) >= 3 and (_RAM_HISTORY[-1] - _RAM_HISTORY[0]) > 12:
        risks.append(f"Rapid RAM climb detected (+{_RAM_HISTORY[-1] - _RAM_HISTORY[0]:.1f}% recently).")

    if cpu >= 80:
        risks.append(f"Sustained high CPU load ({cpu}%) — thermal throttling possible.")

    if free_gb < 15:
        risks.append(f"Low C: drive space ({free_gb:.1f} GB free) — Windows pagefile may slow down.")

    heavy = ", ".join(_top_ram_processes(3))
    if not risks:
        return (
            f"Predictive scan clear, Sir. RAM is at {ram.percent}%, CPU at {cpu}%, "
            f"and C: drive has {free_gb:.1f} GB free. Top memory consumers: {heavy}."
        )
    return (
        "Predictive warning, Sir: " + " ".join(risks) + f" Heaviest processes right now: {heavy}."
    )


def _background_predictor():
    global _LAST_ALERT_TS
    while True:
        try:
            pct = psutil.virtual_memory().percent
            _RAM_HISTORY.append(pct)
            if len(_RAM_HISTORY) > 10:
                _RAM_HISTORY.pop(0)
        except Exception:
            pass
        time.sleep(60)


threading.Thread(target=_background_predictor, daemon=True).start()


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "analyze").strip().lower()
    try:
        if act == "top_memory":
            heavy = ", ".join(_top_ram_processes(5))
            reply = f"Top 5 memory-consuming processes right now, Sir: {heavy}."
        else:
            reply = _run_forecast()
    except Exception as e:
        reply = f"Sir, predictive guardian error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply