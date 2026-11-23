"""
actions/local_docs_search.py — Local Document, Code & PDF Knowledge Search.
Searches across Desktop, Documents, Downloads, and current project folders
for PDFs, text, markdown, CSV, JSON, and Python files.
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from pypdf import PdfReader
    _HAS_PDF = True
except Exception:
    _HAS_PDF = False

_TEXT_EXTS = frozenset({".txt", ".md", ".py", ".json", ".csv", ".log", ".yaml", ".yml", ".ini"})
_SKIP_DIRS = frozenset({".git", ".venv", "venv", "__pycache__", "node_modules", "backups", "time_machine"})


def _default_roots() -> list[Path]:
    home = Path.home()
    proj = Path(__file__).resolve().parent.parent
    candidates = [
        proj,
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
    ]
    return [p for p in candidates if p.exists()]


def _extract_text(file_path: Path, max_chars: int = 8000) -> str:
    ext = file_path.suffix.lower()
    try:
        if ext == ".pdf":
            if not _HAS_PDF:
                return ""
            reader = PdfReader(str(file_path))
            chunks = []
            total = 0
            for page in reader.pages[:15]:
                txt = page.extract_text() or ""
                chunks.append(txt)
                total += len(txt)
                if total >= max_chars:
                    break
            return "\n".join(chunks)[:max_chars]
        elif ext in _TEXT_EXTS:
            return file_path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""
    return ""


def search_local_docs(query: str, folder: str = "", limit: int = 5) -> str:
    q = (query or "").strip().lower()
    if not q:
        return "Provide a keyword or topic to search in local documents."

    roots = [Path(folder).expanduser()] if (folder and Path(folder).expanduser().exists()) else _default_roots()
    keywords = [w for w in q.split() if len(w) > 1] or [q]

    matches = []
    scanned = 0
    max_files = 450

    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d.lower() not in _SKIP_DIRS]
            for fname in filenames:
                if scanned >= max_files:
                    break
                fpath = Path(dirpath) / fname
                ext = fpath.suffix.lower()
                if ext != ".pdf" and ext not in _TEXT_EXTS:
                    continue
                try:
                    if fpath.stat().st_size > 8 * 1024 * 1024:  # Skip >8 MB files for speed
                        continue
                except Exception:
                    continue

                scanned += 1
                name_low = fname.lower()
                name_hits = sum(1 for kw in keywords if kw in name_low)

                content = _extract_text(fpath, max_chars=6000)
                content_low = content.lower()
                body_hits = sum(content_low.count(kw) for kw in keywords)

                score = name_hits * 5 + body_hits
                if score > 0:
                    snippet = ""
                    for kw in keywords:
                        idx = content_low.find(kw)
                        if idx != -1:
                            start = max(0, idx - 90)
                            end = min(len(content), idx + 180)
                            snippet = " ".join(content[start:end].split())
                            break
                    matches.append((score, str(fpath), snippet))
            if scanned >= max_files:
                break

    if not matches:
        return f"No matching PDFs or documents found for '{query}' (scanned {scanned} files)."

    matches.sort(key=lambda x: x[0], reverse=True)
    out_lines = [f"Found {len(matches)} matching file(s) (scanned {scanned}):"]
    for score, path_str, snip in matches[:limit]:
        line = f"- {Path(path_str).name} [{path_str}]"
        if snip:
            line += f"\n  Snippet: \"{snip}...\""
        out_lines.append(line)
    return "\n".join(out_lines)


def read_local_doc(file_query: str, folder: str = "") -> str:
    target = Path(file_query).expanduser()
    if target.is_file():
        txt = _extract_text(target, max_chars=4500)
        return f"File: {target}\n---\n{txt}" if txt else f"Could not extract text from '{target}'."

    q = (file_query or "").strip().lower()
    roots = [Path(folder).expanduser()] if (folder and Path(folder).expanduser().exists()) else _default_roots()
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d.lower() not in _SKIP_DIRS]
            for fname in filenames:
                if q in fname.lower():
                    fpath = Path(dirpath) / fname
                    txt = _extract_text(fpath, max_chars=4500)
                    if txt:
                        return f"File: {fpath}\n---\n{txt}"
    return f"Could not find readable file matching '{file_query}'."


def local_docs_search(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    action = (parameters.get("action") or "search").strip().lower()
    query = (parameters.get("query") or "").strip()
    folder = (parameters.get("folder") or "").strip()

    if action == "read":
        return read_local_doc(query, folder=folder)
    return search_local_docs(query, folder=folder)


TOOL = {
    "name": "local_docs_search",
    "description": (
        "Searches and reads local PDFs, notes, markdown, CSV, JSON, and code files across "
        "Desktop, Documents, Downloads, and the project workspace. Use when the user asks to "
        "find a document/PDF on their PC, search their local files for a topic, or read/summarize a local file."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "'search' to find files matching a topic/keyword, or 'read' to extract text from a specific file.",
            },
            "query": {
                "type": "STRING",
                "description": "Topic/keyword for 'search', or file name/path for 'read'.",
            },
            "folder": {
                "type": "STRING",
                "description": "Optional specific folder path (e.g., 'Desktop', 'Documents', or full path).",
            },
        },
        "required": ["action", "query"],
    },
    "handler": local_docs_search,
}
