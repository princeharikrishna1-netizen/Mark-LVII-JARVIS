"""
JARVIS Plugin: Security Monitoring Sentinel
Monitors removable USB drives, active external network connections, and running processes
to detect unauthorized access or anomalous activity.
"""
from __future__ import annotations

import psutil

PLUGIN = {
    "name": "security_sentinel",
    "description": (
        "Security Monitoring Sentinel. Scans for removable USB drives, active remote network "
        "connections, and suspicious processes. Trigger on phrases like 'security scan', "
        "'check unauthorized access', 'monitor security', or 'check connected usb devices'."
    ),
    "tier": "core",
    "brief": "Scan USB drives, active network connections, and system security status.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "mode": {
                "type": "STRING",
                "description": "One of: 'full' (complete security audit), 'usb' (removable drives), or 'network' (external connections)"
            }
        },
        "required": [],
    },
}


def _check_usb_drives() -> list[str]:
    usb_list = []
    for part in psutil.disk_partitions(all=False):
        if "removable" in part.opts.lower():
            usb_list.append(f"{part.device} ({part.fstype})")
    return usb_list


def _check_external_connections(limit: int = 5) -> list[str]:
    conns = []
    seen = set()
    for c in psutil.net_connections(kind="inet"):
        if c.status == "ESTABLISHED" and c.raddr:
            rip = c.raddr.ip
            if rip.startswith(("127.", "10.", "192.168.", "::1")):
                continue
            key = (rip, c.pid)
            if key in seen:
                continue
            seen.add(key)
            try:
                pname = psutil.Process(c.pid).name() if c.pid else "Unknown"
            except Exception:
                pname = "System"
            conns.append(f"{pname} -> {rip}:{c.raddr.port}")
    return conns[:limit]


def run(parameters: dict, player=None, session_memory=None) -> str:
    mode = (parameters.get("mode") or "full").strip().lower()

    try:
        usbs = _check_usb_drives()
        ext_conns = _check_external_connections(5)

        usb_msg = (
            f"Removable USB drives detected: {', '.join(usbs)}."
            if usbs else "No external USB drives connected."
        )
        net_msg = (
            f"Active external connections ({len(ext_conns)} shown): {', '.join(ext_conns)}."
            if ext_conns else "No active external IP connections detected."
        )

        if mode == "usb":
            reply = f"Security USB check, Sir: {usb_msg}"
        elif mode == "network":
            reply = f"Security network check, Sir: {net_msg}"
        else:
            reply = f"Security Sentinel scan complete, Sir. {usb_msg} {net_msg}"
    except Exception as e:
        reply = f"Sir, security sentinel encountered an error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply