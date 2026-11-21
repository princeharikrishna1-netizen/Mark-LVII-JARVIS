"""
JARVIS Plugin: Multi-Agent War-Room Council (Level 7 Omega - 41/44)
Simulates a 3-persona parallel advisory board (Strategist + Red-Team Auditor + Execution Commander)
using live Gemini model auto-discovery to stress-test critical decisions, legal drafts, or code architectures.
"""
from __future__ import annotations
import json
import os
import urllib.request
from pathlib import Path

API_KEYS_FILE = Path("config/api_keys.json")

PLUGIN = {
    "name": "war_room_council",
    "description": (
        "Multi-Agent War-Room Council. Runs a 3-agent debate (Strategist, Red-Team Auditor, Execution Commander) "
        "to stress-test complex decisions, property/legal workflows, or system architecture. "
        "Trigger on 'war room', 'council', 'debate', or 'stress test'."
    ),
    "tier": "core",
    "brief": "3-Agent AI War-Room debate (Strategist vs Red-Team vs Commander).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'convene', or 'status'"
            },
            "topic": {
                "type": "STRING",
                "description": "Problem, decision, or strategy for the 3-agent council to analyze."
            }
        },
        "required": ["action"],
    },
}


def _get_key() -> str:
    if os.environ.get("GEMINI_API_KEY"):
        return os.environ["GEMINI_API_KEY"].strip()
    if API_KEYS_FILE.exists():
        try:
            d = json.loads(API_KEYS_FILE.read_text(encoding="utf-8"))
            for k in ("gemini_api_key", "GEMINI_API_KEY", "api_key"):
                if isinstance(d.get(k), str) and d[k].strip():
                    return d[k].strip()
        except Exception:
            pass
    return ""


def _call_gemini(prompt: str, key: str) -> str:
    models = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash"]
    try:
        with urllib.request.urlopen(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}", timeout=8) as r:
            listed = [
                m["name"].replace("models/", "")
                for m in json.loads(r.read().decode("utf-8")).get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m.get("name", "")
            ]
            if listed:
                models = listed + [m for m in models if m not in listed]
    except Exception:
        pass
    for mdl in models[:4]:
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={key}"
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            continue
    return "Council offline: Gemini endpoint unreachable."


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    topic = (parameters.get("topic") or "").strip()

    if act == "convene":
        if not topic:
            reply = "Hari, give the War-Room Council a topic or decision to debate."
        else:
            key = _get_key()
            if not key:
                reply = "Hari, Gemini API key missing for War-Room Council."
            else:
                prompt = (
                    f"Convene the J.A.R.V.I.S. 3-Agent War-Room Council for Bhogapati Hari Krishna on: '{topic}'.\n"
                    "Respond strictly in 3 sharp sections:\n"
                    "[1. STRATEGIST]: Optimal blueprint & immediate win.\n"
                    "[2. RED-TEAM AUDITOR]: Hidden risks, edge cases, or failure traps.\n"
                    "[3. EXECUTION COMMANDER]: Final decisive verdict & exact next 3 steps."
                )
                verdict = _call_gemini(prompt, key)
                reply = f"Hari, War-Room Council Verdict:\n{verdict}"
    else:
        reply = "Hari, Multi-Agent War-Room Council ONLINE (Strategist + Red-Team Auditor + Execution Commander ready)."

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
