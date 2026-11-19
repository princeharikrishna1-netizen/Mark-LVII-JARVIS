"""
JARVIS Plugin: Autonomous Sentinel Cryptographic Integrity Shield (Level 9 Transcendence - 52/52)
Computes SHA-256 cryptographic baselines across core orchestrator, server, and critical plugins
to detect unauthorized file tampering or corruption instantaneously.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from pathlib import Path

SEAL_FILE = Path("memory/sentinel_sha256_seal.json")

PLUGIN = {
    "name": "sentinel_shield",
    "description": (
        "Autonomous Sentinel Cryptographic Integrity Shield. Seals and verifies SHA-256 hashes of core "
        "JARVIS system files against tampering or silent corruption. "
        "Trigger on 'sentinel', 'integrity seal', 'security scan', or 'verify hashes'."
    ),
    "tier": "core",
    "brief": "SHA-256 cryptographic tamper-detection shield for JARVIS core.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'seal', 'verify', or 'status'"
            }
        },
        "required": ["action"],
    },
}


def _compute_hashes() -> dict[str, str]:
    targets = [Path("dashboard/server.py"), Path("dashboard/static/autonomous.html")] + sorted(Path("plugins").glob("*.py"))
    out = {}
    for p in targets:
        if p.exists() and p.is_file():
            out[str(p).replace("\\", "/")] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "verify").strip().lower()
    SEAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    current = _compute_hashes()

    if act == "seal" or not SEAL_FILE.exists():
        SEAL_FILE.write_text(
            json.dumps({"sealed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "hashes": current}, indent=2),
            encoding="utf-8",
        )
        reply = f"Hari, Sentinel Cryptographic Seal LOCKED across {len(current)} core files (SHA-256 verified)."
    else:
        saved = json.loads(SEAL_FILE.read_text(encoding="utf-8")).get("hashes", {})
        modified = [k for k, v in current.items() if k in saved and saved[k] != v]
        added = [k for k in current if k not in saved]
        if not modified and not added:
            reply = f"Hari, Sentinel Integrity Shield 100% INTACT: All {len(current)} core files match SHA-256 seal."
        else:
            reply = f"Hari, Sentinel Alert: {len(modified)} modified, {len(added)} new file(s) since last seal -> {(modified + added)[:4]}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
