"""
JARVIS Plugin: Custom Desktop Shortcuts & Macros
- Quickly opens frequent SRO/Document directories, tools, and executes desktop shortcuts via voice.
"""
import os
import subprocess
from pathlib import Path

PLUGIN = {
    "name": "desktop_shortcuts",
    "version": "1.0.0",
    "description": "Executes custom desktop macros, opens specific work folders and tools via voice."
}

TOOL = {
    "name": "run_desktop_shortcut",
    "description": "Runs a predefined desktop shortcut or opens a specific workflow directory like SRO docs or downloads.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "shortcut_name": {
                "type": "STRING",
                "description": "Name of the shortcut or tool to open (e.g., sro_docs, downloads, pictures)."
            }
        },
        "required": ["shortcut_name"]
    }
}

def run(args, player=None, session_memory=None):
    name = args.get("shortcut_name", "").lower()
    
    # Custom paths and shortcuts mapping
    shortcuts = {
        "sro_docs": r"C:\Users\Document",
        "downloads": str(Path.home() / "Downloads"),
        "pictures": str(Path.home() / "Pictures"),
    }
    
    target = shortcuts.get(name)
    if target and os.path.exists(target):
        os.startfile(target)
        msg = f"సార్, {name} ఫోల్డర్ విజయవంతంగా ఓపెన్ చేయబడింది."
    else:
        try:
            subprocess.Popen(name, shell=True)
            msg = f"సార్, {name} అప్లికేషన్ లాంచ్ చేయబడింది."
        except Exception as e:
            msg = f"క్షమించండి Hari, ఆ షార్ట్‌కట్ లేదా పాత్ కనుగొనబడలేదు."

    if player and hasattr(player, "write_log"):
        player.write_log(f"SYS: {msg}")
        
    return msg