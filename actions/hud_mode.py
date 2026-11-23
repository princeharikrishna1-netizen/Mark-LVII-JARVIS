"""
actions/hud_mode.py — Live HUD Overlay Profile, Opacity & Theme Switcher.
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QApplication


_ACCENT_PRESETS = {
    "cyan": "#00E5FF",
    "blue": "#2979FF",
    "red": "#FF2A55",
    "crimson": "#FF1744",
    "gold": "#FFB300",
    "amber": "#FF9100",
    "green": "#00E676",
    "emerald": "#00C853",
    "purple": "#D500F9",
    "violet": "#AA00FF",
}


def switch_hud_mode(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    profile = (parameters.get("profile") or "full").strip().lower()
    color_name = (parameters.get("accent_color") or "").strip().lower()
    accent_hex = _ACCENT_PRESETS.get(color_name, color_name if color_name.startswith("#") else "")

    app = QApplication.instance()
    if app is None:
        return "HUD GUI is not currently running."

    triggered = False
    for widget in app.topLevelWidgets():
        sig = getattr(widget, "_hud_profile_sig", None)
        if sig is not None:
            sig.emit(profile, accent_hex)
            triggered = True
            break

    if not triggered:
        return "Could not locate active HUD MainWindow."

    msg = f"Switched HUD to '{profile}' mode"
    if color_name:
        msg += f" with '{color_name}' accent theme"
    return msg + "."


TOOL = {
    "name": "switch_hud_mode",
    "description": (
        "PRIMARY tool for switching the main HUD visual appearance, centrepiece (3D reactor core vs avatar face), "
        "overlay size/transparency (full, gaming, compact, stealth/ghost mode), or accent color theme live. "
        "ALWAYS use this tool (not open_feature_hud) when the user asks for reactor core, avatar face, "
        "gaming mode, compact overlay, stealth mode, full HUD, or changing HUD colors."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "profile": {
                "type": "STRING",
                "description": "'full' (normal full HUD), 'gaming' or 'compact' (top-right translucent overlay), 'stealth' (ultra-minimal bottom-right ghost HUD), 'reactor' (3D reactor core), or 'face' (holographic avatar).",
            },
            "accent_color": {
                "type": "STRING",
                "description": "Optional color theme name ('cyan', 'red', 'gold', 'green', 'purple', 'blue') or hex code.",
            },
        },
        "required": ["profile"],
    },
    "handler": switch_hud_mode,
}
