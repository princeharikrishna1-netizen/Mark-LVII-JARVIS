"""
JARVIS Promoted Plugin: Automated Log Rotation
Promoted from Self-Improvement Sandbox.
"""
from __future__ import annotations
import gzip, shutil
from datetime import datetime
from pathlib import Path

PLUGIN = {
    "name": "log_rotation",
    "description": (
        "Automated Log Rotation Manager. Archives and compresses large log or JSON trace files "
        "in memory/logs to keep disk usage clean. Trigger on 'rotate logs', 'archive old logs', "
        "or 'log rotation status'."
    ),
    "tier": "core",
    "brief": "Rotate and compress large log files automatically.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'rotate', or 'status'"},
            "max_kb": {"type": "INTEGER", "description": "Size threshold in KB (default 512)."}
        },
        "required": ["action"],
    },
}

# --- Original Evolved Logic Reference ---
# """Auto-evolved JARVIS helper: automated log rotation

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    max_bytes = int(parameters.get("max_kb") or 512) * 1024
    log_dir = Path("memory")
    archive_dir = log_dir / "archived_logs"
    try:
        candidates = [f for f in log_dir.glob("*.log") if f.is_file()]
        if act == "rotate":
            archive_dir.mkdir(parents=True, exist_ok=True)
            rotated = 0
            for lf in candidates:
                if lf.stat().st_size >= max_bytes:
                    gz_path = archive_dir / f"{lf.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log.gz"
                    with lf.open("rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    lf.write_text("", encoding="utf-8")
                    rotated += 1
            reply = f"Hari, Log Rotation complete: {rotated} oversized log file(s) archived to '{archive_dir}'."
        else:
            total_kb = round(sum(f.stat().st_size for f in candidates) / 1024, 1)
            reply = f"Hari, Log Rotation Monitor active: {len(candidates)} .log file(s) tracked ({total_kb} KB total)."
    except Exception as e:
        reply = f"Hari, Log Rotation error: {e}"
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
