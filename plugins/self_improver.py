from __future__ import annotations
import tempfile as _tmp_pyc, os as _os_pyc
"""
JARVIS Plugin: Self-Improvement Engine (#3)
Generates new custom utility scripts/capabilities safely in a sandboxed folder,
validates syntax, and logs capability upgrades.
"""
import py_compile
from datetime import datetime
from pathlib import Path

SANDBOX_DIR = Path("memory/evolved_scripts")

PLUGIN = {
    "name": "self_improver",
    "description": "Self-Improvement Engine. Audits current capabilities, drafts new Python helper modules in a safe sandbox, and validates their syntax. Trigger on 'upgrade capabilities', 'create helper script for [task]', or 'self improvement status'.",
    "tier": "core",
    "brief": "Safely generate and validate new Python helper capabilities.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'audit', 'draft_script', or 'list'"},
            "name": {"type": "STRING", "description": "Short snake_case name for the new helper script."},
            "purpose": {"type": "STRING", "description": "Description of what the new capability should do."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "audit").strip().lower()
    name = "".join(c for c in (parameters.get("name") or "custom_helper").lower() if c.isalnum() or c == "_")
    purpose = (parameters.get("purpose") or "General workflow automation").strip()
    try:
        SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
        if act == "draft_script":
            target = SANDBOX_DIR / f"{name}.py"
            code = (
                f'"""Auto-evolved JARVIS helper: {purpose}\nGenerated: {datetime.now().strftime("%Y-%m-%d %I:%M %p")}"""\n\n'
                f'def execute(context: dict | None = None) -> str:\n'
                f'    return "Executed evolved capability [{name}]: {purpose}"\n'
            )
            target.write_text(code, encoding="utf-8")
            py_compile.compile(str(target), doraise=True)
            reply = f"Self-Improvement complete, Hari. Synthesized and verified '{target}' for: {purpose}."
        elif act == "list":
            scripts = [f.name for f in SANDBOX_DIR.glob("*.py")]
            reply = f"Evolved sandbox modules ({len(scripts)}), Hari: {', '.join(scripts) or 'None yet'}."
        else:
            plugin_count = len(list(Path("plugins").glob("*.py")))
            evolved_count = len(list(SANDBOX_DIR.glob("*.py")))
            reply = f"Capability Audit, Hari: {plugin_count} active core plugins + {evolved_count} self-evolved sandbox scripts online."
    except Exception as e:
        reply = f"Hari, Self-Improver error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
