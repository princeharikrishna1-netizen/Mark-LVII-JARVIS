"""
JARVIS Plugin: Cross-Device Clipboard Sync Bridge (PC <-> iPad <-> Android - 31/31)
Syncs text and links instantaneously between Hari's Windows 11 PC, iOS iPad HUD, and Android Mobile:
- read_pc / write_pc: Reads or writes Windows 11 system clipboard via PowerShell Get-Clipboard/Set-Clipboard
- save_drop / get_drop: Stores shared clipboard item in memory/clipboard_drop.json for iPad/Mobile HUD access
- push_to_android: Types clipboard text onto connected Android device via mobile_bridge
"""
from __future__ import annotations
import json
import subprocess
from datetime import datetime
from pathlib import Path

DROP_FILE = Path("memory/clipboard_drop.json")

PLUGIN = {
    "name": "clipboard_bridge",
    "description": (
        "Cross-Device Clipboard Sync Bridge between Windows 11 PC, iOS iPad, and Android Mobile. "
        "Shares copied text/links from PC to HUD or writes text from iPad/Mobile directly into PC clipboard. "
        "Trigger on 'clipboard', 'sync text', 'send to ipad', 'send to pc', or 'shared clip'."
    ),
    "tier": "core",
    "brief": "Instant clipboard & link sync across Windows 11 PC, iOS iPad, and Android.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'push_from_pc', 'write_pc', 'get_drop', 'push_to_android', or 'status'"
            },
            "text": {
                "type": "STRING",
                "description": "Text payload when action is 'write_pc'."
            }
        },
        "required": ["action"],
    },
}


def _read_win_clipboard() -> str:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
        capture_output=True, text=True, timeout=8
    )
    return (proc.stdout or "").strip()


def _write_win_clipboard(text: str) -> bool:
    safe = text.replace("'", "''")
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value '{safe}'"],
        capture_output=True, text=True, timeout=8
    )
    return proc.returncode == 0


def _save_drop(text: str, source: str) -> dict:
    DROP_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "text": text,
        "source": source,
        "updated_at": datetime.now().strftime("%d-%b-%Y %I:%M:%S %p"),
    }
    DROP_FILE.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def _load_drop() -> dict:
    if not DROP_FILE.exists():
        return {}
    try:
        return json.loads(DROP_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    text = (parameters.get("text") or "").strip()

    try:
        if act == "push_from_pc":
            clip = _read_win_clipboard()
            if not clip:
                reply = "Hari, your Windows 11 clipboard is currently empty."
            else:
                _save_drop(clip, "Windows 11 PC")
                preview = clip[:80] + ("..." if len(clip) > 80 else "")
                reply = f"Hari, synced PC Clipboard to iPad/Mobile HUD ({len(clip)} chars): \"{preview}\""

        elif act == "write_pc":
            if not text:
                reply = "Hari, provide text to write into PC clipboard."
            else:
                ok = _write_win_clipboard(text)
                _save_drop(text, "Remote HUD (iPad/Mobile)")
                preview = text[:80] + ("..." if len(text) > 80 else "")
                reply = (
                    f"Hari, copied directly to Windows 11 PC Clipboard (ready for Ctrl+V): \"{preview}\""
                    if ok else "Hari, failed to update Windows clipboard."
                )

        elif act == "get_drop":
            data = _load_drop()
            if not data.get("text"):
                reply = "Hari, Cross-Device Clipboard Drop is currently empty."
            else:
                reply = f"Hari, Latest Shared Clip (from {data.get('source')} at {data.get('updated_at')}): {data.get('text')}"

        elif act == "push_to_android":
            clip = text or _read_win_clipboard() or _load_drop().get("text", "")
            if not clip:
                reply = "Hari, no text found in PC clipboard or shared drop to send to Android."
            else:
                import plugins.mobile_bridge as mb
                reply = mb.run({"action": "type_text", "target": clip})

        else:
            data = _load_drop()
            has_item = bool(data.get("text"))
            reply = (
                f"Hari, Cross-Device Clipboard Sync Bridge ONLINE (PC <-> iPad <-> Android | "
                f"Shared Drop: {'1 active item from ' + data.get('source', '') if has_item else 'empty'})."
            )
    except Exception as e:
        reply = f"Hari, Clipboard Bridge error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
