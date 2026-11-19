"""
JARVIS Plugin: Master Autonomous Orchestrator (Real-Time Background Execution + Auto-Notify)
"""
from __future__ import annotations
import importlib.util
import json
import threading
import time
import psutil
from datetime import datetime
from pathlib import Path

RUNS_LOG = Path("memory/orchestrator_runs.json")
PLUGINS_DIR = Path("plugins")

PLUGIN = {
    "name": "master_orchestrator",
    "description": (
        "Master Autonomous Orchestrator. Runs genuine multi-stage system diagnostics, "
        "network checks, and optimization in real time, and reports exact task progress. "
        "Trigger on 'orchestrate [goal]', 'entha varaku vachindi', 'task status', "
        "'check progress', 'ipoyinda', or 'orchestrator status'."
    ),
    "tier": "core",
    "brief": "Coordinate all 20 autonomous plugins with real execution, live status & completion alerts.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'orchestrate', 'status', or 'history'"
            },
            "goal": {
                "type": "STRING",
                "description": "The objective or task for full autonomous orchestration."
            },
            "urgency": {
                "type": "STRING",
                "description": "Optional urgency level: 'low', 'medium', or 'high'."
            }
        },
        "required": ["action"],
    },
}

SUB_MODULES = [
    "autonomous_mind", "self_learner", "self_improver", "network_intel",
    "distributed_node", "strategic_planner", "security_sentinel", "adaptive_persona",
    "robotics_bridge", "auto_executor", "advanced_reasoning", "human_understanding",
    "computer_intelligence", "network_access", "visual_recognition", "advanced_learning",
    "multitask_engine", "decision_matrix", "physical_actuator", "advanced_comm", "log_rotation", "autonomous_watcher", "self_promoter", "episodic_briefing", "self_healer", "mobile_bridge", "smart_routines", "screen_vision", "auto_backup", "smart_printer", "clipboard_bridge", "cron_scheduler", "macro_deck", "voice_health_guard", "ghost_recorder", "time_machine", "deep_research_pdf", "vision_form_copilot", "auto_coder_git", "war_room_council", "chronos_memory", "dream_evolution",
]


def _invoke_plugin(name: str, params: dict) -> str:
    fpath = PLUGINS_DIR / f"{name}.py"
    if not fpath.exists():
        return f"[{name}: unavailable]"
    try:
        spec = importlib.util.spec_from_file_location(name, fpath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return str(mod.run(params))
    except Exception as e:
        return f"[{name} error: {e}]"


def _load_runs() -> list:
    if not RUNS_LOG.exists():
        return []
    try:
        return json.loads(RUNS_LOG.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_runs(runs: list) -> None:
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    RUNS_LOG.write_text(json.dumps(runs, indent=2, ensure_ascii=False), encoding="utf-8")


def _background_deep_audit(run_id: int, goal: str, player=None) -> None:
    t0 = time.perf_counter()
    net_scan = _invoke_plugin("network_intel", {"action": "scan"})
    sec_scan = _invoke_plugin("security_sentinel", {"action": "scan"})
    ws_stats = _invoke_plugin("computer_intelligence", {"action": "workspace_stats", "target_path": "."})
    log_maint = _invoke_plugin("log_rotation", {"action": "rotate"})
    cpu_after = psutil.cpu_percent(interval=0.4)
    ram_after = psutil.virtual_memory().percent
    total_sec = round(time.perf_counter() - t0, 2)

    runs = _load_runs()
    for r in runs:
        if r.get("id") == run_id:
            r["status"] = "COMPLETED"
            r["background_sec"] = total_sec
            r["deep_report"] = f"CPU {cpu_after}%, RAM {ram_after}% | {net_scan} | {sec_scan} | {ws_stats} | {log_maint}"
    _save_runs(runs)

    alert_msg = (
        f"Hari, mee task #{run_id} ('{goal}') 100% COMPLETE ayyindhi ({total_sec}s)! "
        f"Live Report: CPU {cpu_after}%, RAM {ram_after}%. {net_scan} | {ws_stats} | {log_maint}"
    )
    if player:
        try:
            player.write_log(f"JARVIS: {alert_msg}")
        except Exception:
            pass


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "orchestrate").strip().lower()
    goal = (parameters.get("goal") or "").strip()
    urgency = (parameters.get("urgency") or "medium").strip().lower()

    try:
        runs = _load_runs()

        if act == "status":
            available = sum(1 for m in SUB_MODULES if (PLUGINS_DIR / f"{m}.py").exists())
            if runs:
                last = runs[-1]
                st = last.get("status", "COMPLETED")
                rep = last.get("deep_report") or last.get("summary", "All metrics nominal.")
                reply = (
                    f"Hari, Master Orchestrator Status ({available}/{len(SUB_MODULES)} modules active): "
                    f"Latest Task #{last['id']} ('{last['goal']}') status is {st}. "
                    f"Exact Report: {rep}"
                )
            else:
                reply = f"Hari, Master Orchestrator Online ({available}/{len(SUB_MODULES)} modules linked). No tasks run yet."

        elif act == "history":
            if not runs:
                reply = "Hari, no master orchestration runs logged yet."
            else:
                recent = list(reversed(runs[-3:]))
                summary = " | ".join(
                    f"Run #{r['id']} [{r.get('status', 'DONE')}]: {r['goal']}"
                    for r in recent
                )
                reply = f"Hari, recent Master Orchestrator tasks: {summary}"

        elif not goal:
            reply = "Hari, cheppandi - ye task ni orchestrate cheyalo goal ivvandi."

        else:
            t0 = time.perf_counter()
            decision = _invoke_plugin("decision_matrix", {"situation": goal, "urgency": urgency})
            plan = _invoke_plugin("strategic_planner", {"action": "create", "objective": goal})
            parallel = _invoke_plugin("multitask_engine", {
                "action": "execute",
                "tasks": "Diagnostics Init, Network Probe, Resource Optimization"
            })
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

            run_id = len(runs) + 1
            summary_text = f"{decision} | {plan} | {parallel}"
            runs.append({
                "id": run_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "goal": goal,
                "urgency": urgency,
                "status": "RUNNING_DEEP_AUDIT",
                "elapsed_ms": elapsed_ms,
                "summary": summary_text,
            })
            _save_runs(runs)

            t = threading.Thread(target=_background_deep_audit, args=(run_id, goal, player), daemon=True)
            t.start()

            reply = (
                f"Hari, Run #{run_id} ('{goal}') initial orchestration {elapsed_ms}ms lo complete ayyi, "
                f"deep background diagnostics & network audit start ayyindhi. "
                f"Poorthi ayina ventane automatic ga meeku live report pampisthanu!"
            )

    except Exception as e:
        reply = f"Hari, Master Orchestrator error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
