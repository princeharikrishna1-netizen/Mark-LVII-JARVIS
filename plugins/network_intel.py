"""
JARVIS Plugin: Network Intelligence (#4)
Scans local network devices (PC, iPad, printers, routers), checks host reachability,
and inspects active network interfaces.
"""
from __future__ import annotations
import socket, subprocess, re

PLUGIN = {
    "name": "network_intel",
    "description": "Network Intelligence Engine. Scans local LAN/Wi-Fi devices, checks IP/host status, and inspects network connectivity. Trigger on 'scan local network', 'check connected devices', 'ping [host]', or 'network status'.",
    "tier": "core",
    "brief": "Scan local network devices and check host connectivity.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'scan', 'ping', or 'local_info'"},
            "target": {"type": "STRING", "description": "IP address or hostname for ping action."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "scan").strip().lower()
    target = (parameters.get("target") or "").strip()
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if act == "local_info":
            reply = f"Network Node Info, Sir: Host='{hostname}', Local IP={local_ip}."
        elif act == "ping" and target:
            res = subprocess.run(["ping", "-n", "1", "-w", "1000", target], capture_output=True, text=True)
            status = "ONLINE (Reachable)" if res.returncode == 0 else "OFFLINE (Unreachable)"
            reply = f"Target '{target}' is {status}, Sir."
        else:
            out = subprocess.check_output(["arp", "-a"], text=True, stderr=subprocess.DEVNULL)
            ips = re.findall(r"(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+dynamic", out)
            if not ips:
                reply = f"Local IP is {local_ip}, Sir. No dynamic LAN peers cached in ARP table right now."
            else:
                peers = ", ".join(f"{ip} ({mac})" for ip, mac in ips[:8])
                reply = f"Network Scan complete from {local_ip}, Sir. Detected {len(ips)} active LAN device(s): {peers}."
    except Exception as e:
        reply = f"Sir, Network Intelligence error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
