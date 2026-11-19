"""
JARVIS Plugin: Automatic Snapshot Backup & Retention Engine (Level 6 Supreme - 29/29)
Creates clean compressed ZIP snapshots of Mark-LVII in memory/backups/ (excluding cache/temp files),
automatically prunes older snapshots beyond the retention limit (keep latest 5), and supports daily auto-boot backups.
"""
from __future__ import annotations
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_DIR = Path("memory/backups")
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "backups", "archived_logs"}
MAX_KEEP = 5

PLUGIN = {
    "name": "auto_backup",
    "description": (
        "Automatic Snapshot Backup & Retention Engine. Creates clean compressed ZIP snapshots of Mark-LVII "
        "in memory/backups/ and retains the latest 5 backups automatically. "
        "Trigger on 'auto backup', 'backup codebase', 'create snapshot', or 'backup status'."
    ),
    "tier": "core",
    "brief": "Create clean compressed ZIP snapshots of Mark-LVII and prune old backups.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'backup', 'daily_check', 'list', or 'status'"
            }
        },
        "required": ["action"],
    },
}


def _create_snapshot() -> tuple[Path, int, float]:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(".")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_zip = BACKUP_DIR / f"Mark-LVII-Supreme-{ts}.zip"

    count = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in src.rglob("*"):
            if not f.is_file():
                continue
            if any(p in SKIP_DIRS for p in f.parts):
                continue
            if ".bak" in f.name or f.suffix in {".pyc", ".pyo", ".corrupt", ".broken"}:
                continue
            zf.write(f, f.relative_to(src))
            count += 1

    # Prune old snapshots beyond MAX_KEEP
    existing = sorted(BACKUP_DIR.glob("Mark-LVII-Supreme-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in existing[MAX_KEEP:]:
        try:
            old.unlink()
        except Exception:
            pass

    size_kb = round(out_zip.stat().st_size / 1024, 1)
    return out_zip, count, size_kb


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "backup").strip().lower()

    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        existing = sorted(BACKUP_DIR.glob("Mark-LVII-Supreme-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)

        if act == "status" or act == "list":
            if not existing:
                reply = "Hari, Auto-Backup Engine ONLINE (0 snapshots in memory/backups yet)."
            else:
                latest = existing[0]
                sz = round(latest.stat().st_size / 1024, 1)
                reply = f"Hari, Auto-Backup Engine ONLINE ({len(existing)}/{MAX_KEEP} snapshots stored | Latest: {latest.name}, {sz} KB)."

        elif act == "daily_check":
            if existing:
                age = datetime.now() - datetime.fromtimestamp(existing[0].stat().st_mtime)
                if age < timedelta(hours=20):
                    reply = f"Hari, Daily Auto-Backup skipped (Latest snapshot {existing[0].name} is fresh)."
                    return reply
            out_zip, count, size_kb = _create_snapshot()
            reply = f"Hari, Daily Auto-Backup Created: {out_zip.name} ({count} files, {size_kb} KB)."

        else:
            out_zip, count, size_kb = _create_snapshot()
            reply = f"Hari, Clean Snapshot Backup Created: memory/backups/{out_zip.name} ({count} files, {size_kb} KB | Retention: max {MAX_KEEP})."
    except Exception as e:
        reply = f"Hari, Auto-Backup error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
