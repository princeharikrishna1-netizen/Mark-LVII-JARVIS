"""JARVIS PRECOG Forecast V2 - additive, read-only predictive plugin.

Drop this file into the existing project's plugins/ folder. It does not replace
or edit any existing project file. The plugin loader discovers *.py plugins.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

import psutil

PLUGIN = {
    "name": "precog_forecast_v2",
    "description": (
        "PRECOG Forecast V2: estimates short-term CPU, RAM and system-drive trends "
        "from locally collected history. Read-only; never kills processes or changes settings. "
        "Trigger on 'precog forecast', 'future system prediction', or 'precog v2 report'."
    ),
    "tier": "core",
    "brief": "Add-on predictive CPU/RAM/disk forecasting with local history.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "analyze, status, or top_processes"
            }
        },
        "required": [],
    },
}

BASE_DIR = Path(__file__).resolve().parents[1]
HISTORY_FILE = BASE_DIR / "memory" / "precog_forecast_v2_history.json"
SAMPLE_SECONDS = 60
MAX_AGE_SECONDS = 24 * 60 * 60
MAX_ROWS = 1500
_LOCK = threading.RLock()
_ROWS: list[dict[str, Any]] = []
_LAST_SAMPLE = 0.0
_LOADED = False
_THREAD_STARTED = False


def _drive_root() -> str:
    if os.name == "nt":
        return os.environ.get("SystemDrive", "C:") + "\\"
    return "/"


def _sample() -> dict[str, Any]:
    vm = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.25)
    disk = psutil.disk_usage(_drive_root())
    net = psutil.net_io_counters()
    return {
        "ts": time.time(),
        "cpu_pct": round(float(cpu), 1),
        "ram_pct": round(float(vm.percent), 1),
        "disk_pct": round(float(disk.percent), 1),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "net_sent_mb": round(net.bytes_sent / (1024 ** 2), 2),
        "net_recv_mb": round(net.bytes_recv / (1024 ** 2), 2),
    }


def _load() -> None:
    global _LOADED, _ROWS
    if _LOADED:
        return
    with _LOCK:
        if _LOADED:
            return
        try:
            if HISTORY_FILE.exists():
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    cutoff = time.time() - MAX_AGE_SECONDS
                    _ROWS = [r for r in data if isinstance(r, dict)
                             and isinstance(r.get("ts"), (int, float))
                             and r["ts"] >= cutoff][-MAX_ROWS:]
        except Exception:
            _ROWS = []
        _LOADED = True


def _save_locked() -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = HISTORY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(_ROWS[-MAX_ROWS:], ensure_ascii=False), encoding="utf-8")
    tmp.replace(HISTORY_FILE)


def _record(force: bool = False) -> dict[str, Any]:
    global _LAST_SAMPLE
    _load()
    now = time.time()
    with _LOCK:
        if not force and now - _LAST_SAMPLE < SAMPLE_SECONDS and _ROWS:
            return _ROWS[-1]
        row = _sample()
        _ROWS.append(row)
        cutoff = now - MAX_AGE_SECONDS
        _ROWS[:] = [r for r in _ROWS if r.get("ts", 0) >= cutoff][-MAX_ROWS:]
        _LAST_SAMPLE = now
        try:
            _save_locked()
        except Exception:
            pass
        return row


def _sampler() -> None:
    while True:
        try:
            _record()
        except Exception:
            pass
        time.sleep(SAMPLE_SECONDS)


def _start_sampler() -> None:
    global _THREAD_STARTED
    with _LOCK:
        if _THREAD_STARTED:
            return
        _THREAD_STARTED = True
        threading.Thread(target=_sampler, name="precog-v2-sampler", daemon=True).start()


def _forecast(key: str, horizon_minutes: int = 15) -> tuple[str, str]:
    rows = [r for r in _ROWS if isinstance(r.get(key), (int, float))]
    if len(rows) < 3:
        return "collecting baseline", "low"
    # Use a bounded recent window. Linear trend is deliberately conservative.
    rows = rows[-60:]
    t0 = float(rows[0]["ts"])
    xs = [(float(r["ts"]) - t0) / 60.0 for r in rows]
    ys = [float(r[key]) for r in rows]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denom = sum((x - mean_x) ** 2 for x in xs)
    slope = (sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom) if denom else 0.0
    current = ys[-1]
    predicted = max(0.0, min(100.0, current + slope * horizon_minutes))
    age_min = max(0.0, (time.time() - t0) / 60.0)
    confidence = "medium" if len(rows) >= 10 and age_min >= 9 else "low"
    if len(rows) >= 30 and age_min >= 29:
        confidence = "higher"
    return f"{predicted:.1f}% in ~{horizon_minutes} min (trend estimate)", confidence


def _top_processes(limit: int = 5) -> list[str]:
    found = []
    for proc in psutil.process_iter(["name", "memory_info"]):
        try:
            info = proc.info
            mem = info.get("memory_info")
            if mem:
                found.append((mem.rss / (1024 ** 2), info.get("name") or "unknown"))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    found.sort(reverse=True)
    return [f"{name} ({mb:.0f} MB)" for mb, name in found[:limit]]


def run(parameters: dict, player=None, session_memory=None) -> str:
    action = str((parameters or {}).get("action") or "analyze").lower().strip()
    try:
        _start_sampler()
        current = _record(force=True)
        with _LOCK:
            count = len(_ROWS)
            age = (time.time() - float(_ROWS[0]["ts"])) / 60 if _ROWS else 0
            cpu_pred, cpu_conf = _forecast("cpu_pct")
            ram_pred, ram_conf = _forecast("ram_pct")
            disk_pred, disk_conf = _forecast("disk_pct")
        if action == "top_processes":
            result = "Top RAM processes: " + ", ".join(_top_processes())
        elif action == "status":
            result = f"PRECOG V2 active. Samples: {count}; history span: {age:.1f} min; sampling interval: {SAMPLE_SECONDS}s."
        else:
            risks = []
            if current["ram_pct"] >= 85:
                risks.append("RAM pressure is currently high")
            if current["cpu_pct"] >= 90:
                risks.append("CPU load is currently very high")
            if current["disk_free_gb"] < 15:
                risks.append("system-drive free space is below 15 GB")
            result = (
                "JARVIS PRECOG FORECAST V2\n"
                f"Now: CPU {current['cpu_pct']}%, RAM {current['ram_pct']}%, "
                f"Disk {current['disk_pct']}% used ({current['disk_free_gb']} GB free).\n"
                f"15-min trend: CPU {cpu_pred} [confidence: {cpu_conf}]; "
                f"RAM {ram_pred} [confidence: {ram_conf}]; "
                f"Disk {disk_pred} [confidence: {disk_conf}].\n"
                f"History: {count} samples across {age:.1f} minutes.\n"
                + ("Current warnings: " + "; ".join(risks) if risks else "No immediate threshold warning.")
                + "\nForecasts are estimates, not guarantees; reliability improves as history accumulates."
            )
        if player:
            try:
                player.write_log("JARVIS: " + result)
            except Exception:
                pass
        return result
    except Exception as exc:
        return f"PRECOG V2 unavailable: {type(exc).__name__}: {exc}"


# Start collecting a baseline after the plugin is loaded. This is read-only.
_start_sampler()
