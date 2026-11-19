from __future__ import annotations
import tempfile as _tmp_pyc, os as _os_pyc
"""
JARVIS Plugin: Self-Evolution Auto-Promoter (Level 4 Autonomous Loop)
Validates, sandbox-tests, and promotes evolved scripts from memory/evolved_scripts/
into active JARVIS plugins and registers them with master_orchestrator.
"""
import importlib.util
import json
import py_compile
import re
from datetime import datetime
from pathlib import Path

EVOLVED_DIR = Path("memory/evolved_scripts")
PLUGINS_DIR = Path("plugins")
REGISTRY_FILE = Path("memory/promoted_registry.json")
ORCH_FILE = Path("plugins/master_orchestrator.py")

BLOCKED_PATTERNS = [
    r"\bshutil\.rmtree\b",
    r"\bos\.remove\b",
    r"\bos\.unlink\b",
    r"\bsubprocess\..*format\b",
    r"\beval\(",
]

PLUGIN = {
    "name": "self_promoter",
    "description": (
        "Self-Evolution Auto-Promoter. Audits, sandbox-tests, and promotes evolved scripts "
        "from memory/evolved_scripts into active JARVIS plugins automatically. "
        "Trigger on 'auto promote scripts', 'promote evolved helpers', or 'evolution status'."
    ),
    "tier": "core",
    "brief": "Audit, sandbox-test, and auto-promote evolved helper scripts into active plugins.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'promote_all', 'audit', or 'status'"
            },
            "script_name": {
                "type": "STRING",
                "description": "Optional specific filename inside memory/evolved_scripts to promote."
            }
        },
        "required": ["action"],
    },
}


def _load_registry() -> list:
    if not REGISTRY_FILE.exists():
        return []
    try:
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_registry(items: list) -> None:
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def _safety_check(code: str) -> tuple[bool, str]:
    for pat in BLOCKED_PATTERNS:
        if re.search(pat, code):
            return False, f"Blocked unsafe pattern matched: {pat}"
    return True, "Clean"


def _sandbox_test(script_path: Path) -> tuple[bool, str]:
    try:
        py_compile.compile(str(script_path), doraise=True)
        spec = importlib.util.spec_from_file_location(script_path.stem, script_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "run"):
            res = str(mod.run({"action": "status"}))
            return True, f"run() passed: {res[:80]}"
        if hasattr(mod, "execute"):
            res = str(mod.execute({}))
            return True, f"execute() passed: {res[:80]}"
        return True, "Module import & compile passed"
    except Exception as e:
        return False, f"Sandbox failure: {e}"


def _link_to_orchestrator(plugin_name: str) -> bool:
    if not ORCH_FILE.exists():
        return False
    otxt = ORCH_FILE.read_text(encoding="utf-8")
    if f'"{plugin_name}"' in otxt:
        return False
    anchor = '"autonomous_watcher",'
    if anchor in otxt:
        replacement = anchor + ' "' + plugin_name + '",'
        otxt = otxt.replace(anchor, replacement, 1)
        ORCH_FILE.write_text(otxt, encoding="utf-8")
        py_compile.compile(str(ORCH_FILE), doraise=True)
        return True
    return False


def _build_wrapper(clean_stem: str, src: Path, ts: str) -> str:
    lines = [
        f'"""JARVIS Auto-Promoted Plugin: {clean_stem} (Promoted on {ts})"""',
        "from __future__ import annotations",
        "import importlib.util",
        "from pathlib import Path",
        "",
        "PLUGIN = {",
        f'    "name": "{clean_stem}",',
        f'    "description": "Auto-evolved capability {clean_stem}. Trigger on run {clean_stem} or {clean_stem} status.",',
        '    "tier": "core",',
        f'    "brief": "Auto-promoted capability: {clean_stem}.",',
        '    "parameters": {',
        '        "type": "OBJECT",',
        '        "properties": {"action": {"type": "STRING", "description": "Action to execute (default status)."}},',
        '        "required": ["action"],',
        "    },",
        "}",
        "",
        f'_EVOLVED_SRC = Path("{src.as_posix()}")',
        "",
        "def run(parameters: dict, player=None, session_memory=None) -> str:",
        "    try:",
        f'        spec = importlib.util.spec_from_file_location("{src.stem}", _EVOLVED_SRC)',
        "        mod = importlib.util.module_from_spec(spec)",
        "        spec.loader.exec_module(mod)",
        '        if hasattr(mod, "execute"):',
        "            out = mod.execute(parameters)",
        '        elif hasattr(mod, "run"):',
        "            out = mod.run(parameters)",
        "        else:",
        f'            out = "Executed {clean_stem} capability cleanly."',
        '        reply = f"Hari, {out}"',
        "    except Exception as e:",
        f'        reply = f"Hari, {clean_stem} error: {{e}}"',
        "    if player:",
        "        try:",
        '            player.write_log(f"JARVIS: {reply}")',
        "        except Exception:",
        "            pass",
        "    return reply",
    ]
    return "\n".join(lines) + "\n"


def _promote_single(src: Path) -> str:
    clean_stem = re.sub(r"_helper$", "", src.stem)
    dst = PLUGINS_DIR / f"{clean_stem}.py"
    if dst.exists():
        _link_to_orchestrator(clean_stem)
        return f"{clean_stem}.py (already active & synced)"

    raw_code = src.read_text(encoding="utf-8")
    safe, reason = _safety_check(raw_code)
    if not safe:
        return f"{src.name} REJECTED ({reason})"

    ok, test_msg = _sandbox_test(src)
    if not ok:
        return f"{src.name} FAILED TEST ({test_msg})"

    if "PLUGIN =" in raw_code and "def run(" in raw_code:
        final_code = raw_code
    else:
        ts = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        final_code = _build_wrapper(clean_stem, src, ts)

    dst.write_text(final_code.strip() + "\n", encoding="utf-8")
    py_compile.compile(str(dst), doraise=True)
    linked = _link_to_orchestrator(clean_stem)

    reg = _load_registry()
    reg.append({
        "plugin": clean_stem,
        "source": src.as_posix(),
        "promoted_at": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "linked_orchestrator": linked,
    })
    _save_registry(reg)
    return f"{clean_stem}.py PROMOTED & LINKED (orchestrator={linked})"


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "promote_all").strip().lower()
    target = (parameters.get("script_name") or "").strip()

    try:
        EVOLVED_DIR.mkdir(parents=True, exist_ok=True)
        scripts = sorted(EVOLVED_DIR.glob("*.py"))

        if act == "status":
            reg = _load_registry()
            reply = (
                f"Hari, Self-Evolution Auto-Promoter Ready: {len(scripts)} evolved script(s) in sandbox | "
                f"{len(reg)} total auto-promoted plugin(s) registered."
            )
        elif act == "audit":
            if not scripts:
                reply = "Hari, sandbox is clean - 0 pending evolved scripts."
            else:
                checks = []
                for s in scripts:
                    safe, _ = _safety_check(s.read_text(encoding="utf-8"))
                    ok, msg = _sandbox_test(s)
                    checks.append(f"{s.name}: {'PASS' if (safe and ok) else 'FAIL'} ({msg})")
                reply = "Hari, Sandbox Audit: " + " | ".join(checks)
        else:
            if target:
                cand = EVOLVED_DIR / target
                if not cand.exists():
                    reply = f"Hari, evolved script '{target}' not found in sandbox."
                else:
                    reply = f"Hari, Auto-Promotion result: {_promote_single(cand)}"
            elif not scripts:
                reply = "Hari, no evolved scripts in sandbox to promote."
            else:
                results = [_promote_single(s) for s in scripts]
                reply = "Hari, Auto-Promotion Cycle Complete: " + " | ".join(results)
    except Exception as e:
        reply = f"Hari, Self-Promoter error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
