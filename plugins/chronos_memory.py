"""
JARVIS Plugin: Chronos Temporal Visual Memory & Instant Screen Recall (Level 7 Omega - 42/44)
Captures lightweight perceptual screen snapshots + active window titles into SQLite (memory/chronos.db)
with automatic 30-frame rolling retention so Hari can recall past screen states or ask AI Vision about them.
"""
from __future__ import annotations
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path

DB_PATH = Path("memory/chronos.db")
SNAP_DIR = Path("memory/chronos_frames")

PLUGIN = {
    "name": "chronos_memory",
    "description": (
        "Chronos Temporal Visual Memory & Screen Recall. Logs timestamped screen snapshots & active window titles "
        "into SQLite so past on-screen documents, numbers, or windows can be recalled anytime. "
        "Trigger on 'chronos', 'visual memory', 'recall screen', or 'what was on my screen'."
    ),
    "tier": "core",
    "brief": "Photographic temporal screen memory & instant recall.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'capture', 'recall', or 'status'"
            },
            "query": {
                "type": "STRING",
                "description": "Window keyword or visual question to recall from recent screen history."
            }
        },
        "required": ["action"],
    },
}


def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS frames (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, window_title TEXT, img_path TEXT)"
    )
    conn.commit()
    return conn


def _active_window() -> str:
    ps = (
        'Add-Type -TypeDefinition \'using System; using System.Runtime.InteropServices; using System.Text; '
        'public class W { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); '
        '[DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int c); }\'; '
        '$h=[W]::GetForegroundWindow(); $sb=New-Object System.Text.StringBuilder 256; [void][W]::GetWindowText($h,$sb,256); Write-Output $sb.ToString()'
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=5)
    return (r.stdout or "Desktop").strip() or "Desktop"


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    query = (parameters.get("query") or "").strip()

    try:
        conn = _init_db()
        if act == "capture":
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fname = SNAP_DIR / f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
                "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); "
                "$g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen(0,0,0,0,$b.Size); "
                f"$bmp.Save('{fname.resolve()}', [System.Drawing.Imaging.ImageFormat]::Jpeg); $g.Dispose(); $bmp.Dispose();"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=8)
            win = _active_window()
            conn.execute("INSERT INTO frames (ts, window_title, img_path) VALUES (?, ?, ?)", (ts, win, str(fname)))
            conn.commit()
            # Keep last 30 frames
            old = conn.execute("SELECT id, img_path FROM frames ORDER BY id DESC LIMIT -1 OFFSET 30").fetchall()
            for oid, opath in old:
                Path(opath).unlink(missing_ok=True)
                conn.execute("DELETE FROM frames WHERE id=?", (oid,))
            conn.commit()
            reply = f"Hari, Chronos Visual Memory indexed frame at {ts} (Window: '{win}')."

        elif act == "recall":
            if query:
                rows = conn.execute(
                    "SELECT ts, window_title, img_path FROM frames WHERE window_title LIKE ? ORDER BY id DESC LIMIT 5",
                    (f"%{query}%",),
                ).fetchall()
            else:
                rows = conn.execute("SELECT ts, window_title, img_path FROM frames ORDER BY id DESC LIMIT 5").fetchall()
            if not rows:
                reply = "Hari, no matching Chronos visual frames found yet. Run 'capture' to index current screen."
            else:
                summary = "; ".join(f"[{r[0]}] {r[1]}" for r in rows)
                reply = f"Hari, Chronos Recall ({len(rows)} frame(s)): {summary}"
        else:
            cnt = conn.execute("SELECT COUNT(*) FROM frames").fetchone()[0]
            latest = conn.execute("SELECT ts, window_title FROM frames ORDER BY id DESC LIMIT 1").fetchone()
            tail = f"Latest: {latest[0]} ({latest[1]})" if latest else "No frames captured yet"
            reply = f"Hari, Chronos Temporal Visual Memory ONLINE ({cnt} indexed screen frames | {tail})."
        conn.close()
    except Exception as e:
        reply = f"Hari, Chronos Memory error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
