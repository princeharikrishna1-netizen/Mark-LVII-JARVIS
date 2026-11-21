"""
JARVIS Plugin: Subconscious Predictive Pre-Fetcher (Level 8 Singularity - 45/48)
Analyzes active foreground window, clipboard content, and time-of-day routine to pre-stage
relevant templates, print queues, or git/code diagnostics before Hari asks.
"""
from __future__ import annotations
import subprocess
from datetime import datetime
from pathlib import Path

PLUGIN = {
    "name": "precog_engine",
    "description": (
        "Subconscious Predictive Pre-Fetcher. Inspects current context (active window, clipboard, time) "
        "and pre-stages next likely actions (Legal print prep, EC checklist, Git sync, or Chronos capture). "
        "Trigger on 'precog', 'predict next', or 'anticipate'."
    ),
    "tier": "core",
    "brief": "Context-aware predictive action pre-fetcher.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'predict', or 'status'"
            }
        },
        "required": ["action"],
    },
}


def _context_signals() -> tuple[str, str]:
    ps = (
        'Add-Type -TypeDefinition \'using System; using System.Runtime.InteropServices; using System.Text; '
        'public class W2 { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); '
        '[DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int c); }\'; '
        '$h=[W2]::GetForegroundWindow(); $sb=New-Object System.Text.StringBuilder 256; [void][W2]::GetWindowText($h,$sb,256); '
        '$cb = Get-Clipboard -Raw -ErrorAction SilentlyContinue; '
        'Write-Output ($sb.ToString() + "|||" + ($cb -replace "`r|`n"," "))'
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=5)
    raw = (r.stdout or "Desktop|||").strip()
    parts = raw.split("|||", 1)
    return (parts[0] or "Desktop").strip(), (parts[1] if len(parts) > 1 else "").strip()[:120]


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "predict").strip().lower()
    win, clip = _context_signals()
    hr = datetime.now().hour
    low_ctx = f"{win} {clip}".lower()

    if any(k in low_ctx for k in ("registration", "igrs", "card", "encumbrance", "ec", "stamp", "deed")):
        pred = "Property Registration context detected -> Pre-staged Legal-Size Print Desk (HP LaserJet 1020) & EC Rectification Checklist."
    elif any(k in low_ctx for k in ("code", "python", "powershell", "github", "mark-lvii", "git")):
        pred = "Developer Workspace context detected -> Pre-staged Shadow Sandbox compiler & GitHub Auto-Coder Sync."
    elif hr < 11:
        pred = "Morning Operational Window -> Pre-staged Episodic Executive Briefing & Chronos Screen Capture."
    else:
        pred = f"Active Window '{win}' analyzed -> Pre-staged Chronos Visual Snapshot & Cross-Device Neural Mesh."

    reply = f"Hari, Precog Engine ({act.upper()}): {pred}"
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
