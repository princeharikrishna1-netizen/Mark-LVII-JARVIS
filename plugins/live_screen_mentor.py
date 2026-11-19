"""
JARVIS Plugin: Universal Live Screen Observer & Correction Mentor (Level 11 Omniscience - 57/60)
Observes ANY website, web portal, spreadsheet, PDF, or desktop app on Hari's Windows 11 screen
using Gemini Multimodal Vision, spots mistakes/missing fields, and gives voice/HUD corrections.
"""
from __future__ import annotations
import base64, json, os, subprocess, urllib.request
from pathlib import Path

API_KEYS_FILE = Path("config/api_keys.json")
TMP_SHOT = Path("memory/live_mentor_screen.jpg")

PLUGIN = {
    "name": "live_screen_mentor",
    "description": "Universal Live Screen Observer & Correction Mentor for ANY website or app.",
    "tier": "core",
    "brief": "AI Screen Observer that spots mistakes & suggests real-time corrections on any site/app.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'observe', or 'status'"},
            "focus": {"type": "STRING", "description": "Optional area or website focus."},
            "speak_alert": {"type": "BOOLEAN", "description": "Speak short voice alert if true."}
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

def _capture_screen() -> Path:
    TMP_SHOT.parent.mkdir(parents=True, exist_ok=True)
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); "
        "$g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen(0,0,0,0,$b.Size); "
        f"$bmp.Save('{TMP_SHOT.resolve()}', [System.Drawing.Imaging.ImageFormat]::Jpeg); $g.Dispose(); $bmp.Dispose();"
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=8)
    return TMP_SHOT

def _vision_analyze(img_path: Path, prompt: str, key: str) -> str:
    b64 = base64.b64encode(img_path.read_bytes()).decode("utf-8")
    models = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.0-flash"]
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
            payload = {"contents": [{"parts": [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": b64}}]}]}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mdl}:generateContent?key={key}"
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            continue
    return "Vision endpoint temporarily unreachable."

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "observe").strip().lower()
    focus = (parameters.get("focus") or "").strip()
    if act == "observe":
        key = _get_key()
        if not key:
            reply = "Hari, Gemini API key missing in config/api_keys.json for Live Screen Mentor."
        else:
            shot = _capture_screen()
            prompt = (
                "You are J.A.R.V.I.S. observing Bhogapati Hari Krishna's Windows 11 screen live. "
                f"Focus context: '{focus or 'ANY website, web portal, spreadsheet, PDF, form, or desktop application currently visible'}'. "
                "Respond concisely in 3 bullet points:\n"
                "1) CURRENT SCREEN CONTEXT: What Hari is actively working on.\n"
                "2) CORRECTIONS / ERRORS SPOTTED: Any typos, blank required fields, invalid formats, or bugs visible (or 'No errors spotted').\n"
                "3) SMART NEXT SUGGESTION: The fastest next action or data entry step."
            )
            analysis = _vision_analyze(shot, prompt, key)
            reply = f"Hari, Live Screen Mentor Report:\n{analysis}"
            if parameters.get("speak_alert"):
                try:
                    import plugins.sovereign_voice_synth as _svs
                    short_voice = analysis.splitlines()[0][:180]
                    _svs.run({"action": "speak", "text": f"Hari, screen observation: {short_voice}"})
                except Exception:
                    pass
    else:
        reply = "Hari, Universal Live Screen Observer & Correction Mentor ONLINE (Ready for any website or app)."
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
