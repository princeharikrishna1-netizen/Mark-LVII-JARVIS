import json
from pathlib import Path

STATE_FILE = Path("memory/mission_control.json")

TOOL = {
    "name": "mission_control",
    "description": "Breaks a large mission into subtasks and updates live progress on the JARVIS HUD.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "start | complete_step | status"},
            "mission_title": {"type": "STRING", "description": "Name of the main mission"},
            "steps": {"type": "STRING", "description": "Semicolon-separated subtasks (for start)"},
            "step_index": {"type": "INTEGER", "description": "1-based step index to mark done (for complete_step)"}
        },
        "required": ["action"]
    }
}

def run(params: dict = None, **kwargs) -> str:
    params = params or {}
    player = kwargs.get("player")
    action = str(params.get("action", "status")).lower()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    if action == "start":
        title = str(params.get("mission_title", "Active Mission")).strip()
        raw_steps = [s.strip() for s in str(params.get("steps", "")).split(";") if s.strip()]
        data = {"title": title, "steps": [{"task": s, "done": False} for s in raw_steps]}
        STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        if not STATE_FILE.exists():
            return "Mission Control: No active mission running."
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if action == "complete_step":
            idx = int(params.get("step_index", 1)) - 1
            if 0 <= idx < len(data["steps"]):
                data["steps"][idx]["done"] = True
                STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    done_cnt = sum(1 for s in data["steps"] if s["done"])
    total_cnt = max(1, len(data["steps"]))
    pct = int((done_cnt / total_cnt) * 100)
    bar = "█" * (pct // 10) + "░" * (10 - (pct // 10))
    lines = [f"🎯 MISSION: {data['title']} [{bar}] {pct}% ({done_cnt}/{total_cnt})"]
    for i, s in enumerate(data["steps"], 1):
        lines.append(f"  {'✅' if s['done'] else '⏳'} {i}. {s['task']}")
    report = "\n".join(lines)
    if player and hasattr(player, "show_content"):
        try:
            player.show_content(f"MISSION CONTROL ({pct}%)", report)
        except Exception:
            pass
    return report

PLUGIN = TOOL

