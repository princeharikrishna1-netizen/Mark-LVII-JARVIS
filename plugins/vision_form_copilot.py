"""
JARVIS Plugin: AI Vision Form Co-Pilot & Smart Typer (Level 6 Supreme - 38/40)
Combines screen_vision with Gemini Multimodal AI to inspect active web/desktop forms
and provide field-by-field guidance or safe SendKeys typing:
- inspect_form: Captures active PC screen and asks Gemini Vision to list visible form fields & next action
- type_fields: Safely types tab-separated field values into the currently focused window
"""
from __future__ import annotations
import subprocess
import time
from pathlib import Path

PLUGIN = {
    "name": "vision_form_copilot",
    "description": (
        "AI Vision Form Co-Pilot & Smart Typer. Captures screen, identifies visible form inputs/buttons via Gemini Vision, "
        "and assists with guided or automated tab-order filling. "
        "Trigger on 'form copilot', 'inspect form', 'autofill screen', or 'fill form'."
    ),
    "tier": "core",
    "brief": "AI Vision form inspector & tab-order smart auto-typer.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'inspect_form', 'type_fields', or 'status'"
            },
            "values": {
                "type": "STRING",
                "description": "Pipe-separated values (e.g., 'Hari Krishna|Kadapa|516309') for 'type_fields'."
            }
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    vals = (parameters.get("values") or "").strip()

    try:
        if act == "inspect_form":
            import plugins.screen_vision as sv
            prompt = (
                "Inspect this PC screen for any visible web form, portal login, or document input fields. "
                "List each visible field label in tab order and state what button to click next. Keep it concise."
            )
            reply = sv.run({"action": "analyze_pc", "question": prompt})

        elif act == "type_fields":
            if not vals:
                reply = "Hari, provide pipe-separated field values (e.g., 'Value1|Value2') to auto-type."
            else:
                items = [v.strip() for v in vals.split("|") if v.strip()]
                time.sleep(1.5)
                for idx, item in enumerate(items):
                    safe = item.replace("'", "''").replace("{", "{{").replace("}", "}}")
                    tab_suffix = "{TAB}" if idx < len(items) - 1 else ""
                    ps = (
                        "Add-Type -AssemblyName System.Windows.Forms; "
                        f"[System.Windows.Forms.SendKeys]::SendWait('{safe}{tab_suffix}')"
                    )
                    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=6)
                    time.sleep(0.35)
                reply = f"Hari, Vision Form Co-Pilot auto-typed {len(items)} field(s) in tab order."
        else:
            reply = "Hari, AI Vision Form Co-Pilot ONLINE (Gemini Multimodal Form Inspector + Tab-Order Auto-Typer ready)."
    except Exception as e:
        reply = f"Hari, Form Co-Pilot error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
