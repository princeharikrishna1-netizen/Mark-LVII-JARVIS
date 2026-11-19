"""
JARVIS Plugin: Robotics & Hardware Bridge (#9)
Discovers connected serial microcontrollers (Arduino, ESP32, Raspberry Pi)
and dispatches hardware control commands over Serial or HTTP IoT endpoints.
"""
from __future__ import annotations
import subprocess, urllib.request

PLUGIN = {
    "name": "robotics_bridge",
    "description": "Robotics & IoT Hardware Bridge. Scans COM/Serial ports for Arduino/ESP32/robots and sends hardware control commands. Trigger on 'scan robotics ports', 'send robot command [cmd]', or 'trigger iot [url]'.",
    "tier": "core",
    "brief": "Scan hardware COM ports and control Arduino/ESP32/IoT robotics devices.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'scan_ports', 'send_serial', or 'http_trigger'"},
            "port": {"type": "STRING", "description": "COM port like 'COM3' or HTTP endpoint URL."},
            "command": {"type": "STRING", "description": "Command string to transmit to hardware."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "scan_ports").strip().lower()
    port = (parameters.get("port") or "").strip()
    cmd = (parameters.get("command") or "").strip()
    try:
        if act == "http_trigger" and port.startswith("http"):
            with urllib.request.urlopen(port, timeout=4) as resp:
                body = resp.read().decode("utf-8", errors="ignore")[:120]
            reply = f"IoT Hardware endpoint triggered ({port}), Sir. Response: {body or 'OK'}."
        elif act == "send_serial" and port and cmd:
            try:
                import serial  # type: ignore
                with serial.Serial(port, 9600, timeout=2) as ser:
                    ser.write((cmd + "\n").encode("utf-8"))
                reply = f"Robotics command '{cmd}' transmitted to {port}, Sir."
            except ImportError:
                reply = f"Sir, pyserial is not installed yet (run 'pip install pyserial') to send '{cmd}' to {port}."
        else:
            out = subprocess.check_output(["powershell", "-Command", "[System.IO.Ports.SerialPort]::GetPortNames()"], text=True).strip()
            ports = [p.strip() for p in out.splitlines() if p.strip()]
            reply = f"Active Robotics/Serial COM ports detected, Sir: {', '.join(ports)}." if ports else "Sir, no active USB Serial/COM robotics controllers detected right now."
    except Exception as e:
        reply = f"Sir, Robotics Bridge error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
