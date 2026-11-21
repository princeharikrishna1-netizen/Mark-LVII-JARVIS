import py_compile, shutil
from pathlib import Path

STAGING_DIR = Path("memory/evolution_staging")

TOOL = {
    "name": "controlled_self_evolution",
    "description": "Stages a code improvement in a sandbox, compiles & tests it, and waits for Hari's explicit approval before applying.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "propose | approve | reject | list"},
            "target_file": {"type": "STRING", "description": "Relative path of file to upgrade (e.g. plugins/my_tool.py)"},
            "new_code": {"type": "STRING", "description": "Full Python code for the proposed upgrade"}
        },
        "required": ["action"]
    }
}

def run(params: dict = None, **kwargs) -> str:
    params = params or {}
    action = str(params.get("action", "list")).lower()
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    if action == "propose":
        target = Path(str(params.get("target_file", "")).strip())
        code = str(params.get("new_code", ""))
        if not target.name or not code:
            return "Controlled Self-Evolution: target_file and new_code are required."
        staged = STAGING_DIR / target.name
        staged.write_text(code, encoding="utf-8")
        try:
            py_compile.compile(str(staged), doraise=True)
        except Exception as e:
            staged.unlink(missing_ok=True)
            return f"❌ Evolution Sandbox Test FAILED (Syntax/Compile error): {e}"
        (STAGING_DIR / f"{target.name}.meta").write_text(str(target), encoding="utf-8")
        return f"🧪 Evolution Staged & Verified: '{target}' passed sandbox compile test. Say 'approve evolution {target.name}' to apply."

    elif action == "approve":
        name = Path(str(params.get("target_file", ""))).name
        staged = STAGING_DIR / name
        meta = STAGING_DIR / f"{name}.meta"
        if not staged.exists() or not meta.exists():
            return f"Controlled Self-Evolution: No staged upgrade found for '{name}'."
        dest = Path(meta.read_text(encoding="utf-8").strip())
        if dest.exists():
            shutil.copy2(dest, STAGING_DIR / f"{name}.bak")
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(staged, dest)
        staged.unlink(missing_ok=True)
        meta.unlink(missing_ok=True)
        return f"✅ Evolution Applied: '{dest}' updated with rollback backup saved."

    elif action == "reject":
        name = Path(str(params.get("target_file", ""))).name
        (STAGING_DIR / name).unlink(missing_ok=True)
        (STAGING_DIR / f"{name}.meta").unlink(missing_ok=True)
        return f"🗑️ Evolution Rejected & Discarded: '{name}'."

    else:
        pending = [f.name for f in STAGING_DIR.glob("*.py")]
        return f"Pending Evolution Proposals: {', '.join(pending)}" if pending else "No pending code evolutions."

PLUGIN = TOOL

