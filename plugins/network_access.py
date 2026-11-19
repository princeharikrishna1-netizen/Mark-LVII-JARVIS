"""
JARVIS Plugin: Computer Network Access & Digital Interop
Interacts with local/remote HTTP endpoints, checks open TCP ports, and validates
digital service availability.
"""
from __future__ import annotations
import socket, urllib.request

PLUGIN = {
    "name": "network_access",
    "description": "Computer Network Access Engine. Interacts with web APIs, checks TCP ports, and queries digital endpoints. Trigger on 'check port [port] on [host]', 'query endpoint [url]', or 'verify local dashboard port'.",
    "tier": "core",
    "brief": "Interact with digital APIs, HTTP endpoints, and TCP network ports.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'check_port', 'http_get', or 'dashboard_check'"},
            "host": {"type": "STRING", "description": "Hostname, IP, or URL."},
            "port": {"type": "INTEGER", "description": "TCP port number (e.g., 8000, 8080)."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "dashboard_check").strip().lower()
    host = (parameters.get("host") or "127.0.0.1").strip()
    port = int(parameters.get("port") or 8000)
    try:
        if act == "http_get" and host.startswith("http"):
            req = urllib.request.Request(host, headers={"User-Agent": "JARVIS-Mark-LVII"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.status
                snippet = resp.read().decode("utf-8", errors="ignore")[:150].replace("\n", " ")
            reply = f"HTTP Endpoint '{host}' responded with Status {status}, Sir. Payload preview: {snippet}"
        else:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.5)
                is_open = s.connect_ex((host, port)) == 0
            state = "OPEN & LISTENING" if is_open else "CLOSED / UNREACHABLE"
            reply = f"Network Socket Probe on {host}:{port}, Sir -> {state}."
    except Exception as e:
        reply = f"Sir, Network Access error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
