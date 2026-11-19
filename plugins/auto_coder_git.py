"""
JARVIS Plugin: Self-Coding Plugin Generator & GitHub Sync Bridge (Level 6 Supreme - 39/40)
Generates verified Python plugins via Gemini AI (with automatic py_compile check) and syncs repo changes to GitHub:
- generate_plugin: Writes a new plugins/<name>.py from specification and verifies syntax
- git_status: Checks local git branch, modified files, and remote status
- git_push: Stages, commits, and pushes updates to configured GitHub remote
"""
from __future__ import annotations
import json
import os
import py_compile
import subprocess
import urllib.request
from datetime import datetime
from pathlib import Path

API_KEYS_FILE = Path("config/api_keys.json")

PLUGIN = {
    "name": "auto_coder_git",
    "description": (
        "JARVIS Auto-Coder & GitHub Sync Bridge. Generates syntax-verified Python plugins from prompts "
        "and manages git status/commit/push to GitHub. "
        "Trigger on 'auto coder', 'write plugin', 'git status', 'git push', or 'github sync'."
    ),
    "tier": "core",
    "brief": "Self-coding plugin generator & one-click GitHub commit/push bridge.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'status', 'git_status', 'git_push', or 'generate_plugin'"
            },
            "spec": {
                "type": "STRING",
                "description": "Commit message for 'git_push', or 'plugin_name: description' for 'generate_plugin'."
            }
        },
        "required": ["action"],
    },
}


def _get_key() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    if API_KEYS_FILE.exists():
        try:
            d = json.loads(API_KEYS_FILE.read_text(encoding="utf-8"))
            for k in ("gemini_api_key", "GEMINI_API_KEY", "api_key"):
                if isinstance(d.get(k), str) and d[k].strip():
                    return d[k].strip()
        except Exception:
            pass
    return ""


def _find_git() -> str:
    import shutil
    g = shutil.which("git")
    if g:
        return g
    for cand in (
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Users\IGRS\AppData\Local\Programs\Git\cmd\git.exe",
    ):
        if Path(cand).exists():
            return cand
    return ""


def _git(args: list[str]) -> tuple[bool, str]:
    g = _find_git()
    if not g:
        return False, "Git for Windows not installed yet (run: winget install Git.Git)"
    p = subprocess.run([g] + args, capture_output=True, text=True, timeout=25)
    out = (p.stdout or p.stderr or "").strip()
    return p.returncode == 0, out



def _gemini_text_generate(prompt: str, key: str) -> str:
    import json, urllib.request
    models = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash"]
    try:
        with urllib.request.urlopen(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}", timeout=10) as r:
            listed = [
                m["name"].replace("models/", "")
                for m in json.loads(r.read().decode("utf-8")).get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m.get("name", "")
            ]
            if listed:
                models = listed + [m for m in models if m not in listed]
    except Exception:
        pass
    last_err = None
    for mdl in models[:4]:
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={key}"
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last_err = e
    raise RuntimeError(f"All Gemini models failed: {last_err}")


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    spec = (parameters.get("spec") or "").strip()

    try:
        if act == "git_status":
            ok, out = _git(["status", "-s"])
            if not ok:
                reply = f"Hari, Git status check: {out}"
            else:
                lines = [l for l in out.splitlines() if l.strip()]
                reply = f"Hari, Git Repository Status ({len(lines)} changed file(s)): " + (", ".join(lines[:8]) if lines else "Working tree clean")

        elif act == "git_push":
            msg = spec or f"JARVIS Mark-LVII Auto-Sync ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
            _git(["add", "-A"])
            ok_c, out_c = _git(["commit", "-m", msg])
            ok_p, out_p = _git(["push"])
            if ok_p:
                reply = f"Hari, GitHub Auto-Push COMPLETE: '{msg}' -> {out_p}"
            else:
                reply = f"Hari, Local Commit: {out_c} | Remote Push Note: {out_p}"

        elif act == "generate_plugin":
            if ":" not in spec:
                reply = "Hari, use format 'plugin_name: what it should do' to auto-generate a plugin."
            else:
                pname, desc = spec.split(":", 1)
                pname = "".join(c if c.isalnum() or c == "_" else "_" for c in pname.strip().lower()).strip("_")
                key = _get_key()
                if not key:
                    reply = "Hari, Gemini API key missing for Auto-Coder."
                else:
                    prompt = (
                        f"Write a clean, standalone Python plugin file for J.A.R.V.I.S. named '{pname}' that does: {desc.strip()}. "
                        "Must define PLUGIN dict (with name, description, tier='core', brief, parameters) and "
                        "def run(parameters: dict, player=None, session_memory=None) -> str addressing user as 'Hari'. "
                        "Output ONLY valid Python code, no markdown fences."
                    )
                    code = _gemini_text_generate(prompt, key)
                    code = code.removeprefix("```python").removeprefix("```").removesuffix("```").strip()
                    out_p = Path(f"plugins/{pname}.py")
                    out_p.write_text(code + "\n", encoding="utf-8")
                    py_compile.compile(str(out_p), doraise=True)
                    reply = f"Hari, Auto-Coder generated & syntax-verified 'plugins/{pname}.py'!"
        else:
            reply = "Hari, JARVIS Auto-Coder & GitHub Sync Bridge ONLINE (Self-Plugin Generator + py_compile Guard + Git Push ready)."
    except Exception as e:
        reply = f"Hari, Auto-Coder / Git error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
