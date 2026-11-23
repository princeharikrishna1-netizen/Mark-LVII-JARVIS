"""
actions/process_guardian.py — Windows Process Monitor, Resource Hog Inspector & Safe Task Killer.
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

import psutil

# Never allow killing critical Windows or self processes
_PROTECTED_EXES = frozenset({
    "system", "idle", "registry", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "winlogon.exe", "dwm.exe",
    "explorer.exe", "taskmgr.exe", "audiodg.exe", "conhost.exe",
})


def get_top_resource_hogs(limit: int = 5) -> str:
    """Returns top CPU and Memory consuming processes on Windows."""
    procs = []
    # Prime CPU measurement briefly
    for p in psutil.process_iter(["pid", "name"]):
        try:
            p.cpu_percent(interval=None)
        except Exception:
            pass

    import time
    time.sleep(0.25)

    for p in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            name = (p.info.get("name") or "").strip()
            if not name or name.lower() in ("system idle process", "system"):
                continue
            cpu = p.cpu_percent(interval=None)
            mem_mb = (p.info["memory_info"].rss / (1024 * 1024)) if p.info.get("memory_info") else 0.0
            procs.append((cpu, mem_mb, p.info["pid"], name))
        except Exception:
            continue

    top_cpu = sorted(procs, key=lambda x: x[0], reverse=True)[:limit]
    top_ram = sorted(procs, key=lambda x: x[1], reverse=True)[:limit]

    cpu_lines = [f"{name} (PID {pid}): {cpu:.1f}% CPU, {ram:.0f} MB" for cpu, ram, pid, name in top_cpu]
    ram_lines = [f"{name} (PID {pid}): {ram:.0f} MB RAM, {cpu:.1f}% CPU" for cpu, ram, pid, name in top_ram]

    total_cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    header = f"System Load -> CPU: {total_cpu:.1f}% | RAM: {vm.percent:.1f}% ({vm.used / (1024**3):.1f}/{vm.total / (1024**3):.1f} GB)"
    return (
        f"{header}\n"
        f"Top CPU Processes:\n- " + "\n- ".join(cpu_lines) + "\n"
        f"Top RAM Processes:\n- " + "\n- ".join(ram_lines)
    )


def kill_target_process(target: str) -> str:
    """Safely terminates processes matching `target` name or PID."""
    q = (target or "").strip().lower()
    if not q:
        return "Specify a process name or PID to terminate."

    aliases = {
        "chrome": "chrome.exe",
        "edge": "msedge.exe",
        "vscode": "code.exe",
        "vs code": "code.exe",
        "discord": "discord.exe",
        "spotify": "spotify.exe",
    }
    q = aliases.get(q, q)

    if q in _PROTECTED_EXES or f"{q}.exe" in _PROTECTED_EXES:
        return f"Blocked: '{target}' is a protected Windows system process."

    killed = []
    for p in psutil.process_iter(["pid", "name"]):
        try:
            pname = (p.info.get("name") or "").lower()
            pid_str = str(p.info.get("pid"))
            if pname in _PROTECTED_EXES:
                continue
            if q == pid_str or q in pname:
                p.terminate()
                killed.append(f"{p.info['name']} ({pid_str})")
        except Exception:
            continue

    if not killed:
        return f"No running process found matching '{target}'."
    return f"Terminated {len(killed)} process(es): {', '.join(killed[:6])}."


def process_guardian(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    action = (parameters.get("action") or "inspect").strip().lower()
    target = (parameters.get("target") or "").strip()

    if action == "kill" and target:
        return kill_target_process(target)
    return get_top_resource_hogs(limit=5)


TOOL = {
    "name": "process_guardian",
    "description": (
        "Inspects top CPU and RAM consuming processes on Windows, or safely terminates "
        "a frozen/heavy application by name or PID. Use this when the user asks why the PC "
        "is slow/lagging, which apps are using high CPU or memory, or asks to force-close/kill a process."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "'inspect' to list top CPU/RAM processes, or 'kill' to terminate a specific app/process.",
            },
            "target": {
                "type": "STRING",
                "description": "Required when action='kill': process name (e.g., 'chrome', 'discord', 'node.exe') or PID.",
            },
        },
        "required": ["action"],
    },
    "handler": process_guardian,
}
