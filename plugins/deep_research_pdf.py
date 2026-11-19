"""
JARVIS Plugin: Autonomous Deep Web Researcher & Legal-Size Report Generator (Level 6 Supreme - 37/40)
Researches any topic using Gemini and outputs a clean Legal-size formatted report
ready for viewing or direct HP LaserJet 1020 Plus printing:
- research: Queries Gemini for structured multi-point analysis and saves a Legal-size formatted report
- list: Lists generated research reports in memory/research_reports/
"""
from __future__ import annotations
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path("memory/research_reports")
API_KEYS_FILE = Path("config/api_keys.json")

PLUGIN = {
    "name": "deep_research_pdf",
    "description": (
        "Autonomous Deep Web Researcher & Legal-Size Report Generator. Researches topics via Gemini AI "
        "and generates clean Legal-size formatted reports ready for HP LaserJet 1020 Plus printing. "
        "Trigger on 'deep research', 'research report', 'generate report', or 'study topic'."
    ),
    "tier": "core",
    "brief": "AI deep research & Legal-size printable report generator.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'research', 'list', or 'status'"
            },
            "topic": {
                "type": "STRING",
                "description": "Topic or question to research in depth."
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



def _gemini_text_generate(prompt: str, key: str) -> str:
    import json, urllib.request
    models = ["gemini-3-flash-preview", "gemini-2.5-flash", "gemini-2.0-flash"]
    try:
        with urllib.request.urlopen(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}", timeout=10) as r:
            listed = [
                m["name"].replace("models/", "")
                for m in json.loads(r.read().decode("utf-8")).get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", []) and "flash" in m.get("name", "")
            ]
            if listed:
                models = listed + [m for m in models if m not in listed]
    except Exception:
        pass
    last_err = None
    for mdl in models[:4]:
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={key}"
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last_err = e
    raise RuntimeError(f"All Gemini models failed: {last_err}")


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    topic = (parameters.get("topic") or "").strip()

    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        if act == "research":
            if not topic:
                reply = "Hari, provide a topic to research."
            else:
                key = _get_key()
                if not key:
                    reply = "Hari, Gemini API key missing for Deep Research."
                else:
                    prompt = (
                        f"You are J.A.R.V.I.S. preparing an executive Legal-size research brief for Bhogapati Hari Krishna on: '{topic}'. "
                        "Provide: 1) Executive Summary, 2) Key Facts & Comparison Table, 3) Actionable Recommendations. Keep formatting crisp plain text."
                    )
                    body = _gemini_text_generate(prompt, key)
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    safe_name = "".join(c if c.isalnum() else "_" for c in topic[:28]).strip("_")
                    out_file = REPORTS_DIR / f"Report_{safe_name}_{ts}.txt"
                    header = (
                        "========================================================================\n"
                        f"  J.A.R.V.I.S. LEGAL-SIZE RESEARCH DOSSIER  |  {datetime.now().strftime('%d-%b-%Y %I:%M %p')}\n"
                        f"  Subject: {topic}\n"
                        "========================================================================\n\n"
                    )
                    out_file.write_text(header + body + "\n", encoding="utf-8")
                    preview = body[:180].replace("\n", " ") + "..."
                    reply = f"Hari, Deep Research Report saved ({out_file.name}): {preview}"
        else:
            files = sorted(REPORTS_DIR.glob("*.txt"), key=lambda p: p.stat().st_mtime, reverse=True)
            reply = f"Hari, Deep Researcher ONLINE ({len(files)} reports saved): " + (", ".join(f.name for f in files[:4]) if files else "none yet")
    except Exception as e:
        reply = f"Hari, Deep Research error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
