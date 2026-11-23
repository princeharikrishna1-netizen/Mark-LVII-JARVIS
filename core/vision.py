import io
import mss
from PIL import Image
import pygetwindow as gw
import pyperclip


class ScreenVision:
    def __init__(self, max_width: int = 1280, quality: int = 75):
        self.max_width = max_width
        self.quality = quality

    def get_active_window_title(self) -> str:
        try:
            win = gw.getActiveWindow()
            return win.title.strip() if win and win.title else "Unknown Window"
        except Exception:
            return "Unknown Window"

    def get_clipboard_text(self, max_chars: int = 1500) -> str:
        try:
            text = pyperclip.paste()
            if text and isinstance(text, str):
                return text.strip()[:max_chars]
        except Exception:
            pass
        return ""

    def capture_screen_bytes(self, monitor_index: int = 1) -> bytes:
        """Captures primary monitor and returns compressed JPEG bytes."""
        with mss.mss() as sct:
            monitors = sct.monitors
            target = monitors[monitor_index] if monitor_index < len(monitors) else monitors[0]
            raw = sct.grab(target)
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

            if img.width > self.max_width:
                ratio = self.max_width / float(img.width)
                new_height = int(float(img.height) * ratio)
                img = img.resize((self.max_width, new_height), Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=self.quality, optimize=True)
            return buf.getvalue()

    def build_visual_context(self, include_clipboard: bool = True) -> dict:
        """Returns image bytes along with active app & clipboard metadata."""
        img_bytes = self.capture_screen_bytes()
        window_title = self.get_active_window_title()
        clipboard = self.get_clipboard_text() if include_clipboard else ""

        context_note = f"[Active Window: {window_title}]"
        if clipboard:
            context_note += f"\n[Clipboard Snippet]:\n{clipboard}"

        return {
            "image_bytes": img_bytes,
            "mime_type": "image/jpeg",
            "window_title": window_title,
            "clipboard": clipboard,
            "context_note": context_note,
        }
