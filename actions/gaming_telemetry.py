"""
actions/gaming_telemetry.py — Live Gaming & System Telemetry (CPU, RAM, Network Ping, Power).
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

import socket
import time
import psutil


def measure_ping_ms(host: str = "8.8.8.8", port: int = 53, timeout: float = 1.2) -> int:
    """Fast TCP socket latency check in milliseconds."""
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return max(1, int((time.perf_counter() - t0) * 1000))
    except Exception:
        return -1


def get_gaming_stats() -> dict:
    cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    ping = measure_ping_ms()
    batt = psutil.sensors_battery()
    plugged = batt.power_plugged if batt else True
    pct = int(batt.percent) if batt else 100
    return {
        "cpu": round(cpu, 1),
        "ram_pct": round(vm.percent, 1),
        "ram_used_gb": round(vm.used / (1024 ** 3), 1),
        "ram_total_gb": round(vm.total / (1024 ** 3), 1),
        "ping_ms": ping,
        "plugged": plugged,
        "battery_pct": pct,
    }


def gaming_telemetry(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    stats = get_gaming_stats()
    ping_str = f"{stats['ping_ms']} ms" if stats["ping_ms"] > 0 else "Offline / Timeout"
    power_str = "AC Power (High Performance)" if stats["plugged"] else f"Battery ({stats['battery_pct']}%)"
    return (
        f"Gaming Telemetry -> CPU: {stats['cpu']}% | "
        f"RAM: {stats['ram_pct']}% ({stats['ram_used_gb']}/{stats['ram_total_gb']} GB) | "
        f"Ping: {ping_str} | Power: {power_str}"
    )


TOOL = {
    "name": "gaming_telemetry",
    "description": (
        "Checks live gaming performance telemetry including CPU load, RAM usage, network ping latency (ms), "
        "and power/battery status. Use when the user asks for ping, latency, gaming performance, or live telemetry stats."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    },
    "handler": gaming_telemetry,
}
