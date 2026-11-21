import ctypes
import re
from datetime import datetime

TOOL = {
    "name": "get_live_context",
    "description": (
        "Returns the user's current active desktop context: foreground window title, "
        "active application process, clipboard text preview (sanitized), and time of day. "
        "Call this when the user says 'this', 'here', 'current window', or asks about what they are doing."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    },
}

_SENSITIVE_RE = re.compile(r"(api[_-]?key|secret|password|token|bearer\s+[a-z0-9\-_]+|sk-[a-z0-9]+)", re.I)

def _get_active_window() -> str:
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "Desktop"
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return "Desktop"
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value.strip()
        return title[:120] if title else "Desktop"
    except Exception:
        return "Unknown"

def _get_clipboard_preview() -> str:
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        try:
            text = r.clipboard_get()
        except Exception:
            text = ""
        finally:
            r.destroy()
        text = " ".join(str(text).split()).strip()
        if not text:
            return ""
        if _SENSITIVE_RE.search(text):
            return "[REDACTED_SENSITIVE_CLIPBOARD]"
        return text[:300]
    except Exception:
        return ""

def get_snapshot() -> str:
    win = _get_active_window()
    clip = _get_clipboard_preview()
    now = datetime.now().strftime("%I:%M %p")
    parts = [f"Time: {now}", f"Active Window: '{win}'"]
    if clip:
        parts.append(f"Clipboard: '{clip}'")
    return " | ".join(parts)

def run(params: dict = None, **kwargs) -> str:
    return f"Live Context -> {get_snapshot()}"

PLUGIN = TOOL

