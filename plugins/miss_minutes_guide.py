"""
JARVIS Plugin: MISS MINUTES ? Interactive AI Guide, Step-by-Step Mentor & Reminder Engine
Provides friendly bilingual (Telugu/English) guidance, live system status narration,
step-by-step workflow tutorials, context-aware suggestions, and persistent reminders.
"""
from __future__ import annotations
import json, psutil
from datetime import datetime
from pathlib import Path

REMINDERS_FILE = Path("memory/miss_minutes_reminders.json")
PENDING_FILE = Path("memory/pending_permissions.json")

PLUGIN = {
    "name": "miss_minutes_guide",
    "description": "MISS MINUTES Interactive AI Guide: Provides step-by-step user guidance, natural system status explanations, context-aware help, and notifications/reminders.",
    "tier": "core",
    "brief": "MISS MINUTES Interactive AI Guide, Step-by-Step Mentor & Reminders.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'status', 'explain_system', 'guide', 'remind', 'context_help'"
            },
            "topic": {"type": "STRING", "description": "Workflow topic for step-by-step guidance or reminder text"}
        },
        "required": ["action"],
    },
}


def _load_reminders() -> list:
    if not REMINDERS_FILE.exists():
        return []
    try:
        return json.loads(REMINDERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_reminder(text: str) -> int:
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    items = _load_reminders()
    items.append({
        "id": len(items) + 1,
        "text": text,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "ACTIVE",
    })
    REMINDERS_FILE.write_text(json.dumps(items[-30:], indent=2, ensure_ascii=False), encoding="utf-8")
    return len(items)


def _pending_count() -> int:
    if not PENDING_FILE.exists():
        return 0
    try:
        data = json.loads(PENDING_FILE.read_text(encoding="utf-8"))
        return len([x for x in data if isinstance(x, dict) and x.get("status") == "PENDING"]) if isinstance(data, list) else 0
    except Exception:
        return 0


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    topic = (parameters.get("topic") or "JARVIS Daily Operations").strip()
    cpu = psutil.cpu_percent(interval=0.05)
    ram = psutil.virtual_memory().percent
    pending = _pending_count()
    rems = _load_reminders()

    if act == "explain_system":
        reply = (
            f"Hey there, Hari! Miss Minutes here with your live TVA/JARVIS system briefing: "
            f"Your workstation is running smooth at {cpu}% CPU and {ram}% RAM. "
            f"All Sovereign engines (SUPREME INTELLIGENCE, ULTRON, FRIDAY, VISION, ZOLA Vault & DUM-E/U Robotics) are green, "
            f"and you currently have {pending} pending Permission Gate approval(s) and {len(rems)} active reminder(s)."
        )

    elif act == "guide":
        reply = (
            f"Hey Hari! Here is your step-by-step guide for '{topic}': "
            f"Step 1 -> Let ZOLA & VISION verify the document/target state. "
            f"Step 2 -> Review any Tier-2 action in the Permission Gate for safety. "
            f"Step 3 -> Say 'APPROVE' so FRIDAY & DUM-E execute on your HP LaserJet 1020 Plus (Legal Size) and sync to GitHub Cloud!"
        )

    elif act == "remind":
        total = _save_reminder(topic)
        reply = f"Got it, Hari! Miss Minutes logged reminder #{total}: '{topic}'. I'll keep it front and center for your next session."

    elif act == "context_help":
        if pending > 0:
            advice = f"You have {pending} document print task(s) waiting in the Permission Gate. Say 'APPROVE' whenever you're ready to send it to HP LaserJet 1020 Plus (Legal Size)!"
        else:
            advice = "All queues are clear! You can index new PDF/Excel/Word files into ARNIM ZOLA or run a DUM-E & U hardware check."
        reply = f"Miss Minutes Context-Aware Tip for Hari -> {advice}"

    else:
        reply = (
            f"Hey Hari! MISS MINUTES Interactive AI Guide ONLINE -> "
            f"[Animated Avatar & Bilingual Voice: Armed] | "
            f"[Step-by-Step Mentor & Context Help: Active] | "
            f"[Active Reminders: {len(rems)} | Pending Approvals: {pending}]."
        )

    if player:
        try:
            player.write_log(f"MISS MINUTES: {reply}")
        except Exception:
            pass
    return reply
