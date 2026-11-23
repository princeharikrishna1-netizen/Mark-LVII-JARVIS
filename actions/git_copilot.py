"""
actions/git_copilot.py — Voice-Driven Git Co-Pilot & Repository Watcher.
Supports git status, diff summary, commit log, and smart auto-commit.
Auto-discovered by core.action_loader via TOOL dict.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _repo_root(repo_path: str = "") -> Path:
    if repo_path and Path(repo_path).exists():
        return Path(repo_path).resolve()
    return Path(__file__).resolve().parent.parent


def _run_git(args: list[str], cwd: Path, timeout: int = 12) -> tuple[int, str]:
    try:
        res = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        out = (res.stdout or res.stderr or "").strip()
        return res.returncode, out
    except FileNotFoundError:
        return 127, "Git is not installed or not in PATH."
    except subprocess.TimeoutExpired:
        return 124, "Git command timed out."
    except Exception as e:
        return 1, f"Git error: {e}"


def git_status_summary(cwd: Path) -> str:
    code, inside = _run_git(["rev-parse", "--is-inside-work-tree"], cwd)
    if code != 0 or inside.lower() != "true":
        return f"'{cwd}' is not a Git repository."

    _, branch = _run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    _, status_short = _run_git(["status", "--short"], cwd)
    _, last_commit = _run_git(["log", "-1", "--pretty=format:%h - %s (%cr)"], cwd)

    lines = [ln for ln in status_short.splitlines() if ln.strip()]
    if not lines:
        return f"Branch: {branch} | Working tree is clean.\nLast Commit: {last_commit}"

    modified = [ln[3:] for ln in lines if ln[:2].strip() in ("M", "MM", "AM")]
    added = [ln[3:] for ln in lines if ln[:2].strip() in ("A", "??")]
    deleted = [ln[3:] for ln in lines if "D" in ln[:2]]

    parts = [f"Branch: {branch} | Total changed files: {len(lines)}"]
    if modified:
        parts.append(f"Modified ({len(modified)}): {', '.join(modified[:8])}")
    if added:
        parts.append(f"New/Untracked ({len(added)}): {', '.join(added[:8])}")
    if deleted:
        parts.append(f"Deleted ({len(deleted)}): {', '.join(deleted[:6])}")
    if last_commit:
        parts.append(f"Last Commit: {last_commit}")
    return "\n".join(parts)


def git_diff_summary(cwd: Path, max_chars: int = 2500) -> str:
    _, stat = _run_git(["diff", "--stat"], cwd)
    _, cached_stat = _run_git(["diff", "--cached", "--stat"], cwd)
    _, diff_body = _run_git(["diff", "--unified=2"], cwd)

    if not diff_body:
        _, diff_body = _run_git(["diff", "--cached", "--unified=2"], cwd)

    if not stat and not cached_stat and not diff_body:
        return "No unstaged or staged diff changes found (check untracked files via status)."

    summary = []
    if stat:
        summary.append(f"Unstaged Stats:\n{stat}")
    if cached_stat:
        summary.append(f"Staged Stats:\n{cached_stat}")
    if diff_body:
        summary.append(f"Diff Preview:\n{diff_body[:max_chars]}")
    return "\n\n".join(summary)


def _generate_auto_message(cwd: Path) -> str:
    _, status_short = _run_git(["status", "--short"], cwd)
    files = [ln[3:].strip().split("/")[-1] for ln in status_short.splitlines() if ln.strip()]
    if not files:
        return "chore: update workspace"
    if len(files) == 1:
        return f"feat: update {files[0]}"
    if len(files) <= 3:
        return f"feat: update {', '.join(files)}"
    return f"feat: update {files[0]}, {files[1]} and {len(files) - 2} more files"


def git_commit_changes(cwd: Path, message: str = "", push: bool = False) -> str:
    _, status_short = _run_git(["status", "--short"], cwd)
    if not status_short.strip():
        return "Nothing to commit — working tree is already clean."

    commit_msg = (message or "").strip() or _generate_auto_message(cwd)

    code_add, out_add = _run_git(["add", "-A"], cwd)
    if code_add != 0:
        return f"git add failed: {out_add}"

    code_cm, out_cm = _run_git(["commit", "-m", commit_msg], cwd)
    if code_cm != 0:
        return f"git commit failed: {out_cm}"

    result = f"Committed with message: '{commit_msg}'\n{out_cm.splitlines()[0] if out_cm else ''}".strip()

    if push:
        code_push, out_push = _run_git(["push"], cwd, timeout=20)
        if code_push == 0:
            result += "\nPushed to remote successfully."
        else:
            result += f"\nCommit succeeded, but push failed: {out_push}"

    return result


def git_recent_log(cwd: Path, count: int = 5) -> str:
    code, out = _run_git(["log", f"-n{max(1, min(count, 15))}", "--pretty=format:%h | %cr | %s"], cwd)
    if code != 0:
        return f"Could not read git log: {out}"
    return f"Recent Commits:\n{out}"


def git_copilot(parameters: dict, **kwargs) -> str:
    """Entry point invoked by core.action_loader."""
    action = (parameters.get("action") or "status").strip().lower()
    repo_path = (parameters.get("repo_path") or "").strip()
    message = (parameters.get("message") or "").strip()
    push = bool(parameters.get("push", False))

    cwd = _repo_root(repo_path)

    if action == "diff":
        return git_diff_summary(cwd)
    if action == "commit":
        return git_commit_changes(cwd, message=message, push=push)
    if action == "log":
        return git_recent_log(cwd)
    return git_status_summary(cwd)


TOOL = {
    "name": "git_copilot",
    "description": (
        "Git repository assistant for checking branch & modified files (status), "
        "inspecting code changes (diff), viewing recent commit history (log), or "
        "staging and committing changes with an auto-generated or custom commit message (commit). "
        "Use whenever the user asks about git status, changed files, code diff, commits, or saving progress to git."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "'status' (modified/untracked files), 'diff' (code changes summary), 'commit' (stage & commit all changes), or 'log' (recent commits).",
            },
            "message": {
                "type": "STRING",
                "description": "Optional commit message when action='commit'. Leave empty to auto-generate from changed files.",
            },
            "push": {
                "type": "BOOLEAN",
                "description": "Set true only if the user explicitly asks to push after committing.",
            },
            "repo_path": {
                "type": "STRING",
                "description": "Optional path to another Git repository. Defaults to the current Mark-LVII project folder.",
            },
        },
        "required": ["action"],
    },
    "handler": git_copilot,
}
