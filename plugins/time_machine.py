"""
JARVIS Plugin: System Time-Machine & Instant File Rollback (Level 6 Supreme - 36/40)
Creates instant point-in-time checkpoints of critical code/config/memory files and rolls back on demand:
- checkpoint: Saves a timestamped restore point in memory/time_machine/
- rollback: Restores files from the latest (or named) checkpoint
- list: Lists available Time-Machine restore points
"""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path

TM_ROOT = Path("memory/time_machine")
WATCH_DIRS = ["plugins", "dashboard", "config"]

PLUGIN = {
    "name": "time_machine",
    "description": (
        "System Time-Machine & Instant File Rollback. Creates point-in-time checkpoints and restores "
        "previous states immediately if any edit or file deletion needs undoing. "
        "Trigger on 'time machine', 'checkpoint', 'rollback', 'restore point', or 'undo changes'."
    ),
    "tier": "core",
    "brief": "Instant point-in-time checkpoints & one-click state rollback.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'checkpoint', 'rollback', 'list', or 'status'"
            },
            "tag": {
                "type": "STRING",
                "description": "Optional checkpoint label or folder name to restore."
            }
        },
        "required": ["action"],
    },
}


def _list_points() -> list[Path]:
    if not TM_ROOT.exists():
        return []
    return sorted([d for d in TM_ROOT.iterdir() if d.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    tag = (parameters.get("tag") or "snap").strip().replace(" ", "_")

    try:
        if act == "checkpoint":
            TM_ROOT.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest = TM_ROOT / f"cp_{ts}_{tag}"
            dest.mkdir(parents=True, exist_ok=True)
            copied = 0
            for w in WATCH_DIRS:
                src_d = Path(w)
                if src_d.exists():
                    for f in src_d.rglob("*"):
                        if f.is_file() and "__pycache__" not in str(f) and f.name != "api_keys.json":
                            rel = f.relative_to(".")
                            out_f = dest / rel
                            out_f.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(f, out_f)
                            copied += 1
            pts = _list_points()
            for old in pts[6:]:
                shutil.rmtree(old, ignore_errors=True)
            reply = f"Hari, Time-Machine Checkpoint created: {dest.name} ({copied} critical files protected)."

        elif act == "rollback":
            pts = _list_points()
            if not pts:
                reply = "Hari, no Time-Machine checkpoints found yet."
            else:
                target_cp = next((p for p in pts if tag in p.name), pts[0])
                restored = 0
                for f in target_cp.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(target_cp)
                        rel.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(f, rel)
                        restored += 1
                reply = f"Hari, Time-Machine Rollback COMPLETE from '{target_cp.name}' ({restored} files restored)."
        else:
            pts = _list_points()
            names = [p.name for p in pts[:5]]
            reply = f"Hari, Time-Machine ONLINE ({len(pts)} restore points): " + (", ".join(names) if names else "none yet")
    except Exception as e:
        reply = f"Hari, Time-Machine error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
