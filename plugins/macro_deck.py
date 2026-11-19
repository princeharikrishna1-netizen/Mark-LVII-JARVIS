"""
JARVIS Plugin: Voice Macro & One-Tap Workflow Deck (Level 6 Supreme - 33/34)
Parses jarvis_macros.txt and executes multi-step desktop/system/vision/printer macros:
- list: Lists all available built-in + jarvis_macros.txt workflows
- run_macro: Executes a named macro sequence (e.g., 'work_desk', 'full_audit', 'vision_check', 'clean_boost')
- add_macro: Appends a custom macro shortcut into jarvis_macros.txt
"""
from __future__ import annotations
from pathlib import Path

MACROS_FILE = Path("jarvis_macros.txt")

BUILTIN_MACROS = {
    "work_desk": "Activate Work Mode + Check HP LaserJet 1020 Printer + Sync Clipboard",
    "full_audit": "Run Self-Healer Watchdog + Master Orchestrator Diagnostics",
    "vision_check": "Capture PC Screen + Gemini AI Visual Analysis",
    "clean_boost": "Rotate Logs + Clear Stuck Print Queue + Create Snapshot Backup",
}

PLUGIN = {
    "name": "macro_deck",
    "description": (
        "Voice Macro & One-Tap Workflow Deck. Executes multi-step automation macros and reads jarvis_macros.txt. "
        "Trigger on 'macro', 'run macro', 'workflow deck', or 'quick macro'."
    ),
    "tier": "core",
    "brief": "One-tap multi-step workflow macros & jarvis_macros.txt launcher.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'list', 'run_macro', or 'add_macro'"
            },
            "name": {
                "type": "STRING",
                "description": "Macro key name (e.g., 'work_desk', 'full_audit', 'vision_check', 'clean_boost')."
            },
            "steps": {
                "type": "STRING",
                "description": "Macro description/steps when action is 'add_macro'."
            }
        },
        "required": ["action"],
    },
}


def _read_custom_macros() -> dict[str, str]:
    custom = {}
    if MACROS_FILE.exists():
        lines = MACROS_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines):
            s = line.strip()
            if not s or s.startswith("#") or s.startswith(";"):
                continue
            if "::" in s:
                hk, rest = s.split("::", 1)
                label = hk.strip().replace("^!", "Ctrl+Alt+").upper()
                action = rest.strip() or (lines[i + 1].strip() if i + 1 < len(lines) else "AHK Hotkey")
                custom[f"hotkey_{hk.strip()}"] = f"{label} -> {action}"
            elif ":" in s and not s.lower().startswith(("run", "http", "c:\\")):
                k, v = s.split(":", 1)
                custom[k.strip().lower().replace(" ", "_")] = v.strip()
    return custom


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "list").strip().lower()
    name = (parameters.get("name") or "").strip().lower().replace(" ", "_")
    steps = (parameters.get("steps") or "").strip()

    try:
        all_macros = dict(BUILTIN_MACROS)
        all_macros.update(_read_custom_macros())

        if act == "add_macro":
            if not name or not steps:
                reply = "Hari, provide both macro 'name' and 'steps' to save."
            else:
                existing = MACROS_FILE.read_text(encoding="utf-8") if MACROS_FILE.exists() else ""
                MACROS_FILE.write_text(existing.rstrip() + f"\n{name}: {steps}\n", encoding="utf-8")
                reply = f"Hari, saved macro '{name}' into jarvis_macros.txt."

        elif act == "run_macro":
            if name in ("work_desk", "work"):
                import plugins.smart_routines as sr, plugins.smart_printer as sp, plugins.clipboard_bridge as cb
                r1 = sr.run({"routine": "work_mode"})
                r2 = sp.run({"action": "status"})
                r3 = cb.run({"action": "status"})
                reply = f"Hari, Macro [Work Desk] Complete -> {r1} | {r2} | {r3}"
            elif name in ("full_audit", "audit"):
                import plugins.self_healer as sh, plugins.master_orchestrator as mo
                r1 = sh.run({"action": "audit"})
                r2 = mo.run({"action": "status"})
                reply = f"Hari, Macro [Full Audit] Complete -> {r1} | {r2}"
            elif name in ("vision_check", "vision"):
                import plugins.screen_vision as sv
                reply = sv.run({"action": "analyze_pc"})
            elif name in ("clean_boost", "clean"):
                import plugins.log_rotation as lr, plugins.smart_printer as sp, plugins.auto_backup as ab
                r1 = lr.run({"action": "rotate"})
                r2 = sp.run({"action": "clear_queue"})
                r3 = ab.run({"action": "backup"})
                reply = f"Hari, Macro [Clean Boost] Complete -> {r1} | {r2} | {r3}"
            elif name in all_macros:
                reply = f"Hari, Macro [{name}] Dispatched: {all_macros[name]}"
            else:
                reply = f"Hari, macro '{name}' not found. Available: {', '.join(all_macros.keys())}"
        else:
            items = [f"{k} ({v})" for k, v in all_macros.items()]
            reply = f"Hari, Macro Deck Ready ({len(all_macros)} macros): " + " | ".join(items)
    except Exception as e:
        reply = f"Hari, Macro Deck error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
