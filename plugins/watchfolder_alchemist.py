"""
JARVIS Plugin: Autonomous Watchfolder & Legal Document Alchemist (Level 9 Transcendence - 49/52)
Scans Desktop & Downloads for newly dropped legal/registration files (.pdf, .docx, .txt, .xlsx, .png, .jpg),
stages them into memory/legal_inbox/, auto-extracts registration/EC tables to Excel (.xlsx) with
unmasked Aadhaar & relation columns (E/F/H), and optionally sends them to HP LaserJet 1020 Plus.
"""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path

INBOX_DIR = Path("memory/legal_inbox")
OUT_XLSX_DIR = INBOX_DIR / "extracted_xlsx"
WATCH_EXTS = {".pdf", ".docx", ".txt", ".xlsx", ".csv", ".png", ".jpg", ".jpeg"}

PLUGIN = {
    "name": "watchfolder_alchemist",
    "description": (
        "Autonomous Watchfolder & Legal Document Alchemist. Scans Desktop/Downloads for new documents, "
        "stages them into memory/legal_inbox, auto-extracts registration/EC/check-slip PDFs into structured "
        "Excel (.xlsx), and optionally prints on HP LaserJet 1020 Plus. Trigger on 'watchfolder', "
        "'scan downloads', 'legal inbox', 'process legal pipeline', or 'stage and print'."
    ),
    "tier": "core",
    "brief": "Auto-stages Desktop/Downloads docs, extracts registration Excel, & prints on LaserJet 1020.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'scan', 'process_pipeline', 'list', or 'status'"
            },
            "auto_print": {
                "type": "BOOLEAN",
                "description": "If true, sends generated Excel/staged files directly to HP LaserJet 1020 Plus."
            }
        },
        "required": ["action"],
    },
}


def _stage_files() -> list[Path]:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    home = Path.home()
    roots = [home / "Desktop", home / "Downloads"]
    staged = []
    for root in roots:
        if not root.exists():
            continue
        for f in sorted(root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:15]:
            if f.is_file() and f.suffix.lower() in WATCH_EXTS:
                dst = INBOX_DIR / f.name
                if not dst.exists() or f.stat().st_mtime > dst.stat().st_mtime:
                    shutil.copy2(f, dst)
                    staged.append(dst)
    return staged


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "process_pipeline").strip().lower()
    auto_print = bool(parameters.get("auto_print", False))
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    OUT_XLSX_DIR.mkdir(parents=True, exist_ok=True)

    if act == "scan":
        staged = _stage_files()
        if staged:
            reply = f"Hari, Watchfolder Alchemist staged {len(staged)} document(s) into Legal Inbox: {', '.join(f.name for f in staged[:5])}."
        else:
            total = len([x for x in INBOX_DIR.glob("*") if x.is_file()])
            reply = f"Hari, Watchfolder scan complete: No new drops ({total} document(s) ready in Legal Inbox)."

    elif act == "process_pipeline":
        staged = _stage_files()
        targets = staged if staged else sorted([x for x in INBOX_DIR.glob("*") if x.is_file() and x.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}], key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        if not targets:
            reply = "Hari, Legal Inbox lo process cheyadaniki kotha PDFs lekapovadam valla pipeline idle ga undi."
        else:
            from plugins import doc_to_excel, smart_printer
            logs = []
            for doc in targets:
                if doc.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
                    out_xlsx = OUT_XLSX_DIR / f"{doc.stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    res = doc_to_excel.run({
                        "file_path": str(doc.resolve()),
                        "mode": "extract_excel",
                        "output_excel": str(out_xlsx.resolve()),
                    }, player=player, session_memory=session_memory)
                    logs.append(f"{doc.name} -> {out_xlsx.name}")
                    if auto_print and out_xlsx.exists():
                        p_res = smart_printer.run({"action": "print_file", "target": str(out_xlsx.resolve())}, player=player)
                        logs.append(f"Printed: {p_res}")
                elif auto_print:
                    p_res = smart_printer.run({"action": "print_file", "target": str(doc.resolve())}, player=player)
                    logs.append(f"{doc.name} -> {p_res}")
            reply = f"Hari, Auto-Pipeline complete ({len(targets)} file(s)): " + " | ".join(logs)
    else:
        items = sorted(p.name for p in INBOX_DIR.glob("*") if p.is_file())
        reply = f"Hari, Legal Inbox ({len(items)} file(s)): {', '.join(items[:8]) if items else 'Empty'}."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
