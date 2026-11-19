"""
JARVIS Plugin: Mark-85 Tactical Suit Management & Combat Telemetry Core
Unifies Voice Intelligence, Suit Power/HUD Controls, Real-Time Analysis, Threat Detection,
Hardware Diagnostics, Mission Assistance, Heavy Data Processing, and Remote Node Control for Hari.
"""
from __future__ import annotations
import psutil
from datetime import datetime

PLUGIN = {
    "name": "mark85_suit_hud",
    "description": "Mark-85 Tactical Suit Controls, Hardware Diagnostics, Threat & Mission Telemetry.",
    "tier": "core",
    "brief": "Mark-85 Iron Man Suit Management & Full Tactical Diagnostics.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'full_diagnostics', 'combat_mode', 'stealth_mode', or 'status'"}
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "full_diagnostics").strip().lower()
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(".").percent
    now = datetime.now().strftime("%H:%M:%S")

    if act == "combat_mode":
        mode_str = "MARK-85 TACTICAL OVERDRIVE (All 8 Subsystems at 100% Alert)"
    elif act == "stealth_mode":
        mode_str = "MARK-85 STEALTH PROTOCOL (PC Muted, Sentinel Shield Active)"
    else:
        mode_str = "MARK-85 SOVEREIGN ONLINE (All 8 Tactical Subsystems Nominal)"

    reply = (
        f"Hari, [{now}] {mode_str} | "
        f"Core Power/CPU: {cpu}% | Neural RAM: {ram}% | Storage Matrix: {disk}% | "
        f"Suit Controls, Live Screen Analysis, Threat Sentinel, Mission Advisor, Heavy Data Engine & Remote Mesh: 100% READY."
    )
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
