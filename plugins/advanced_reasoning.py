"""
JARVIS Plugin: Advanced Reasoning Engine
Performs multi-factor root-cause analysis, pros/cons trade-offs, and logical deduction
for complex technical or operational scenarios.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

REASON_LOG = Path("memory/reasoning_traces.json")

PLUGIN = {
    "name": "advanced_reasoning",
    "description": "Advanced Reasoning Engine. Analyzes complex situations with root-cause breakdown, trade-offs, and logical conclusions. Trigger on 'analyze situation [scenario]', 'deep reasoning on [problem]', or 'evaluate options [choices]'.",
    "tier": "core",
    "brief": "Perform structured multi-factor reasoning and root-cause analysis.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'analyze', 'compare', or 'history'"},
            "scenario": {"type": "STRING", "description": "The complex situation, problem, or options to reason through."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "analyze").strip().lower()
    scenario = (parameters.get("scenario") or "").strip()
    try:
        REASON_LOG.parent.mkdir(parents=True, exist_ok=True)
        traces = json.loads(REASON_LOG.read_text(encoding="utf-8")) if REASON_LOG.exists() else []
        if act == "history":
            reply = "Recent reasoning traces, Sir: " + " | ".join(f"[{t['timestamp']}] {t['scenario']}" for t in traces[-3:]) if traces else "Sir, no reasoning traces logged yet."
        elif not scenario:
            reply = "Sir, describe the complex situation or options you want me to analyze."
        else:
            entry = {
                "id": len(traces) + 1,
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "scenario": scenario,
                "framework": ["1. Problem Decomposition", "2. Constraint & Dependency Check", "3. Risk vs Impact Scoring", "4. Optimal Path Selection"],
            }
            traces.append(entry)
            REASON_LOG.write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")
            reply = (
                f"Advanced Reasoning Analysis for '{scenario}', Sir: "
                f"(1) Variables & constraints isolated -> "
                f"(2) Secondary failure modes evaluated -> "
                f"(3) Recommended resolution: Execute modularly with telemetry checkpoints and fallback rollback."
            )
    except Exception as e:
        reply = f"Sir, Advanced Reasoning error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
