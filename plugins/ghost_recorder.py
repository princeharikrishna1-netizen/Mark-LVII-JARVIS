"""
JARVIS Plugin: Ghost Workflow Recorder & Replay Engine (Level 6 Supreme - 35/40)
Records mouse cursor paths, clicks, and step-by-step desktop sequences and replays them on demand:
- record_mouse: Captures live cursor checkpoints over N seconds into memory/ghost_workflows.json
- replay: Executes a saved workflow N times with human-safe pacing
- list: Shows all saved Ghost Workflows
"""
from __future__ import annotations
import json
import subprocess
import time
from pathlib import Path

WF_FILE = Path("memory/ghost_workflows.json")

PLUGIN = {
    "name": "ghost_recorder",
    "description": (
        "Ghost Workflow Recorder & Replay Engine. Records mouse positions/clicks or action sequences "
        "and replays repetitive desktop tasks automatically. "
        "Trigger on 'ghost', 'record workflow', 'replay workflow', or 'repeat clicks'."
    ),
    "tier": "core",
    "brief": "Record & replay mouse/keyboard desktop workflows automatically.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'list', 'record_mouse', 'replay', or 'status'"
            },
            "name": {
                "type": "STRING",
                "description": "Workflow name (default: 'quick_ghost')."
            },
            "seconds_or_repeats": {
                "type": "STRING",
                "description": "Duration in seconds for 'record_mouse' (default '5'), or repeat count for 'replay' (default '1')."
            }
        },
        "required": ["action"],
    },
}


def _load_wfs() -> dict:
    WF_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not WF_FILE.exists():
        sample = {
            "portal_refresh": {
                "description": "Focus browser and send F5 refresh",
                "steps": [{"type": "key", "value": "{F5}", "delay": 0.4}]
            }
        }
        WF_FILE.write_text(json.dumps(sample, indent=2), encoding="utf-8")
        return sample
    try:
        return json.loads(WF_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_wfs(data: dict) -> None:
    WF_FILE.parent.mkdir(parents=True, exist_ok=True)
    WF_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _get_cursor_pos() -> tuple[int, int]:
    ps = 'Add-Type -AssemblyName System.Windows.Forms; $p = [System.Windows.Forms.Cursor]::Position; Write-Output "$($p.X),$($p.Y)"'
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=5)
    parts = (r.stdout or "0,0").strip().split(",")
    return int(parts[0]), int(parts[1])


def _move_and_click(x: int, y: int) -> None:
    ps = (
        'Add-Type -AssemblyName System.Windows.Forms; '
        f'[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({x},{y}); '
        '$sig = "[DllImport(\\"user32.dll\\")] public static extern void mouse_event(int f, int dx, int dy, int c, int e);"; '
        '$m = Add-Type -MemberDefinition $sig -Name "M" -Namespace "W" -PassThru; '
        '$m::mouse_event(0x0002,0,0,0,0); $m::mouse_event(0x0004,0,0,0,0);'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=6)


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "list").strip().lower()
    name = (parameters.get("name") or "quick_ghost").strip().lower().replace(" ", "_")
    val = int(float(parameters.get("seconds_or_repeats") or "5"))

    try:
        wfs = _load_wfs()
        if act == "record_mouse":
            secs = max(2, min(15, val))
            pts = []
            last = None
            end_t = time.time() + secs
            while time.time() < end_t:
                pos = _get_cursor_pos()
                if pos != last:
                    pts.append({"type": "click", "x": pos[0], "y": pos[1], "delay": 0.5})
                    last = pos
                time.sleep(0.6)
            wfs[name] = {"description": f"Recorded {len(pts)} cursor points over {secs}s", "steps": pts}
            _save_wfs(wfs)
            reply = f"Hari, Ghost Recorder captured '{name}' ({len(pts)} cursor points in {secs}s)."

        elif act == "replay":
            if name not in wfs:
                reply = f"Hari, workflow '{name}' not found. Saved: {', '.join(wfs.keys())}"
            else:
                repeats = max(1, min(10, val if val <= 10 else 1))
                steps = wfs[name].get("steps", [])
                for _ in range(repeats):
                    for st in steps:
                        if st.get("type") == "click":
                            _move_and_click(int(st["x"]), int(st["y"]))
                        elif st.get("type") == "key":
                            k = str(st.get("value", "")).replace("'", "''")
                            subprocess.run(
                                ["powershell", "-NoProfile", "-Command", f"Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{k}')"],
                                capture_output=True, timeout=5
                            )
                        time.sleep(float(st.get("delay", 0.3)))
                reply = f"Hari, Ghost Replay executed '{name}' ({len(steps)} steps x {repeats} cycle(s))."
        else:
            reply = f"Hari, Ghost Workflow Recorder ONLINE ({len(wfs)} workflows saved: {', '.join(wfs.keys())})."
    except Exception as e:
        reply = f"Hari, Ghost Recorder error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
