"""
JARVIS Plugin: AI Screen Vision & Multimodal Analyzer v2 (Level 6 Supreme - 29/29)
Gives Mark-LVII true visual perception across Windows 11 PC and Android Mobile:
- pc_capture & mobile_capture: Live screen capture to dashboard/static/
- analyze_pc & analyze_mobile: Sends live screen image to Google Gemini Multimodal Vision API
  to diagnose errors, read forms/documents, and summarize on-screen context for Hari.
- pc_windows & inspect_mobile_ui: Fast structural UI/window inspection.
"""
from __future__ import annotations
import base64
import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

PC_SCREEN = Path("dashboard/static/pc_screen.png")
MOB_SCREEN = Path("dashboard/static/mobile_screen.png")
API_KEYS_FILE = Path("config/api_keys.json")

PLUGIN = {
    "name": "screen_vision",
    "description": (
        "AI Screen Vision & Multimodal Analyzer v2. Captures and visually analyzes PC or Android mobile screens "
        "using Gemini Vision AI to diagnose errors, read documents/forms, and explain what is on screen. "
        "Trigger on 'analyze screen', 'check my screen', 'what is on my screen', 'read error on screen', or 'screen vision'."
    ),
    "tier": "core",
    "brief": "Capture & visually analyze PC or Android screens using Gemini Multimodal Vision AI.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "One of: 'analyze_pc', 'analyze_mobile', 'pc_capture', 'mobile_capture', "
                    "'pc_windows', 'inspect_mobile_ui', or 'status'"
                )
            },
            "question": {
                "type": "STRING",
                "description": "Optional specific question about what is visible on the screen."
            }
        },
        "required": ["action"],
    },
}


def _get_gemini_key() -> str:
    env_k = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_k:
        return env_k
    if API_KEYS_FILE.exists():
        try:
            data = json.loads(API_KEYS_FILE.read_text(encoding="utf-8"))
            for k in ("gemini_api_key", "GEMINI_API_KEY", "api_key", "google_api_key"):
                if isinstance(data.get(k), str) and data[k].strip():
                    return data[k].strip()
        except Exception:
            pass
    return ""


def _vision_analyze_image(img_path: Path, prompt_text: str) -> str:
    if not img_path.exists():
        return f"Hari, screenshot file not found at {img_path}."
    api_key = _get_gemini_key()
    if not api_key:
        return "Hari, Gemini API key not found in config/api_keys.json or environment."

    # Resize & compress to lightweight JPEG (~45KB) via PowerShell System.Drawing for 7x faster upload
    tmp_jpg = img_path.with_suffix(".tmp.jpg")
    mime_type = "image/png"
    img_bytes = img_path.read_bytes()
    try:
        src_abs = str(img_path.resolve()).replace("'", "''")
        dst_abs = str(tmp_jpg.resolve()).replace("'", "''")
        ps_zip = (
            "Add-Type -AssemblyName System.Drawing; "
            f"$img = [System.Drawing.Image]::FromFile('{src_abs}'); "
            "$w = 960; $h = [int]($img.Height * (960.0 / $img.Width)); "
            "$bmp = New-Object System.Drawing.Bitmap($w, $h); "
            "$g = [System.Drawing.Graphics]::FromImage($bmp); "
            "$g.DrawImage($img, 0, 0, $w, $h); "
            f"$bmp.Save('{dst_abs}', [System.Drawing.Imaging.ImageFormat]::Jpeg); "
            "$g.Dispose(); $bmp.Dispose(); $img.Dispose()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_zip], capture_output=True, timeout=8)
        if tmp_jpg.exists():
            img_bytes = tmp_jpg.read_bytes()
            mime_type = "image/jpeg"
            tmp_jpg.unlink(missing_ok=True)
    except Exception:
        pass

    b64_img = base64.b64encode(img_bytes).decode("ascii")
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt_text},
                {"inline_data": {"mime_type": mime_type, "data": b64_img}}
            ]
        }]
    }

    models = []
    try:
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        with urllib.request.urlopen(list_url, timeout=10) as r:
            mdata = json.loads(r.read().decode("utf-8"))
            for m in mdata.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    mname = m.get("name", "").replace("models/", "")
                    if "flash" in mname and "lite" not in mname and "tts" not in mname and "image" not in mname:
                        models.append(mname)
    except Exception:
        pass
    for fallback in ("gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"):
        if fallback not in models:
            models.append(fallback)

    last_err = ""
    for model in models[:4]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                cands = res.get("candidates") or []
                if cands:
                    parts = cands[0].get("content", {}).get("parts") or []
                    txt = "".join(p.get("text", "") for p in parts).strip()
                    if txt:
                        return f"Hari, AI Vision Analysis ({model}): {txt}"
        except BaseException as e:
            if isinstance(e, KeyboardInterrupt):
                raise
            last_err = str(e)
            continue
    return f"Hari, Gemini Vision call could not complete ({last_err}). Screenshot saved at {img_path}."


def _capture_pc_screen() -> tuple[bool, str]:
    PC_SCREEN.parent.mkdir(parents=True, exist_ok=True)
    out_abs = str(PC_SCREEN.resolve()).replace("'", "''")
    ps_cmd = (
        "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
        "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height); "
        "$g = [System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); "
        f"$bmp.Save('{out_abs}', [System.Drawing.Imaging.ImageFormat]::Png); "
        "$g.Dispose(); $bmp.Dispose(); "
        "Write-Output \"$($b.Width)x$($b.Height)\""
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True, text=True, timeout=15
    )
    if proc.returncode == 0 and PC_SCREEN.exists():
        return True, proc.stdout.strip()
    return False, (proc.stderr or proc.stdout or "capture failed").strip()


def _inspect_pc_windows() -> str:
    ps_cmd = (
        "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | "
        "Select-Object -First 8 ProcessName, MainWindowTitle | "
        "ForEach-Object { \"$($_.ProcessName): $($_.MainWindowTitle)\" }"
    )
    proc = subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps_cmd],
        capture_output=True, text=True, timeout=10
    )
    lines = [l.strip() for l in proc.stdout.splitlines() if l.strip()]
    if not lines:
        return "Hari, no visible desktop windows detected right now."
    return "Hari, Active PC Windows: " + " | ".join(lines)


def _inspect_android_ui() -> str:
    import plugins.mobile_bridge as mb
    if not mb._find_adb():
        return "Hari, ADB not available for mobile UI inspection."
    devs = mb._connected_devices()
    if not devs:
        return "Hari, no Android mobile connected for UI inspection."
    dev = devs[0]
    remote_xml = "/sdcard/jarvis_ui.xml"
    local_xml = Path("memory/last_mobile_ui.xml")
    local_xml.parent.mkdir(parents=True, exist_ok=True)
    mb._adb(["-s", dev, "shell", "uiautomator", "dump", remote_xml], timeout=12)
    ok, err = mb._adb(["-s", dev, "pull", remote_xml, str(local_xml)], timeout=10)
    mb._adb(["-s", dev, "shell", "rm", "-f", remote_xml], timeout=6)
    if not ok or not local_xml.exists():
        return f"Hari, could not read mobile UI hierarchy: {err}"
    try:
        tree = ET.parse(local_xml)
        texts: list[str] = []
        for node in tree.iter("node"):
            t = (node.attrib.get("text") or "").strip()
            cd = (node.attrib.get("content-desc") or "").strip()
            val = t or cd
            if val and val not in texts:
                texts.append(val)
            if len(texts) >= 15:
                break
        return (
            "Hari, Live Android Screen Text: " + " | ".join(texts)
            if texts else "Hari, mobile UI dumped, no readable text elements found."
        )
    except Exception as e:
        return f"Hari, XML parse error: {e}"


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    question = (parameters.get("question") or "").strip()

    try:
        if act == "pc_capture":
            ok, info = _capture_pc_screen()
            reply = (
                f"Hari, PC Desktop Screenshot captured ({info}) -> http://10.90.58.117:8000/static/pc_screen.png"
                if ok else f"Hari, PC screenshot failed: {info}"
            )
        elif act == "analyze_pc":
            ok, info = _capture_pc_screen()
            if not ok:
                reply = f"Hari, PC capture failed before vision analysis: {info}"
            else:
                q = question or "You are JARVIS speaking to Hari. Concisely describe what is open on this Windows 11 PC screen, highlight any errors, forms, or key details, and suggest the next helpful action in 3-4 lines."
                reply = _vision_analyze_image(PC_SCREEN, q)

        elif act == "analyze_mobile":
            import plugins.mobile_bridge as mb
            cap_res = mb.run({"action": "screenshot"})
            if not MOB_SCREEN.exists():
                reply = cap_res
            else:
                q = question or "You are JARVIS speaking to Hari. Concisely summarize what is currently shown on this Android mobile screen (app, messages, notifications, or errors) in 3 lines."
                reply = _vision_analyze_image(MOB_SCREEN, q)

        elif act == "pc_windows":
            reply = _inspect_pc_windows()
        elif act == "mobile_capture":
            import plugins.mobile_bridge as mb
            reply = mb.run({"action": "screenshot"})
        elif act == "inspect_mobile_ui":
            reply = _inspect_android_ui()
        else:
            has_key = bool(_get_gemini_key())
            reply = (
                f"Hari, AI Screen Vision v2 ONLINE (Gemini Multimodal Vision: {'READY' if has_key else 'NO API KEY'} | "
                "PC & Android live capture + visual error/form analysis active)."
            )
    except Exception as e:
        reply = f"Hari, Screen Vision error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
