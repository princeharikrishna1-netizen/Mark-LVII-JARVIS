import json
from datetime import datetime
from pathlib import Path

SYNC_FILE = Path("memory/device_mesh_sync.json")

TOOL = {
    "name": "device_network_sync",
    "description": "Synchronizes tasks, clipboard notes, and alerts securely between PC and Mobile dashboard.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "push_to_mobile | read_sync | clear"},
            "message": {"type": "STRING", "description": "Payload or notification to sync across devices"}
        },
        "required": ["action"]
    }
}

def run(params: dict = None, **kwargs) -> str:
    params = params or {}
    action = str(params.get("action", "read_sync")).lower()
    SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
    items = json.loads(SYNC_FILE.read_text(encoding="utf-8")) if SYNC_FILE.exists() else []

    if action == "push_to_mobile":
        msg = str(params.get("message", "")).strip()
        if not msg:
            return "Device Network: Nothing to push."
        items.append({"ts": datetime.now().strftime("%H:%M"), "from": "PC", "msg": msg})
        SYNC_FILE.write_text(json.dumps(items[-20:], indent=2), encoding="utf-8")
        return f"Device Intelligence Network: Synced to Mobile Hub -> '{msg}'"
    elif action == "clear":
        SYNC_FILE.write_text("[]", encoding="utf-8")
        return "Device Intelligence Network: Sync queue cleared."
    else:
        if not items:
            return "Device Intelligence Network: All devices in sync (0 pending items)."
        return "Device Sync Feed:\n" + "\n".join(f"[{x['ts']}] {x['from']}: {x['msg']}" for x in items[-5:])

PLUGIN = TOOL

