"""
JARVIS Plugin: High-Speed Computer Intelligence
Processes large logs, directories, and structured datasets to extract statistics,
anomalies, and executive summaries rapidly.
"""
from __future__ import annotations
from pathlib import Path

PLUGIN = {
    "name": "computer_intelligence",
    "description": "Computer Intelligence Engine. Rapidly processes large files, logs, or folders to extract line counts, keyword frequencies, and structural summaries. Trigger on 'process data in [path]', 'analyze large file [path]', or 'compute workspace stats'.",
    "tier": "core",
    "brief": "Rapidly index and summarize large files, logs, and data directories.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {"type": "STRING", "description": "One of: 'analyze_file', 'workspace_stats', or 'search_pattern'"},
            "target_path": {"type": "STRING", "description": "File or folder path to process."},
            "pattern": {"type": "STRING", "description": "Optional keyword pattern to count."}
        },
        "required": ["action"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    act = (parameters.get("action") or "workspace_stats").strip().lower()
    target = Path(parameters.get("target_path") or ".")
    pattern = (parameters.get("pattern") or "").strip().lower()
    try:
        if act == "analyze_file" and target.is_file():
            content = target.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            words = content.split()
            hits = content.lower().count(pattern) if pattern else 0
            extra = f" | Pattern '{pattern}' occurrences: {hits}" if pattern else ""
            reply = f"Computer Intelligence Report on '{target.name}', Sir: {len(lines)} lines, {len(words)} words, {target.stat().st_size} bytes{extra}."
        else:
            py_files = [f for f in target.rglob("*.py") if "__pycache__" not in str(f)]
            total_lines = sum(len(f.read_text(encoding="utf-8", errors="ignore").splitlines()) for f in py_files)
            reply = f"Computer Intelligence Workspace Telemetry, Sir: Indexed {len(py_files)} Python modules totaling {total_lines:,} lines of code."
    except Exception as e:
        reply = f"Sir, Computer Intelligence error: {e}"
    if player:
        try: player.write_log(f"JARVIS: {reply}")
        except Exception: pass
    return reply
