"""
JARVIS Plugin: Strategic Planning Engine (#6)
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

PLANS_FILE = Path("memory/strategic_plans.json")

PLUGIN = {
    "name": "strategic_planner",
    "description": "Strategic Planning Engine. Creates multi-phase execution roadmaps for complex tasks. Trigger on 'create a strategic plan for [project]', 'make a roadmap for [goal]', or 'show strategic plans'.",
    "tier": "core",
    "brief": "Generate multi-phase strategic roadmaps for complex tasks.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'create', 'list', or 'complete'"},
            "objective": {"type": "STRING", "description": "The complex project or objective to plan."},
            "plan_id": {"type": "INTEGER", "description": "Plan ID when marking complete."}
        },
        "required": ["action"],
    },
}

def _load_plans() -> list[dict]:
    if not PLANS_FILE.exists(): return []
    try: return json.loads(PLANS_FILE.read_text(encoding="utf-8"))
    except Exception: return []

def _save_plans(plans: list[dict]) -> None:
    PLANS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PLANS_FILE.write_text(json.dumps(plans, indent=2, ensure_ascii=False), encoding="utf-8")

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "create").strip().lower()
    objective = (parameters.get("objective") or "").strip()
    plan_id = parameters.get("plan_id")
    try:
        plans = _load_plans()
        if act == "list":
            reply = "Strategic Plans on file, Sir: " + " | ".join(f"Plan #{p['id']} [{p['status']}]: {p['objective']}" for p in plans[-4:]) if plans else "Sir, no active strategic plans on record."
        elif act == "complete" and plan_id is not None:
            for p in plans:
                if p.get("id") == int(plan_id): p["status"] = "completed"
            _save_plans(plans)
            reply = f"Strategic Plan #{plan_id} marked as completed, Sir."
        elif not objective:
            reply = "Sir, specify the objective you want a strategic plan for."
        else:
            new_id = len(plans) + 1
            plans.append({"id": new_id, "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"), "objective": objective, "status": "active"})
            _save_plans(plans)
            reply = f"Strategic Plan #{new_id} formulated for '{objective}', Sir: Phase 1 (Recon & Backup) -> Phase 2 (Modular Execution) -> Phase 3 (Integrity Verification)."
    except Exception as e:
        reply = f"Sir, Strategic Planner error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
