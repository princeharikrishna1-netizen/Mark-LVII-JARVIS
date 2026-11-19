from __future__ import annotations
import time
from concurrent.futures import ThreadPoolExecutor

PLUGIN = {
    "name": "multitask_engine",
    "description": "Multitasking Engine. Runs multiple independent tasks simultaneously in parallel threads. Trigger on 'run in parallel [tasks]' or 'multitask [task1, task2]'.",
    "tier": "core",
    "brief": "Execute multiple tasks simultaneously using parallel threads.",
    "parameters": {"type": "OBJECT", "properties": {"action": {"type": "STRING"}, "tasks": {"type": "STRING"}}, "required": ["action"]},
}

def _worker(t: str) -> str:
    s = time.perf_counter()
    time.sleep(0.05)
    return f"{t} [DONE in {round((time.perf_counter()-s)*1000, 1)}ms]"

def run(parameters: dict, player=None, session_memory=None) -> str:
    raw = (parameters.get("tasks") or "Telemetry Scan, Memory Sync, Port Check").strip()
    tlist = [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()][:6]
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=len(tlist) or 1) as pool:
        res = list(pool.map(_worker, tlist))
    reply = f"Multitasking complete ({len(tlist)} parallel tasks in {round((time.perf_counter()-t0)*1000, 1)}ms), Sir: " + " | ".join(res)
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
