# Mark-LVII Architecture & Code Logic Explanation

## 1. Entry Point & Core Loop (`main.py` & `ui.py`)
- **`main.py`**: Initializes the main event loop in a background thread, maintaining the bidirectional real-time Gemini Live audio/vision session (`JarvisLive`). It handles audio streaming (`sounddevice`), speech-to-text / text-to-speech fallback pipelines, wake-word detection (`core/wake_word.py`), push-to-talk (`core/hotkey.py`), proactive briefings (`actions/proactive.py`), and system monitoring.
- **`ui.py` / `gui/`**: Manages the PyQt6 graphical user interface on the Qt main thread. This includes the holographic reactor HUD (`gui/hud.py`), glass panels, metrics display (`gui/metrics.py`), and theme handling (`gui/theme.py`, `gui/style.py`). Thread safety is guaranteed via signals and thread-safe `JarvisUI` (`player`) methods.

## 2. Action & Plugin Execution Subsystems (`actions/`, 📁 `plugins/`)
- **Actions (`actions/*.py`)**: Core system capabilities auto-discovered by `core/action_loader.py`. They perform desktop control, browser actions, background monitoring, weather reports, and voice switching.
- **Plugins (`plugins/*.py`)**: Drop-in extension modules auto-discovered by `core/plugin_loader.py`. Each plugin defines a `PLUGIN` dictionary and a `run(parameters, player, session_memory)` function. They operate on worker threads and interact with the user interface strictly through thread-safe `player` calls (`write_log`, `show_content`, `show_quiz`, etc.).

## 3. Background Task & Routine Engines (`core/tasks/`, `core/routines/`)
- **Task Engine (`core/tasks/`)**: Manages long-running background asynchronous work (e.g., deep research, multi-step drafting, report generation) using agent profiles from `agents/` (such as `researcher.md` and `general.md`), atomic disk storage (`store.py`), and tool safety enforcement (`tools.py`).
- **Routine Engine (`core/routines/`)**: Schedules unprompted autonomous assistant actions such as morning briefings, proactive quiet-hour check-ins, and news watches based on time rules (`rules.py`).

## 4. AI & Model Layer (`core/gemini.py`, `providers/`)
- **Gemini & Fallback Ladder (`core/gemini.py`)**: Manages model API keys (`config/api_keys.json`), timeouts, quota cooldowns, and fallback tiers (`FAST`, `SMART`).
- **Providers (`providers/`)**: Optional alternative local/cloud STT, LLM, and TTS providers (Whisper, Piper, OpenAI, ElevenLabs) integrated via `providers/registry.py`.

## 5. Security, Memory, & Utilities
- **Memory (`memory/`)**: Manages configuration settings (`config_manager.py`) and long-term user context (`memory_manager.py`).
- **Security & Confirmations (`core/confirm.py`, `core/undo.py`, `proactive_security.py`)**: Implements AES-GCM token audits, irreversible action confirmation gates, and a shared undo stack.
