"""
JARVIS Plugin: Live Screen Co-Pilot & Gamer Tactical HUD
Captures active monitor via core.screenview, identifies target UI elements/buttons,
and draws a live click-through Holographic Cyan/Red Target Ring directly on screen.
"""
from __future__ import annotations

import io
import json
import PIL.ImageDraw
from google.genai import types
from core import gemini, screenview
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPen, QColor, QFont

PLUGIN = {
    "name": "screen_copilot",
    "description": (
        "Live Screen Co-Pilot & Tactical HUD Overlay. Visually locates exact buttons, icons, "
        "fields, or game targets on the screen and draws a glowing holographic target ring over them. "
        "Use ONLY when the user asks 'where should I click', 'point to', 'show me where', "
        "'highlight the button', or 'guide me step by step on screen'. "
        "For general screen reading or error explanations without pointing, use analyze_screen_visually instead."
    ),
    "tier": "core",
    "brief": "Draw a live holographic target ring on screen to show where to click or look.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "question": {
                "type": "STRING",
                "description": "What button, element, or area the user wants located or guided on screen."
            }
        },
        "required": ["question"],
    },
}


class TacticalOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.target_x = None
        self.target_y = None
        self.label_text = ""
        self.pulse_radius = 25
        self.growing = True

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate)

    def show_target(self, mon_rect: dict, norm_x: int, norm_y: int, label: str, duration_ms: int = 8000):
        # యాక్టివ్ మానిటర్ geometry కి మ్యాప్ చేయడం (Multi-monitor safe)
        self.setGeometry(mon_rect["left"], mon_rect["top"], mon_rect["width"], mon_rect["height"])
        self.target_x = int((norm_x / 1000.0) * mon_rect["width"])
        self.target_y = int((norm_y / 1000.0) * mon_rect["height"])
        self.label_text = label
        self.show()
        self.anim_timer.start(35)
        QTimer.singleShot(duration_ms, self.clear_target)

    def clear_target(self):
        self.anim_timer.stop()
        self.target_x = None
        self.hide()

    def _animate(self):
        if self.growing:
            self.pulse_radius += 1
            if self.pulse_radius >= 42:
                self.growing = False
        else:
            self.pulse_radius -= 1
            if self.pulse_radius <= 22:
                self.growing = True
        self.update()

    def paintEvent(self, event):
        if self.target_x is None or self.target_y is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Outer Pulsing Cyan Ring
        cyan = QColor(0, 240, 255, 235)
        painter.setPen(QPen(cyan, 3))
        painter.drawEllipse(
            self.target_x - self.pulse_radius,
            self.target_y - self.pulse_radius,
            self.pulse_radius * 2,
            self.pulse_radius * 2
        )

        # Inner Red Tactical Crosshair
        red = QColor(255, 55, 55, 245)
        painter.setPen(QPen(red, 2))
        painter.drawLine(self.target_x - 14, self.target_y, self.target_x + 14, self.target_y)
        painter.drawLine(self.target_x, self.target_y - 14, self.target_x, self.target_y + 14)

        # HUD Label Tag
        if self.label_text:
            painter.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
            painter.setPen(cyan)
            painter.drawText(self.target_x + 48, self.target_y + 5, f"[TARGET: {self.label_text}]")


_OVERLAY = None


def _trigger_hud(mon_rect: dict, x: int, y: int, label: str):
    global _OVERLAY
    app = QApplication.instance()
    if not app:
        return
    if _OVERLAY is None:
        _OVERLAY = TacticalOverlay()
    _OVERLAY.show_target(mon_rect, x, y, label)


def run(parameters: dict, player=None, session_memory=None) -> str:
    question = (parameters.get("question") or "").strip() or "Locate the main action button on screen."
    try:
        view = screenview.look()
        mon = screenview.monitor_rect(view)
        image, mon_rect, px = screenview.capture(mon)

        # JARVIS HUD ని మాస్క్ చేయడం
        draw = PIL.ImageDraw.Draw(image)
        for left, top, w, h in screenview.own_window_rects():
            x1 = int((left - mon_rect["left"]) * px)
            y1 = int((top - mon_rect["top"]) * px)
            x2 = int(x1 + w * px)
            y2 = int(y1 + h * px)
            draw.rectangle([x1, y1, x2, y2], fill=(10, 14, 20))

        max_dim = 1400
        if max(image.width, image.height) > max_dim:
            ratio = max_dim / float(max(image.width, image.height))
            image = image.resize((int(image.width * ratio), int(image.height * ratio)))

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        img_part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

        prompt = (
            f"Active window: {view.app} — {view.title}\n"
            f"User request: {question}\n\n"
            "You are JARVIS Live Screen Co-Pilot. Find the exact UI element, button, or target area "
            "the user needs to click or look at. Provide normalized coordinates on a 0 to 1000 scale "
            "(0,0 = top-left, 1000,1000 = bottom-right).\n"
            "Respond ONLY with valid JSON:\n"
            '{"voice_reply": "Short helpful reply in English or Telugu/Tenglish matching user query", '
            '"has_target": true, "x": 500, "y": 300, "label": "SHORT TAG"}'
        )

        resp = gemini.call(
            contents=[img_part, prompt],
            tier=gemini.SMART,
            timeout_ms=30_000,
        )
        raw = (resp.text or "").strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)

        reply = data.get("voice_reply", "Target locked on your screen, Sir.")
        if data.get("has_target") and QApplication.instance():
            x = max(0, min(1000, int(data.get("x", 500))))
            y = max(0, min(1000, int(data.get("y", 500))))
            label = str(data.get("label", "TARGET"))
            QTimer.singleShot(0, lambda: _trigger_hud(mon_rect, x, y, label))

    except Exception as e:
        reply = f"Sir, screen co-pilot failed: {e}"

    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply