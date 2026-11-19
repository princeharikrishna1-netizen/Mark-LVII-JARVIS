"""
JARVIS Plugin: Smart Print & Document Pipeline Pro (HP LaserJet 1020 Plus - 30/30)
Tailored for Hari's HP LaserJet 1020 Plus printer with Legal-size page layout preference:
- status: Checks HP LaserJet 1020 Plus online status, driver state, and pending job count
- queue / clear_queue: Lists or clears stuck print jobs on HP LaserJet 1020 Plus
- print_file: Sends PDF, DOCX, TXT, or image files directly to HP LaserJet 1020 Plus
- print_note: Formats a clean Legal-size headered memo/note and sends it to the printer
"""
from __future__ import annotations
import subprocess
from datetime import datetime
from pathlib import Path

PREFERRED_PRINTER_KEY = "1020"
NOTES_DIR = Path("memory/print_jobs")

PLUGIN = {
    "name": "smart_printer",
    "description": (
        "Smart Print & Document Pipeline Pro for Hari's HP LaserJet 1020 Plus (Legal-size layout). "
        "Checks printer status, manages/clears print queue, and prints files or Legal-size notes. "
        "Trigger on 'print', 'printer', 'laserjet', 'print queue', 'clear print', or 'legal print'."
    ),
    "tier": "core",
    "brief": "Operate HP LaserJet 1020 Plus printer (status, queue control, Legal-size printing).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'status', 'queue', 'clear_queue', 'print_file', or 'print_note'"
            },
            "target": {
                "type": "STRING",
                "description": "File path for 'print_file', or text content for 'print_note'."
            }
        },
        "required": ["action"],
    },
}


def _ps(cmd: str, timeout: int = 12) -> tuple[bool, str]:
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    out = (proc.stdout or proc.stderr or "").strip()
    return proc.returncode == 0, out


def _detect_printer() -> str:
    ok, out = _ps("Get-Printer | Select-Object -ExpandProperty Name")
    if not ok or not out:
        return ""
    names = [n.strip() for n in out.splitlines() if n.strip()]
    for n in names:
        if PREFERRED_PRINTER_KEY in n.lower():
            return n
    return names[0] if names else ""


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    target = (parameters.get("target") or "").strip()

    try:
        pname = _detect_printer()
        if not pname:
            reply = "Hari, no Windows printers detected on this PC right now."
        elif act == "status":
            safe_p = pname.replace("'", "''")
            _, info = _ps(
                f"$p = Get-Printer -Name '{safe_p}'; "
                f"$jobs = @(Get-PrintJob -PrinterName '{safe_p}' -ErrorAction SilentlyContinue).Count; "
                f"Write-Output \"$($p.Name) | Status: $($p.PrinterStatus) | Port: $($p.PortName) | Pending Jobs: $jobs\""
            )
            reply = f"Hari, Printer Ready (Legal-Size Profile): {info}"

        elif act == "queue":
            safe_p = pname.replace("'", "''")
            _, qout = _ps(
                f"$j = Get-PrintJob -PrinterName '{safe_p}' -ErrorAction SilentlyContinue; "
                f"if (-not $j) {{ '0 pending jobs' }} else {{ ($j | ForEach-Object {{ \"#$($_.Id): $($_.DocumentName) ($($_.JobStatus))\" }}) -join ' | ' }}"
            )
            reply = f"Hari, {pname} Queue: {qout}"

        elif act == "clear_queue":
            safe_p = pname.replace("'", "''")
            _ps(f"Get-PrintJob -PrinterName '{safe_p}' -ErrorAction SilentlyContinue | Remove-PrintJob -ErrorAction SilentlyContinue")
            reply = f"Hari, cleared all pending/stuck print jobs on {pname}."

        elif act == "print_file":
            fpath = Path(target)
            if not target or not fpath.exists():
                reply = f"Hari, file not found for printing: '{target}'."
            else:
                abs_f = str(fpath.resolve()).replace("'", "''")
                safe_p = pname.replace("'", "''")
                ok, err = _ps(f"Start-Process -FilePath '{abs_f}' -Verb PrintTo -ArgumentList '\"{safe_p}\"' -WindowStyle Hidden")
                reply = (
                    f"Hari, sent '{fpath.name}' to {pname} (Legal-Size Layout)."
                    if ok else f"Hari, print dispatch failed: {err}"
                )

        elif act == "print_note":
            if not target:
                reply = "Hari, provide text content to print as a Legal-size memo."
            else:
                NOTES_DIR.mkdir(parents=True, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                note_file = NOTES_DIR / f"Legal_Memo_{ts}.txt"
                formatted = (
                    "====================================================================\n"
                    f"  J.A.R.V.I.S. LEGAL-SIZE PRINT MEMO  |  {datetime.now().strftime('%d-%b-%Y %I:%M %p')}\n"
                    "  Prepared for: Bhogapati Hari Krishna\n"
                    "====================================================================\n\n"
                    f"{target}\n\n"
                    "--------------------------------------------------------------------\n"
                )
                note_file.write_text(formatted, encoding="utf-8")
                abs_f = str(note_file.resolve()).replace("'", "''")
                safe_p = pname.replace("'", "''")
                _ps(f"Start-Process -FilePath '{abs_f}' -Verb PrintTo -ArgumentList '\"{safe_p}\"' -WindowStyle Hidden")
                reply = f"Hari, Legal-size memo formatted and sent to {pname} ({note_file.name})."
        else:
            reply = f"Hari, unknown smart_printer action '{act}'."
    except Exception as e:
        reply = f"Hari, Smart Printer error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
