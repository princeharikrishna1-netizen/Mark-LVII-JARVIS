"""
JARVIS Plugin: Android Mobile Control Bridge v2 (Pro Level 5+)
Operates Hari's Android mobile from PC via USB or Wireless Wi-Fi ADB:
- Call by phone number OR Contact Name lookup on device
- Live mobile screenshot capture to dashboard/static/mobile_screen.png
- Launch apps, tap/swipe screen, type text, press media/volume/home keys, read battery & notifications
"""
from __future__ import annotations
import json
import re
import shutil
import subprocess
from pathlib import Path

CFG_FILE = Path("memory/mobile_bridge_config.json")
SCREEN_OUT = Path("dashboard/static/mobile_screen.png")

APP_PACKAGES = {
    "youtube": "com.google.android.youtube",
    "whatsapp": "com.whatsapp",
    "chrome": "com.android.chrome",
    "camera": "com.android.camera",
    "settings": "com.android.settings",
    "spotify": "com.spotify.music",
    "bgmi": "com.pubg.imobile",
    "instagram": "com.instagram.android",
    "maps": "com.google.android.apps.maps",
    "phone": "com.google.android.dialer",
    "messages": "com.google.android.apps.messaging",
}

KEYCODES = {
    "home": "3",
    "back": "4",
    "call": "5",
    "end_call": "6",
    "volume_up": "24",
    "volume_down": "25",
    "power": "26",
    "camera": "27",
    "enter": "66",
    "play_pause": "85",
    "next": "87",
    "previous": "88",
    "mute": "164",
    "wake": "224",
}

PLUGIN = {
    "name": "mobile_bridge",
    "description": (
        "Android Mobile Control Bridge v2 (ADB). Operates Hari's Android phone from PC: "
        "connect/pair over Wi-Fi, call by number or contact name, capture mobile screenshot, "
        "open mobile apps, tap/swipe screen, type text, press keys, and read battery or notifications. "
        "Trigger on 'phone', 'mobile', 'android', 'call on phone', 'mobile screenshot', or 'open app on mobile'."
    ),
    "tier": "core",
    "brief": "Operate Hari's Android mobile from PC (calls by name/number, screenshots, apps, screen control).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": (
                    "One of: 'status', 'connect', 'pair', 'call', 'call_name', 'screenshot', "
                    "'open_app', 'tap', 'swipe', 'type_text', 'key', 'battery', or 'notifications'"
                ),
            },
            "target": {
                "type": "STRING",
                "description": (
                    "Phone number for 'call', contact name for 'call_name', app name/package for 'open_app', "
                    "IP:PORT for 'connect'/'pair', coordinates 'x y' for 'tap', text for 'type_text', or key name."
                ),
            },
            "pair_code": {
                "type": "STRING",
                "description": "6-digit Wireless Debugging pairing code when action is 'pair'."
            }
        },
        "required": ["action"],
    },
}


def _find_adb() -> str | None:
    found = shutil.which("adb")
    if found:
        return found
    for c in [
        Path.home() / "AppData/Local/Android/Sdk/platform-tools/adb.exe",
        Path("C:/platform-tools/adb.exe"),
        Path("C:/adb/adb.exe"),
    ]:
        if c.exists():
            return str(c)
    return None


def _adb(args: list[str], timeout: int = 12) -> tuple[bool, str]:
    adb_bin = _find_adb()
    if not adb_bin:
        return False, "ADB (platform-tools) not installed on PC."
    try:
        proc = subprocess.run(
            [adb_bin] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        out = (proc.stdout or proc.stderr or "").strip()
        return proc.returncode == 0, out
    except Exception as e:
        return False, str(e)


def _save_cfg(data: dict) -> None:
    CFG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CFG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _load_cfg() -> dict:
    if not CFG_FILE.exists():
        return {}
    try:
        return json.loads(CFG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _connected_devices() -> list[str]:
    ok, out = _adb(["devices"])
    if not ok:
        return []
    devs = []
    for line in out.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devs.append(parts[0])
    return devs


def _lookup_contact_number(dev: str, name_query: str) -> tuple[str | None, str | None]:
    safe_q = re.sub(r"[^a-zA-Z0-9 _-]", "", name_query).strip()
    if not safe_q:
        return None, None
    ok, out = _adb([
        "-s", dev, "shell", "content", "query",
        "--uri", "content://com.android.contacts/data/phones",
        "--projection", "display_name:data1",
        "--where", f"display_name LIKE '%{safe_q}%'"
    ], timeout=12)
    if not ok or "Row:" not in out:
        return None, None
    m_name = re.search(r"display_name=([^,]+)", out)
    m_num = re.search(r"data1=([^\r\n]+)", out)
    if m_num:
        num = re.sub(r"[^0-9+*#]", "", m_num.group(1))
        cname = m_name.group(1).strip() if m_name else safe_q
        return cname, num
    return None, None


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "status").strip().lower()
    target = (parameters.get("target") or "").strip()
    pair_code = (parameters.get("pair_code") or "").strip()

    try:
        if act == "pair":
            if not target or not pair_code:
                reply = "Hari, provide Android Wireless Debugging IP:PORT as target and 6-digit pair_code."
            else:
                ok, out = _adb(["pair", target, pair_code], timeout=15)
                reply = f"Hari, Android Wireless Pair {'SUCCESS' if ok else 'FAILED'}: {out}"

        elif act == "connect":
            endpoint = target or _load_cfg().get("last_endpoint", "")
            if not endpoint:
                reply = "Hari, provide your Android phone's Wireless Debugging IP:PORT."
            else:
                ok, out = _adb(["connect", endpoint], timeout=12)
                if ok and "connected" in out.lower():
                    _save_cfg({"last_endpoint": endpoint})
                reply = f"Hari, Android Bridge Connect: {out}"

        elif act == "status":
            adb_bin = _find_adb()
            if not adb_bin:
                reply = "Hari, ADB platform-tools not found on PC."
            else:
                devs = _connected_devices()
                if not devs:
                    last_ep = _load_cfg().get("last_endpoint", "none")
                    reply = f"Hari, ADB ready, 0 Android devices attached right now (Last saved IP: {last_ep})."
                else:
                    _, model = _adb(["-s", devs[0], "shell", "getprop", "ro.product.model"])
                    _, bat = _adb(["-s", devs[0], "shell", "dumpsys", "battery"])
                    lvl = re.search(r"level:\s*(\d+)", bat)
                    pct = f"{lvl.group(1)}%" if lvl else "unknown"
                    reply = f"Hari, Android Connected: {model or devs[0]} ({devs[0]}) | Battery: {pct}."

        else:
            devs = _connected_devices()
            if not devs:
                last_ep = _load_cfg().get("last_endpoint", "")
                if last_ep:
                    _adb(["connect", last_ep], timeout=8)
                    devs = _connected_devices()
            if not devs:
                reply = "Hari, no Android mobile connected right now. Pair/connect via USB or Wireless ADB first."
            else:
                dev = devs[0]
                if act == "call":
                    if any(ch.isalpha() for ch in target):
                        cname, num = _lookup_contact_number(dev, target)
                        if not num:
                            reply = f"Hari, contact '{target}' not found on your Android phone."
                        else:
                            ok, _ = _adb(["-s", dev, "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{num}"])
                            reply = f"Hari, calling {cname} ({num}) on your Android mobile." if ok else "Hari, call failed."
                    else:
                        num = re.sub(r"[^0-9+*#]", "", target)
                        if not num:
                            reply = "Hari, specify a valid phone number or contact name."
                        else:
                            ok, out = _adb(["-s", dev, "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{num}"])
                            reply = f"Hari, dialing {num} on your Android mobile." if ok else f"Hari, call failed: {out}"

                elif act == "call_name":
                    cname, num = _lookup_contact_number(dev, target)
                    if not num:
                        reply = f"Hari, contact '{target}' not found on your Android mobile."
                    else:
                        ok, _ = _adb(["-s", dev, "shell", "am", "start", "-a", "android.intent.action.CALL", "-d", f"tel:{num}"])
                        reply = f"Hari, calling {cname} ({num}) on your Android mobile." if ok else "Hari, call failed."

                elif act == "screenshot":
                    SCREEN_OUT.parent.mkdir(parents=True, exist_ok=True)
                    remote_tmp = "/sdcard/jarvis_cap.png"
                    ok1, _ = _adb(["-s", dev, "shell", "screencap", "-p", remote_tmp], timeout=12)
                    ok2, out2 = _adb(["-s", dev, "pull", remote_tmp, str(SCREEN_OUT)], timeout=12)
                    _adb(["-s", dev, "shell", "rm", "-f", remote_tmp], timeout=6)
                    if ok1 and ok2 and SCREEN_OUT.exists():
                        reply = "Hari, Mobile Screenshot captured -> http://10.90.58.117:8000/static/mobile_screen.png"
                    else:
                        reply = f"Hari, mobile screenshot failed: {out2}"

                elif act == "open_app":
                    key = target.lower()
                    pkg = APP_PACKAGES.get(key, target)
                    if not pkg:
                        reply = "Hari, tell me which app to open on your mobile."
                    else:
                        ok, out = _adb(["-s", dev, "shell", "monkey", "-p", pkg, "-c", "android.intent.category.LAUNCHER", "1"])
                        reply = f"Hari, launched {target} ({pkg}) on your Android mobile." if ok else f"Hari, could not launch {pkg}: {out}"

                elif act == "tap":
                    coords = target.replace(",", " ").split()
                    if len(coords) < 2:
                        reply = "Hari, provide 'x y' coordinates for screen tap."
                    else:
                        ok, _ = _adb(["-s", dev, "shell", "input", "tap", coords[0], coords[1]])
                        reply = f"Hari, tapped mobile screen at ({coords[0]}, {coords[1]})." if ok else "Hari, tap failed."

                elif act == "swipe":
                    coords = target.replace(",", " ").split()
                    if len(coords) < 4:
                        reply = "Hari, provide 'x1 y1 x2 y2' coordinates for swipe."
                    else:
                        ok, _ = _adb(["-s", dev, "shell", "input", "swipe", coords[0], coords[1], coords[2], coords[3], "300"])
                        reply = f"Hari, swiped mobile screen." if ok else "Hari, swipe failed."

                elif act == "type_text":
                    escaped = target.replace(" ", "%s")
                    ok, _ = _adb(["-s", dev, "shell", "input", "text", escaped])
                    reply = "Hari, typed text onto your mobile screen." if ok else "Hari, text input failed."

                elif act == "key":
                    code = KEYCODES.get(target.lower(), target)
                    ok, _ = _adb(["-s", dev, "shell", "input", "keyevent", str(code)])
                    reply = f"Hari, sent key '{target}' to your Android mobile." if ok else "Hari, keyevent failed."

                elif act == "battery":
                    _, bat = _adb(["-s", dev, "shell", "dumpsys", "battery"])
                    lvl = re.search(r"level:\s*(\d+)", bat)
                    temp = re.search(r"temperature:\s*(\d+)", bat)
                    pct = f"{lvl.group(1)}%" if lvl else "?"
                    deg = f"{int(temp.group(1))/10:.1f}C" if temp else "?"
                    reply = f"Hari, Android Battery: {pct} | Temp: {deg}."

                elif act == "notifications":
                    _, raw = _adb(["-s", dev, "shell", "dumpsys", "notification", "--noredact"])
                    titles = re.findall(r"android\.title=String\s*\(([^)]+)\)", raw)
                    unique = list(dict.fromkeys(t.strip() for t in titles if t.strip()))[:5]
                    reply = (
                        "Hari, Recent Mobile Notifications: " + " | ".join(unique)
                        if unique else "Hari, no active notifications readable on your mobile."
                    )
                else:
                    reply = f"Hari, unknown mobile_bridge action '{act}'."
    except Exception as e:
        reply = f"Hari, Mobile Bridge error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
