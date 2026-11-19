"""
JARVIS Plugin: Multi-Step Autonomous Mission Commander (Level 10 Apotheosis - 55/56)
Chains multiple Level 7-10 engines into a single atomic mission pipeline:
1) Legal Watchfolder Scan -> 2) Legal Diff Audit -> 3) Chronos Visual Capture -> 4) Sentinel Integrity Verify.
"""
from __future__ import annotations

PLUGIN = {
    "name": "mission_commander",
    "description": (
        "Multi-Step Autonomous Mission Commander. Executes end-to-end chained missions across "
        "Watchfolder, Legal Auditor, Chronos Memory, and Sentinel Shield in one command. "
        "Trigger on 'mission', 'chain run', 'autonomous pipeline', or 'full sweep'."
    ),
    "tier": "core",
    "brief": "Executes chained multi-module autonomous missions.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'execute_sweep', or 'status'"
            }
        },
        "required": ["action"],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "execute_sweep").strip().lower()
    if act == "execute_sweep":
        import plugins.watchfolder_alchemist as wa
        import plugins.legal_diff_auditor as lda
        import plugins.chronos_memory as cm
        import plugins.sentinel_shield as sh

        s1 = wa.run({"action": "scan"})
        s2 = lda.run({"action": "audit"})
        s3 = cm.run({"action": "capture"})
        s4 = sh.run({"action": "verify"})
        reply = f"Hari, Autonomous Mission Sweep COMPLETE:\n1) {s1}\n2) {s2}\n3) {s3}\n4) {s4}"
    else:
        reply = "Hari, Multi-Step Autonomous Mission Commander ONLINE (4-stage chained sweep ready)."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
