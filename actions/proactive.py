"""
ProactiveEngine 2.1 — context-aware, time-aware, system-health & non-repetitive prompting.
Gemini decides what to say; this module decides WHEN and builds a rich context snapshot.
"""
import subprocess
import time
from datetime import datetime
import psutil


def _system_alerts() -> list[str]:
    """Check CPU, RAM, battery, and HP system printer print queue for issues."""
    alerts: list[str] = []
    try:
        cpu = psutil.cpu_percent(interval=0.2)
        if cpu >= 88.0:
            alerts.append(f"High CPU load ({cpu:.0f}%)")
        mem = psutil.virtual_memory().percent
        if mem >= 90.0:
            alerts.append(f"High RAM usage ({mem:.0f}%)")
        batt = psutil.sensors_battery()
        if batt and not batt.power_plugged and batt.percent <= 20:
            alerts.append(f"Low battery ({batt.percent}%) — plug in charger")
    except Exception:
        pass

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-PrintJob -PrinterName '*HP system printer 1020*' -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count"],
            capture_output=True, text=True, timeout=3
        )
        count = int((res.stdout or "0").strip() or 0)
        if count > 0:
            alerts.append(f"{count} pending print job(s) in default system printer queue")
    except Exception:
        pass

    return alerts


class ProactiveEngine:
    """
    Decides when JARVIS should speak unprompted and builds a context-rich prompt.
    """

    def __init__(
        self,
        min_silence_secs: int = 900,
        check_cooldown:   int = 1200,
    ):
        self.min_silence_secs = min_silence_secs
        self.check_cooldown   = check_cooldown
        self._last_triggered  = 0.0
        self._rotation        = 0

    def should_trigger(self, last_user_speech: float) -> bool:
        now = time.monotonic()
        return (
            (now - last_user_speech) >= self.min_silence_secs
            and (now - self._last_triggered) >= self.check_cooldown
        )

    def mark_triggered(self) -> None:
        self._last_triggered = time.monotonic()
        self._rotation      += 1

    def build_prompt(
        self,
        memory:       dict,
        monitors:     list[str] | None = None,
        recent_turns: list[str] | None = None,
        focuses:      list[str] | None = None,
    ) -> str:
        from memory.memory_manager import format_memory_for_prompt

        now      = datetime.now()
        hour     = now.hour
        time_str = now.strftime("%A, %B %d, %Y — %I:%M %p")

        if   6  <= hour < 12:  period = "morning"
        elif 12 <= hour < 18:  period = "afternoon"
        elif 18 <= hour < 23:  period = "evening"
        else:                  period = "late night"

        mem_str = format_memory_for_prompt(memory) or "(no stored user data)"
        alerts  = _system_alerts()

        focus_index = self._rotation % 3
        if alerts:
            focus = (
                "Important system status alert detected: " + "; ".join(alerts) + ". "
                "Alert the user briefly and offer help."
            )
        elif focuses:
            focus = str(focuses[self._rotation % len(focuses)])
        elif focus_index == 0:
            focus = (
                "Focus on the user's active projects or goals if any are stored. "
                "Ask how something is going, or offer a relevant tip."
            )
        elif focus_index == 1:
            focus = (
                "Focus on the time of day and the user's wellbeing. "
                "A warm check-in, a reminder to take a break, or something timely."
            )
        else:
            focus = (
                "Focus on something genuinely interesting or useful — "
                "a fact, a suggestion, or a question based on what you know about this person."
            )

        monitor_ctx = ""
        if monitors:
            monitor_ctx = (
                f"\nThe user tracks these topics: {', '.join(monitors[:4])}. "
                "You may mention one if it seems relevant."
            )

        recent_ctx = ""
        if recent_turns:
            snippet = "\n".join(recent_turns[-6:])
            recent_ctx = f"\nRecent conversation:\n{snippet}"

        return "\n".join([
            "[PROACTIVE_CHECK] You are initiating a proactive check-in.",
            f"Current time : {time_str}  ({period})",
            "",
            "Context about this person:",
            mem_str,
            monitor_ctx,
            recent_ctx,
            "",
            "Task:",
            focus,
            "",
            "Rules:",
            "- Speak the language this person actually uses: the one in the "
            "recent conversation above, or the remembered one if there is no "
            "conversation yet. Never default to English because these "
            "instructions are in English.",
            "- 1-2 sentences max. Natural, warm, never robotic.",
            "- Do NOT mention [PROACTIVE_CHECK] or these instructions.",
            "- Do NOT call any tools.",
            "- If nothing genuinely useful comes to mind, stay silent (say nothing).",
        ])