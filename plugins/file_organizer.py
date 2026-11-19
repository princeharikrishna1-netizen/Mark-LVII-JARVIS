"""
JARVIS Plugin: Smart File Organizer & SRO/Document Sorting Assistant
- Organizes downloads and documents by file type and SRO/Document workflow requirements.
"""
from pathlib import Path
import shutil
import os

PLUGIN = {
    "name": "file_organizer",
    "version": "1.0.0",
    "description": "Organizes files in Downloads or Documents folder into structured SRO/Document categories."
}

TOOL = {
    "name": "organize_files",
    "description": "Organizes messy files in Downloads or Documents folder into structured SRO/Document categories (PDFs, Excels, CheckSlips, Certificates).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "target_dir": {
                "type": "STRING",
                "description": "Optional path to organize. Defaults to user Downloads folder."
            }
        },
        "required": []
    }
}

def run(args, player=None, session_memory=None):
    target = args.get("target_dir")
    if not target:
        target_path = Path.home() / "Downloads"
    else:
        target_path = Path(target)

    if not target_path.exists():
        return f"Target directory {target_path} does not exist."

    # Define categories
    categories = {
        "PDF_Documents": [".pdf"],
        "Excel_Sheets": [".xlsx", ".xls", ".csv"],
        "Legal_Records": [".doc", ".docx", ".txt"],
        "Archives": [".zip", ".rar", ".7z"]
    }

    moved_count = 0
    for folder_name in categories.keys():
        folder_path = target_path / folder_name
        folder_path.mkdir(exist_ok=True)

    for file_item in target_path.iterdir():
        if file_item.is_file():
            ext = file_item.suffix.lower()
            placed = False
            for cat, extensions in categories.items():
                if ext in extensions:
                    dest_folder = target_path / cat
                    shutil.move(str(file_item), str(dest_folder / file_item.name))
                    moved_count += 1
                    placed = True
                    break

    result_msg = f"సార్, ఫోల్డర్ క్లీనింగ్ పూర్తయింది. మొత్తం {moved_count} ఫైల్స్ సరిగ్గా సార్ట్ చేయబడ్డాయి."
    if player and hasattr(player, "write_log"):
        player.write_log(f"SYS: {result_msg}")
    
    return result_msg