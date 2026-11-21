"""
JARVIS Plugin: Distributed Intelligence Coordinator (#5)
Coordinates multi-node task delegation and state sync between Master PC
and connected companion devices (iPad/Mobile Dashboard).
"""
from __future__ import annotations
import json, socket
from datetime import datetime
from pathlib import Path

NODES_FILE = Path("memory/distributed_nodes.json")

PLUGIN = {
    "name": "distributed_node",
    "description": "Distributed Intelligence Coordinator. Manages multi-device AI nodes (PC Master + iPad/Mobile workers) and delegates parallel tasks. Trigger on 'register node [name]', 'delegate task [task] to [node]', or 'distributed status'.",
    "tier": "core",
    "brief": "Coordinate multi-device AI nodes and delegate distributed tasks.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'status', 'register', or 'delegate'"},
            "node_name": {"type": "STRING", "description": "Target device/node name (e.g., 'iPad-Pro', 'Office-PC')."},
            "task": {"type": "STRING", "description": "Task description to queue for the node."}
        },
        "required": ["action"],
    },
}

def _load_state() -> dict:
    if not NODES_FILE.exists():
        return {"master": socket.gethostname(), "nodes": {}, "queue": []}
    try:
        return json.loads(NODES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"master": socket.gethostname(), "nodes": {}, "queue": []}

def _save_state(state: dict) -> None:
    NODES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NODES_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    node = (parameters.get("node_name") or "companion-node").strip()
    task = (parameters.get("task") or "").strip()
    try:
        state = _load_state()
        if act == "register":
            state["nodes"][node] = {"role": "worker", "status": "online", "last_seen": datetime.now().strftime("%Y-%m-%d %I:%M %p")}
            _save_state(state)
            reply = f"Distributed Intelligence: Node '{node}' registered under Master '{state['master']}', Hari."
        elif act == "delegate" and task:
            job_id = len(state["queue"]) + 1
            state["queue"].append({"id": job_id, "node": node, "task": task, "status": "dispatched", "time": datetime.now().strftime("%I:%M %p")})
            _save_state(state)
            reply = f"Task #{job_id} dispatched to node '{node}', Hari: '{task}'."
        else:
            node_list = ", ".join(f"{k} ({v['status']})" for k, v in state["nodes"].items()) or "None registered yet"
            reply = f"Distributed Mesh Status, Hari: Master='{state['master']}' | Worker Nodes: {node_list} | Queued Jobs: {len(state['queue'])}."
    except Exception as e:
        reply = f"Hari, Distributed Node error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
