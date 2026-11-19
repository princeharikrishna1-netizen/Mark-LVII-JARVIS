"""
JARVIS Plugin: Ghost Mode — Zero-Click Background Workflow Recorder & Replayer
Records user mouse clicks and keyboard actions in the background, saves them as
named workflows, and replays them automatically on command.
"""
from __future__ import annotations

import json
import time
import threading
from pathlib import Path
import pyautogui
from pynput import mouse, keyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.15

WORKFLOW_FILE = Path("memory/ghost_workflows.json")

PLUGIN = {
    "name": "ghost_mode",
    "description": (
        "Ghost Mode workflow recorder and replayer. Use when the user says: "
        "'start ghost mode', 'learn this task [name]', 'record workflow [name]', "
        "'stop ghost mode', 'stop learning', 'run ghost mode [name]', or 'replay workflow [name]'."
    ),
    "tier": "core",
    "brief": "Record and replay mouse/keyboard workflows hands-free.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'start', 'stop', 'run', or 'list'"
            },
            "workflow_name": {
                "type": "STRING",
                "description": "Name of the workflow to record or replay (e.g., 'system_login', 'daily_report')"
            }
        },
        "required": ["action"],
    },
}


class GhostRecorder:
    def __init__(self):
        self.recording = False
        self.current_name = ""
        self.events = []
        self.last_time = 0.0
        self.m_listener = None
        self.k_listener = None

    def start(self, name: str) -> str:
        if self.recording:
            return f"Sir, Ghost Mode is already recording '{self.current_name}'. Say 'stop ghost mode' first."
        self.current_name = name.strip().lower().replace(" ", "_") or "custom_task"
        self.events = []
        self.last_time = time.time()
        self.recording = True

        self.m_listener = mouse.Listener(on_click=self._on_click)
        self.k_listener = keyboard.Listener(on_press=self._on_key)
        self.m_listener.start()
        self.k_listener.start()
        return f"Ghost Mode active, Sir. Recording '{self.current_name}'. Perform your steps and tell me when to stop."

    def _delay(self) -> float:
        now = time.time()
        dt = min(round(now - self.last_time, 2), 4.0)
        self.last_time = now
        return dt

    def _on_click(self, x, y, button, pressed):
        if not self.recording or not pressed:
            return
        btn = "right" if button == mouse.Button.right else "left"
        self.events.append({"type": "click", "x": int(x), "y": int(y), "button": btn, "wait": self._delay()})

    def _on_key(self, key):
        if not self.recording:
            return
        try:
            k_val = key.char
            if k_val:
                self.events.append({"type": "char", "val": k_val, "wait": self._delay()})
        except AttributeError:
            special = str(key).replace("Key.", "")
            if special in ("enter", "tab", "backspace", "esc", "space", "up", "down", "left", "right"):
                self.events.append({"type": "key", "val": special, "wait": self._delay()})

    def stop(self) -> str:
        if not self.recording:
            return "Sir, Ghost Mode is not currently recording."
        self.recording = False
        if self.m_listener:
            self.m_listener.stop()
        if self.k_listener:
            self.k_listener.stop()

        trimmed = self.events[:-15] if len(self.events) > 18 else self.events

        WORKFLOW_FILE.parent.mkdir(parents=True, exist_ok=True)
        db = {}
        if WORKFLOW_FILE.exists():
            try:
                db = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
            except Exception:
                db = {}

        db[self.current_name] = trimmed
        WORKFLOW_FILE.write_text(json.dumps(db, indent=2), encoding="utf-8")
        return f"Ghost Mode stopped. Learned '{self.current_name}' with {len(trimmed)} steps, Sir."

    def replay(self, name: str) -> str:
        if self.recording:
            return "Sir, stop the active Ghost Mode recording before running a workflow."
        if not WORKFLOW_FILE.exists():
            return "Sir, no Ghost Mode workflows have been recorded yet."

        db = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
        key_name = name.strip().lower().replace(" ", "_")
        if key_name not in db:
            avail = ", ".join(db.keys()) if db else "none"
            return f"Sir, I couldn't find workflow '{key_name}'. Available workflows: {avail}."

        steps = db[key_name]

        def _worker():
            time.sleep(1.0)
            for ev in steps:
                time.sleep(ev.get("wait", 0.2))
                t = ev.get("type")
                if t == "click":
                    pyautogui.click(ev["x"], ev["y"], button=ev.get("button", "left"))
                elif t == "char":
                    pyautogui.write(ev["val"])
                elif t == "key":
                    pyautogui.press(ev["val"])

        threading.Thread(target=_worker, daemon=True).start()
        return f"Executing Ghost Mode workflow '{key_name}' ({len(steps)} steps) now, Sir."

    def list_workflows(self) -> str:
        if not WORKFLOW_FILE.exists():
            return "Sir, no Ghost Mode workflows saved yet."
        db = json.loads(WORKFLOW_FILE.read_text(encoding="utf-8"))
        if not db:
            return "Sir, your Ghost Mode memory is empty."
        return "Saved Ghost Mode workflows: " + ", ".join(f"{k} ({len(v)} steps)" for k, v in db.items())


_GHOST = GhostRecorder()


def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "").strip().lower()
    wf_name = (parameters.get("workflow_name") or "default_task").strip()

    try:
        if act in ("start", "record", "learn"):
            reply = _GHOST.start(wf_name)
        elif act in ("stop", "save", "finish"):
            reply = _GHOST.stop()
        elif act in ("run", "replay", "play", "execute"):
            reply = _GHOST.replay(wf_name)
        elif act in ("list", "show"):
            reply = _GHOST.list_workflows()
        else:
            reply = "Sir, please specify whether to start, stop, run, or list Ghost Mode workflows."
    except Exception as e:
        reply = f"Sir, Ghost Mode error: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply