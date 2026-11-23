"""
actions/ps_runner.py — Safe PowerShell Command Runner for Windows Diagnostics & Automation.
Blocks destructive system/disk/registry commands while enabling fast CLI execution.
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

_DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bremove-item\b.*(-recurse|-force)",
    r"\bdel\s+/[sqf]",
    r"\brd\s+/s",
    r"\bformat-volume\b",
    r"\bformat\s+[a-z]:",
    r"\bclear-disk\b",
    r"\bstop-computer\b",
    r"\brestart-computer\b",
    r"\bshutdown\b",
    r"\breg\s+delete\b",
    r"\bbcdedit\b",
    r"\bdiskpart\b",
    r"\bnet\s+user\b.*(/delete|/add)",
    r"\binvoke-expression\b",
    r"\biex\b",
]


def _is_blocked(cmd: str) -> str | None:
    low = cmd.strip().lower()
    for pat in _DANGEROUS_PATTERNS:
        if re.search(pat, low):
            return f"Blocked unsafe command matching safety rule: '{pat}'"
    return None


def run_powershell(command: str, timeout: int = 15) -> str:
    cmd = (command or "").strip()
    if not cmd:
        return "No PowerShell command provided."

    blocked_reason = _is_blocked(cmd)
    if blocked_reason:
        return blocked_reason

    cwd = Path(__file__).resolve().parent.parent
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(3, min(timeout, 30)),
        )
        stdout = (res.stdout or "").strip()
        stderr = (res.stderr or "").strip()

        if res.returncode == 0:
            out = stdout or "(Command completed with no output)"
            return out[:3000]
        err = stderr or stdout or f"Exited with code {res.returncode}"
        return f"PowerShell Error (code {res.returncode}):\n{err[:2000]}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s."
    except Exception as e:
        return f"Execution failed: {e}"


def ps_runner(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    command = (parameters.get("command") or "").strip()
    timeout = int(parameters.get("timeout") or 15)
    return run_powershell(command, timeout=timeout)


TOOL = {
    "name": "ps_runner",
    "description": (
        "Executes safe, read-only or diagnostic PowerShell commands on Windows (such as checking "
        "disk space, IP/network status, open ports, installed Python packages, system uptime, or running scripts) "
        "and returns the terminal output. Destructive commands are blocked automatically."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "command": {
                "type": "STRING",
                "description": "The PowerShell command to run (e.g., 'Get-PSDrive -PSProvider FileSystem', 'Test-Connection 8.8.8.8 -Count 2', 'netstat -ano | findstr :8000').",
            },
            "timeout": {
                "type": "INTEGER",
                "description": "Optional timeout in seconds (default 15, max 30).",
            },
        },
        "required": ["command"],
    },
    "handler": ps_runner,
}
