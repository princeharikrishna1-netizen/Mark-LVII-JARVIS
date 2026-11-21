import re
from pathlib import Path

TOOL = {
    "name": "threat_simulate_check",
    "description": "Analyzes a shell command, script, or file for malicious or destructive behavior before execution.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "payload": {"type": "STRING", "description": "Command string or file path to inspect"}
        },
        "required": ["payload"]
    }
}

_HIGH_RISK = [
    (r"\b(rm\s+-rf|del\s+/[sqf]|rmdir\s+/s|format\s+[a-z]:|diskpart|cipher\s+/w)\b", "Destructive disk/file wipe command"),
    (r"\b(reg\s+delete|bcdedit|net\s+user\s+.*\/add|schtasks\s+/create)\b", "System privilege or registry modification"),
    (r"(invoke-expression|iex\s*\(|downloadstring|encodedcommand|-enc\s+)", "Obfuscated remote PowerShell execution"),
    (r"(api_keys\.json|passwords|id_rsa|\.env)", "Sensitive credential file access")
]

def run(params: dict = None, **kwargs) -> str:
    payload = str((params or {}).get("payload", "")).strip()
    if not payload:
        return "Threat Simulation: Empty payload."
    text_to_scan = payload
    p = Path(payload)
    if p.exists() and p.is_file() and p.stat().st_size < 500_000:
        try:
            text_to_scan += "\n" + p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
    findings = [reason for pat, reason in _HIGH_RISK if re.search(pat, text_to_scan, re.I)]
    if findings:
        return f"🚨 THREAT SIMULATION BLOCKED [HIGH RISK]: {', '.join(findings)}. Explicit user confirmation required before running."
    return "✅ Threat Simulation [SAFE]: No destructive or credential-exfiltration patterns detected."

PLUGIN = TOOL

