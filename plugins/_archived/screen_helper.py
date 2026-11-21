"""
JARVIS Plugin: Visual Screen Helper & Error Solver
Captures the active monitor (masking JARVIS's own HUD) and uses Gemini Vision
to explain errors, guide form filling, or summarize what is on screen.
"""
from __future__ import annotations

import io
from google.genai import types
from core import gemini, screenview

PLUGIN = {
    "name": "analyze_screen_visually",
    "description": (
        "Takes a screenshot of the user's active screen and visually analyzes it to solve errors, "
        "explain what is displayed, or help fill out forms/webpages. Use whenever the user asks "
        "'what is on my screen', 'help me with this error', 'read my screen', or 'screen chusi help cheyi'."
    ),
    "tier": "core",
    "brief": "Capture and visually analyze the screen to solve errors or explain content.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "question": {
                "type": "STRING",
                "description": "What the user wants to know or fix on the screen."
            }
        },
        "required": [],
    },
}


def run(parameters: dict, player=None, session_memory=None) -> str:
    question = (parameters.get("question") or "").strip()
    if player:
        try:
            player.write_log("JARVIS: Capturing screen for visual analysis...")
        except Exception:
            pass

    try:
        import PIL.ImageDraw

        view = screenview.look()
        mon = screenview.monitor_rect(view)
        image, mon_rect, px = screenview.capture(mon)

        # Mask JARVIS's own HUD window so Gemini focuses only on the user's work
        draw = PIL.ImageDraw.Draw(image)
        for left, top, w, h in screenview.own_window_rects():
            x1 = int((left - mon_rect["left"]) * px)
            y1 = int((top - mon_rect["top"]) * px)
            x2 = int(x1 + w * px)
            y2 = int(y1 + h * px)
            draw.rectangle([x1, y1, x2, y2], fill=(10, 14, 20))

        # Resize slightly if ultra-high-res to keep latency fast
        max_dim = 1600
        if max(image.width, image.height) > max_dim:
            ratio = max_dim / float(max(image.width, image.height))
            image = image.resize((int(image.width * ratio), int(image.height * ratio)))

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        img_part = types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg")

        user_ask = question if question else "Explain what is currently on the screen and highlight any errors or next steps."
        prompt = (
            f"Active window: {view.app} — {view.title}\n"
            f"User request: {user_ask}\n\n"
            "Analyze the screenshot clearly and concisely in 2-4 sentences. "
            "If there is an error message, give the exact fix. "
            "Reply in the same language/style the user asked in (English or Telugu/Tenglish)."
        )

        resp = gemini.call(
            contents=[img_part, prompt],
            tier=gemini.SMART,
            timeout_ms=45_000,
        )
        answer = (resp.text or "").strip()
        if not answer:
            return "Sir, I captured the screen, but could not extract a clear answer."

        if player:
            try:
                player.show_content(f"SCREEN VISION — {view.app or 'DESKTOP'}", answer)
            except Exception:
                pass
        return answer

    except Exception as e:
        return f"Sir, visual screen analysis failed: {e}"