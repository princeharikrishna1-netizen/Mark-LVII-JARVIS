"""
JARVIS Plugin: Live Screen OCR & Instant Text Radar (#72)
Captures the current Windows 11 screen, extracts visible English/Telugu text
via Tesseract OCR (or Windows native OCR fallback), copies it to clipboard,
and returns a clean text readout for summarization or form filling.
"""
from __future__ import annotations
import shutil, subprocess
from datetime import datetime
from pathlib import Path

CAPTURE_DIR = Path("memory/screen_radar")

PLUGIN = {
    "name": "vision_screen_radar",
    "description": (
        "Live Screen OCR & Text Radar. Captures the current screen and extracts readable text "
        "from open PDFs, browser pages, or images, copying the text to clipboard. Trigger on "
        "'scan my screen', 'read screen text', 'ocr screen', or 'capture screen text'."
    ),
    "tier": "core",
    "brief": "Capture screen and extract visible text via OCR.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'scan' (default) or 'copy_only'"
            },
            "lang": {
                "type": "STRING",
                "description": "Optional OCR language code, e.g. 'eng', 'tel', or 'eng+tel'."
            }
        },
        "required": [],
    },
}


def _grab_screen(out_path: Path) -> bool:
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(all_screens=False)
        img.save(out_path, "PNG")
        return True
    except Exception:
        pass
    try:
        import pyautogui
        pyautogui.screenshot(str(out_path))
        return out_path.exists()
    except Exception:
        return False


def _ocr_image(img_path: Path, lang: str = "eng") -> str:
    tess_bin = shutil.which("tesseract") or r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(tess_bin).exists():
        try:
            res = subprocess.run(
                [str(tess_bin), str(img_path), "stdout", "-l", lang],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass

    ps_script = f"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media, ContentType=WindowsRuntime]
function Await($WinRtTask, $ResultType) {{
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.IsGenericMethod }})[0].MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}}
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('{img_path.resolve()}')) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$ocrResult = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
Write-Output $ocrResult.Text
"""
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
        )
        if res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return ""


def run(parameters: dict, player=None, session_memory=None) -> str:
    lang = (parameters.get("lang") or "eng").strip()
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    snap = CAPTURE_DIR / f"radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

    if not _grab_screen(snap):
        return "Screen Radar could not capture display (install Pillow or pyautogui)."

    extracted = _ocr_image(snap, lang=lang)
    if not extracted:
        reply = f"Screen captured to {snap}, but no readable text was detected on screen."
    else:
        try:
            import pyperclip
            pyperclip.copy(extracted)
            clip_note = " (copied to clipboard)"
        except Exception:
            clip_note = ""
        preview = extracted[:1200] + ("..." if len(extracted) > 1200 else "")
        reply = f"Screen Radar extracted {len(extracted)} characters{clip_note}:\n\n{preview}"

    if player:
        try:
            player.write_log(f"JARVIS: Screen Radar scanned ({len(extracted)} chars).")
        except Exception:
            pass
    return reply
