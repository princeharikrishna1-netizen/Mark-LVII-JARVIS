"""JARVIS PRECOG Intelligence V3 - additive, read-only predictive plugin.
Install as plugins/precog_intelligence_v3.py. Does not edit PRECOG V2.
"""
from __future__ import annotations
import json, math, os, statistics, threading, time
from pathlib import Path
from typing import Any
import psutil

PLUGIN = {
    "name": "precog_intelligence_v3",
    "description": ("PRECOG Intelligence V3: read-only trend forecasting, robust anomaly "
        "detection, disk depletion estimates, network throughput monitoring, thermal "
        "status when supported, and risk explanations. Trigger on 'precog v3', "
        "'precog intelligence', 'predict system problems', or 'system risk report'."),
    "tier": "core",
    "brief": "Predictive system health, anomaly, disk, network and thermal intelligence.",
    "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING",
        "description": "analyze, status, or top_processes"}}, "required": []},
}
BASE_DIR = Path(__file__).resolve().parents[1]
HISTORY_FILE = BASE_DIR / "memory" / "precog_intelligence_v3_history.json"
SAMPLE_SECONDS, MAX_AGE_SECONDS, MAX_ROWS = 60, 7 * 24 * 60 * 60, 5000
_LOCK = threading.RLock()
_ROWS: list[dict[str, Any]] = []
_LOADED = _THREAD_STARTED = False
_LAST_SAMPLE = 0.0


def _drive_root() -> str:
    return os.environ.get("SystemDrive", "C:") + "\\" if os.name == "nt" else "/"


def _temperature_c() -> tuple[float | None, str]:
    try:
        getter = getattr(psutil, "sensors_temperatures", None)
        if getter is None:
            return None, "temperature sensors are not exposed by this platform"
        sensors = getter(fahrenheit=False) or {}
        values = [float(x.current) for group in sensors.values() for x in (group or [])
                  if isinstance(getattr(x, "current", None), (int, float))
                  and math.isfinite(float(x.current))]
        return (round(max(values), 1), "sensor reading available") if values else (
            None, "no readable temperature sensor was found")
    except Exception as exc:
        return None, f"temperature sensor unavailable ({type(exc).__name__})"


def _sample() -> dict[str, Any]:
    vm, cpu = psutil.virtual_memory(), psutil.cpu_percent(interval=0.25)
    disk, net = psutil.disk_usage(_drive_root()), psutil.net_io_counters()
    temp, note = _temperature_c()
    return {"ts": time.time(), "cpu_pct": round(float(cpu), 1),
        "ram_pct": round(float(vm.percent), 1), "disk_pct": round(float(disk.percent), 1),
        "disk_free_gb": round(disk.free / 1024**3, 3),
        "net_sent_mb": round(net.bytes_sent / 1024**2, 3),
        "net_recv_mb": round(net.bytes_recv / 1024**2, 3), "temp_c": temp, "temp_note": note}


def _load() -> None:
    global _LOADED, _ROWS
    if _LOADED: return
    with _LOCK:
        if _LOADED: return
        try:
            if HISTORY_FILE.exists():
                data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    cutoff = time.time() - MAX_AGE_SECONDS
                    _ROWS = [r for r in data if isinstance(r, dict)
                        and isinstance(r.get("ts"), (int, float)) and r["ts"] >= cutoff][-MAX_ROWS:]
        except Exception: _ROWS = []
        _LOADED = True


def _record(force: bool = False) -> dict[str, Any]:
    global _LAST_SAMPLE
    _load(); now = time.time()
    with _LOCK:
        if not force and _ROWS and now - _LAST_SAMPLE < SAMPLE_SECONDS: return _ROWS[-1]
        row = _sample(); _ROWS.append(row)
        cutoff = now - MAX_AGE_SECONDS
        _ROWS[:] = [r for r in _ROWS if isinstance(r.get("ts"), (int, float))
                    and r["ts"] >= cutoff][-MAX_ROWS:]
        _LAST_SAMPLE = now
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp = HISTORY_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(_ROWS, ensure_ascii=False), encoding="utf-8")
            tmp.replace(HISTORY_FILE)
        except Exception: pass
        return row


def _sampler() -> None:
    while True:
        try: _record()
        except Exception: pass
        time.sleep(SAMPLE_SECONDS)


def _start_sampler() -> None:
    global _THREAD_STARTED
    with _LOCK:
        if not _THREAD_STARTED:
            _THREAD_STARTED = True
            threading.Thread(target=_sampler, name="precog-v3-sampler", daemon=True).start()


def _numeric(key: str, limit: int = 120) -> list[dict[str, Any]]:
    return [r for r in _ROWS[-limit:] if isinstance(r.get(key), (int, float))
            and math.isfinite(float(r[key]))]


def _forecast(key: str) -> tuple[str, str]:
    rows = _numeric(key)
    if len(rows) < 5: return "insufficient history (need 5 samples)", "unavailable"
    t0 = float(rows[0]["ts"]); xs = [(float(r["ts"])-t0)/60 for r in rows]
    ys = [float(r[key]) for r in rows]; mx, my = statistics.fmean(xs), statistics.fmean(ys)
    denom = sum((x-mx)**2 for x in xs)
    if denom <= 0: return f"{ys[-1]:.1f} (insufficient time separation)", "low"
    slope = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/denom
    value = ys[-1] + slope*15
    if key in ("cpu_pct", "ram_pct", "disk_pct"): value = max(0.0, min(100.0, value))
    span = (float(rows[-1]["ts"])-t0)/60
    confidence = ("higher (trend only; not calibrated)" if len(rows)>=30 and span>=29 else
                  "medium" if len(rows)>=10 and span>=9 else "low")
    return f"{value:.1f}% in ~15 min (linear trend estimate)", confidence


def _anomalies() -> list[str]:
    found = []
    for key, label, floor in (("cpu_pct", "CPU", 15), ("ram_pct", "RAM", 8), ("disk_pct", "Disk usage", 5)):
        rows = _numeric(key, 61)
        if len(rows) < 9: continue
        base = [float(r[key]) for r in rows[:-1]][-60:]
        now, med = float(rows[-1][key]), statistics.median(base)
        mad = statistics.median(abs(v-med) for v in base)
        if now-med >= max(floor, 3.5*1.4826*mad):
            found.append(f"{label} unusually high ({now:.1f}%; recent median {med:.1f}%).")
    rates = []
    for a, b in zip(_ROWS[-61:], _ROWS[-60:]):
        dt = float(b["ts"])-float(a["ts"])
        if dt > 0:
            delta = max(0, float(b["net_sent_mb"])-float(a["net_sent_mb"])) + max(
                0, float(b["net_recv_mb"])-float(a["net_recv_mb"]))
            rates.append(delta/dt*60)
    if len(rates) >= 8:
        base = rates[:-1]; med = statistics.median(base)
        mad = statistics.median(abs(v-med) for v in base)
        if rates[-1] > max(25, med+5*max(mad, 1)):
            found.append(f"Network throughput spike ({rates[-1]:.1f} MB/min; median {med:.1f}); not proof of malicious activity.")
    return found


def _disk_projection() -> str:
    rows = _numeric("disk_free_gb")
    if len(rows) < 10: return "Insufficient disk history (need 10 samples)."
    x = [(float(r["ts"])-float(rows[0]["ts"]))/3600 for r in rows]
    y = [float(r["disk_free_gb"]) for r in rows]
    if x[-1] < .15: return "Collecting a longer disk baseline."
    mx, my = statistics.fmean(x), statistics.fmean(y); denom = sum((v-mx)**2 for v in x)
    if denom <= 0: return "Disk trend cannot be calculated yet."
    slope = sum((a-mx)*(b-my) for a,b in zip(x,y))/denom
    if slope >= -.01: return "No consistent disk-space decrease detected."
    rate = -slope; days = y[-1]/rate/24
    if days > 3650: return f"Disk decreasing very slowly (~{rate:.3f} GB/hour); no near-term fill estimate."
    return f"At the recent rate ({rate:.3f} GB/hour), free space could reach 0 GB in ~{days:.1f} days. Rough linear projection only."


def _network() -> str:
    if len(_ROWS)<2: return "Network rate: collecting baseline."
    a,b = _ROWS[-2:]; dt=max(.001,float(b["ts"])-float(a["ts"]))
    sent=max(0,float(b["net_sent_mb"])-float(a["net_sent_mb"]))
    recv=max(0,float(b["net_recv_mb"])-float(a["net_recv_mb"]))
    return f"Last interval: sent {sent/dt*60:.2f} MB/min; received {recv/dt*60:.2f} MB/min."


def _thermal(row: dict[str, Any]) -> str:
    t=row.get("temp_c")
    if not isinstance(t,(int,float)): return f"Temperature unavailable — {row.get('temp_note','no sensor data')}."
    status="critical; investigate cooling" if t>=90 else "high; check cooling" if t>=85 else "elevated; monitor" if t>=80 else "normal"
    return f"Highest readable sensor: {t:.1f}°C ({status})."


def _top_processes() -> list[str]:
    found=[]
    for p in psutil.process_iter(["name","memory_info","cpu_percent"]):
        try:
            i=p.info; m=i.get("memory_info")
            if m: found.append((m.rss/1024**2,i.get("name") or "unknown",float(i.get("cpu_percent") or 0)))
        except (psutil.NoSuchProcess,psutil.AccessDenied,psutil.ZombieProcess): pass
    found.sort(reverse=True)
    return [f"{n} ({mb:.0f} MB RAM, {cpu:.1f}% CPU)" for mb,n,cpu in found[:5]]


def run(parameters: dict, player=None, session_memory=None) -> str:
    action=str((parameters or {}).get("action") or "analyze").lower().strip()
    try:
        _start_sampler(); current=_record(force=True)
        with _LOCK:
            count=len(_ROWS); age=(float(_ROWS[-1]["ts"])-float(_ROWS[0]["ts"]))/60 if len(_ROWS)>1 else 0
            anomalies=_anomalies(); cf,cc=_forecast("cpu_pct"); rf,rc=_forecast("ram_pct"); df,dc=_forecast("disk_pct")
        if action=="top_processes": result="Top RAM processes: "+", ".join(_top_processes())
        elif action=="status": result=f"PRECOG V3 active. Samples: {count}; history: {age:.1f} min; interval: {SAMPLE_SECONDS}s; file: {HISTORY_FILE.name}."
        else:
            risks=[]
            if current["ram_pct"]>=90: risks.append("Critical RAM pressure: inspect memory-heavy applications.")
            elif current["ram_pct"]>=85: risks.append("High RAM pressure: inspect memory-heavy processes.")
            if current["cpu_pct"]>=95: risks.append("Critical CPU load: identify the process consuming CPU.")
            elif current["cpu_pct"]>=90: risks.append("Very high CPU load: check sustained background work.")
            if current["disk_free_gb"]<10: risks.append("Critical system-drive space: less than 10 GB remains.")
            elif current["disk_free_gb"]<20: risks.append("Low system-drive space: less than 20 GB remains.")
            if isinstance(current.get("temp_c"),(int,float)) and current["temp_c"]>=85: risks.append("Thermal warning: check ventilation and fans.")
            result=("JARVIS PRECOG INTELLIGENCE V3\n"
                f"Current: CPU {current['cpu_pct']}%, RAM {current['ram_pct']}%, Disk {current['disk_pct']}% used ({current['disk_free_gb']:.2f} GB free).\n"
                f"15-min trend: CPU {cf} [confidence: {cc}]; RAM {rf} [confidence: {rc}]; Disk {df} [confidence: {dc}].\n"
                f"Disk capacity: {_disk_projection()}\nNetwork: {_network()}\n{_thermal(current)}\n"
                f"History: {count} samples across {age:.1f} minutes.\n"
                + ("Anomaly findings: "+" ".join(anomalies) if anomalies else "Anomaly findings: no unusual spike detected against available baseline.")+"\n"
                + ("Risk guidance: "+" ".join(risks) if risks else "Risk guidance: no configured critical threshold is crossed.")
                + "\nForecasts are simple statistical trend estimates, not ML predictions or guarantees. Network spikes do not prove malicious activity.")
        if player:
            try: player.write_log("JARVIS: "+result)
            except Exception: pass
        return result
    except Exception as exc: return f"PRECOG V3 unavailable: {type(exc).__name__}: {exc}"


_start_sampler()
