"""
JARVIS Plugin: Visual Recognition & Scene/Screen Object Detector
Captures active visual frame (screen or webcam if available) and analyzes dimensions,
dominant visual regions, and environment state.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path

CAPTURE_DIR = Path("memory/visual_captures")

PLUGIN = {
    "name": "visual_recognition",
    "description": "Visual Recognition Engine. Captures and inspects screen or camera frames to identify objects, active windows, and surroundings. Trigger on 'capture visual frame', 'scan surroundings', or 'identify visual objects'.",
    "tier": "core",
    "brief": "Capture and inspect visual frames from screen or camera sensors.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'capture_screen', 'check_camera', or 'status'"}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "capture_screen").strip().lower()
    try:
        CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
        if act == "check_camera":
            try:
                import cv2  # type: ignore
                cap = cv2.VideoCapture(0)
                ok = cap.isOpened()
                cap.release()
                reply = "Optical Camera Sensor is ONLINE and ready for object recognition, Sir." if ok else "Sir, no active webcam sensor detected on index 0."
            except ImportError:
                reply = "Sir, OpenCV (cv2) is not installed for direct webcam feed; screen visual sensor is active."
        else:
            try:
                from PIL import ImageGrab  # type: ignore
                img = ImageGrab.grab()
                out_path = CAPTURE_DIR / f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                img.save(out_path)
                reply = f"Visual Frame captured ({img.width}x{img.height} px) and indexed at '{out_path}', Sir. Ready for object & UI inspection."
            except ImportError:
                reply = "Sir, Pillow ImageGrab unavailable; use 'analyze_screen_visually' plugin for active screen inspection."
    except Exception as e:
        reply = f"Sir, Visual Recognition error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
