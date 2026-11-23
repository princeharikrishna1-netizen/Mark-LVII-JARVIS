"""
actions/window_snapper.py — Smart Window Layout & Workspace Manager for Windows.
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import pygetwindow as gw


def _get_work_area() -> tuple[int, int, int, int]:
    """Returns primary monitor work area (left, top, width, height) excluding taskbar."""
    rect = wintypes.RECT()
    SPI_GETWORKAREA = 0x0030
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def _find_window(app_query: str):
    """Finds the best matching visible window by title substring (case-insensitive)."""
    q = (app_query or "").strip().lower()
    if not q or q in ("current", "active", "this", "window"):
        return gw.getActiveWindow()

    aliases = {
        "vscode": "visual studio code",
        "vs code": "visual studio code",
        "code": "visual studio code",
        "terminal": "powershell",
        "cmd": "command prompt",
        "browser": "chrome",
    }
    q = aliases.get(q, q)

    candidates = []
    for win in gw.getAllWindows():
        title = (win.title or "").strip()
        if not title or not win.visible:
            continue
        if q in title.lower():
            candidates.append(win)

    return candidates[0] if candidates else None


def snap_window(app_name: str = "active", position: str = "left") -> str:
    win = _find_window(app_name)
    if not win:
        return f"Could not find an open window matching '{app_name}'."

    pos = (position or "left").strip().lower().replace("-", "_").replace(" ", "_")
    label = win.title[:45]

    try:
        if pos == "minimize":
            win.minimize()
            return f"Minimized '{label}'."

        if win.isMinimized:
            win.restore()

        if pos == "maximize":
            win.maximize()
            return f"Maximized '{label}'."

        if pos == "restore":
            win.restore()
            return f"Restored '{label}'."

        if win.isMaximized:
            win.restore()

        wx, wy, ww, wh = _get_work_area()
        half_w = ww // 2
        half_h = wh // 2

        zones = {
            "left":         (wx, wy, half_w, wh),
            "right":        (wx + half_w, wy, half_w, wh),
            "top":          (wx, wy, ww, half_h),
            "bottom":       (wx, wy + half_h, ww, half_h),
            "top_left":     (wx, wy, half_w, half_h),
            "top_right":    (wx + half_w, wy, half_w, half_h),
            "bottom_left":  (wx, wy + half_h, half_w, half_h),
            "bottom_right": (wx + half_w, wy + half_h, half_w, half_h),
            "center":       (wx + int(ww * 0.12), wy + int(wh * 0.08), int(ww * 0.76), int(wh * 0.84)),
        }

        if pos not in zones:
            return f"Unknown position '{position}'. Use left, right, maximize, minimize, or center."

        x, y, w, h = zones[pos]
        win.moveTo(x, y)
        win.resizeTo(w, h)
        try:
            win.activate()
        except Exception:
            pass
        return f"Snapped '{label}' to {pos}."
    except Exception as e:
        return f"Failed to snap '{label}': {e}"


def split_screen(left_app: str, right_app: str) -> str:
    res_l = snap_window(left_app, "left")
    res_r = snap_window(right_app, "right")
    return f"{res_l} | {res_r}"


def focus_only(app_name: str = "active") -> str:
    target = _find_window(app_name)
    if not target:
        return f"Could not find window matching '{app_name}'."

    for win in gw.getAllWindows():
        try:
            if win._hWnd != target._hWnd and win.visible and not win.isMinimized and win.title.strip():
                win.minimize()
        except Exception:
            pass

    if target.isMinimized:
        target.restore()
    target.maximize()
    try:
        target.activate()
    except Exception:
        pass
    return f"Focus mode enabled on '{target.title[:45]}'."


def window_snapper(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    mode = (parameters.get("mode") or "snap").strip().lower()
    app_name = parameters.get("app_name") or "active"
    position = parameters.get("position") or "left"
    left_app = parameters.get("left_app") or ""
    right_app = parameters.get("right_app") or ""

    if mode == "split" and left_app and right_app:
        return split_screen(left_app, right_app)
    if mode == "focus":
        return focus_only(app_name)
    return snap_window(app_name, position)


TOOL = {
    "name": "window_snapper",
    "description": (
        "Arranges, snaps, maximizes, minimizes, or split-screens open desktop windows. "
        "Use this whenever the user asks to move a window to the left/right/center, "
        "put two apps side-by-side in split screen, maximize/minimize a window, "
        "or enter focus mode on a single window."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "mode": {
                "type": "STRING",
                "description": "Layout mode: 'snap' (single window), 'split' (two windows side-by-side), or 'focus' (maximize one and minimize all others).",
            },
            "app_name": {
                "type": "STRING",
                "description": "Target application name or window title (e.g., 'Visual Studio Code', 'Chrome', 'PowerShell', or 'active').",
            },
            "position": {
                "type": "STRING",
                "description": "For mode='snap': 'left', 'right', 'top', 'bottom', 'top_left', 'top_right', 'bottom_left', 'bottom_right', 'maximize', 'minimize', 'center', or 'restore'.",
            },
            "left_app": {
                "type": "STRING",
                "description": "For mode='split': application name for the left half of the screen.",
            },
            "right_app": {
                "type": "STRING",
                "description": "For mode='split': application name for the right half of the screen.",
            },
        },
        "required": ["mode"],
    },
    "handler": window_snapper,
}
