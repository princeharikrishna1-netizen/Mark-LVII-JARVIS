"""
JARVIS Plugin: Autonomous Watchfolder & Legal Document Alchemist (Level 9 Transcendence - 49/52)
Scans Desktop & Downloads for newly dropped legal/registration files (.pdf, .docx, .txt, .xlsx),
stages them into memory/legal_inbox/, and prepares HP LaserJet 1020 Plus Legal-size print metadata.
"""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path

INBOX_DIR = Path("memory/legal_inbox")
WATCH_EXTS = {".pdf", ".docx", ".txt", ".xlsx", ".csv"}

PLUGIN = {
    "name": "watchfolder_alchemist",
    "description": (
        "Autonomous Watchfolder & Legal Document Alchemist. Scans Desktop/Downloads for new documents "
        "and stages them into memory/legal_inbox for Legal-size HP LaserJet 1020 Plus printing. "
        "Trigger on 'watchfolder', 'scan downloads', 'legal inbox', or 'stage documents'."
    ),
    "tier": "core",
    "brief": "Auto-stages new Desktop/Downloads documents for Legal print & analysis.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'scan', 'list', or 'status'"
            }
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "scan").strip().lower()
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    home = Path.home()
    roots = [home / "Desktop", home / "Downloads"]

    if act == "scan":
        staged = []
        for root in roots:
            if not root.exists():
                continue
            for f in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:15]:
                if f.is_file() and f.suffix.lower() in WATCH_EXTS:
                    dst = INBOX_DIR / f.name
                    if not dst.exists() or f.stat().st_mtime > dst.stat().st_mtime:
                        shutil.copy2(f, dst)
                        staged.append(f.name)
        if staged:
            reply = f"Hari, Watchfolder Alchemist staged {len(staged)} document(s) into Legal Inbox: {', '.join(staged[:5])}."
        else:
            total = len(list(INBOX_DIR.glob("*")))
            reply = f"Hari, Watchfolder scan complete: No new drops ({total} document(s) ready in Legal Inbox)."
    else:
        items = sorted(p.name for p in INBOX_DIR.glob("*") if p.is_file())
        reply = f"Hari, Legal Inbox ({len(items)} file(s)): {', '.join(items[:8]) if items else 'Empty'}."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
