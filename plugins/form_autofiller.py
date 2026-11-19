"""
JARVIS Plugin: Smart Registration Form Auto-Filler
Reads extracted party/property records from an Excel (.xlsx) sheet (or direct values)
and types them sequentially into an active browser/desktop form using Tab navigation.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

PLUGIN = {
    "name": "autofill_registration_form",
    "description": (
        "Auto-fills a web or desktop registration form using rows from an extracted Excel (.xlsx) "
        "spreadsheet or provided party details (Name, Relation, ID, Survey No, Village). "
        "Gives a 3-second countdown so the user can focus the first input box, then types each "
        "field separated by Tab keys. Use when the user says 'fill form from excel', "
        "'auto-fill registration details', or 'type row 1 into the form'."
    ),
    "tier": "core",
    "brief": "Auto-type extracted Excel row data into an active form using Tab keys.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "excel_path": {
                "type": "STRING",
                "description": "Path to the .xlsx spreadsheet containing extracted registration records."
            },
            "row_number": {
                "type": "INTEGER",
                "description": "Data row number to fill (1 = first data row after header). Default is 1."
            },
            "role_filter": {
                "type": "STRING",
                "description": "Optional filter: 'Executant' or 'Claimant' to pick that specific party."
            },
            "fields": {
                "type": "STRING",
                "description": (
                    "Comma-separated column names in exact form tab order. "
                    "Default: 'Party Name,Relation Name,ID Number,Survey/Door No,Village'"
                )
            }
        },
        "required": ["excel_path"],
    },
}

DEFAULT_FIELDS = [
    "Party Name",
    "Relation Name",
    "ID Number",
    "Survey/Door No",
    "Village",
]


def _load_row_from_excel(excel_path: Path, row_number: int, role_filter: str) -> dict[str, str]:
    import openpyxl

    wb = openpyxl.load_workbook(excel_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        raise ValueError("Excel file has no data rows.")

    headers = [str(h or "").strip() for h in rows[0]]
    data_rows = rows[1:]

    if role_filter:
        rf = role_filter.strip().lower()
        role_idx = next((i for i, h in enumerate(headers) if h.lower() == "role"), -1)
        if role_idx >= 0:
            filtered = [r for r in data_rows if str(r[role_idx] or "").strip().lower() == rf]
            if filtered:
                data_rows = filtered

    idx = max(0, min(row_number - 1, len(data_rows) - 1))
    chosen = data_rows[idx]
    return {
        headers[i]: str(chosen[i] if i < len(chosen) and chosen[i] is not None else "").strip()
        for i in range(len(headers))
        if headers[i]
    }


def run(parameters: dict, player=None, session_memory=None) -> str:
    raw_path = (parameters.get("excel_path") or "").strip().strip('"')
    row_num = max(1, int(parameters.get("row_number", 1) or 1))
    role_filter = (parameters.get("role_filter") or "").strip()
    raw_fields = (parameters.get("fields") or "").strip()

    if not raw_path:
        return "Sir, please provide the Excel file path to auto-fill from."

    target = Path(os.path.expanduser(raw_path))
    if not target.is_file():
        return f"Sir, Excel file not found: {target}"

    try:
        import pyautogui
    except ImportError:
        return "Sir, pyautogui is not installed. Run: pip install pyautogui"

    try:
        record = _load_row_from_excel(target, row_num, role_filter)
        field_order = (
            [f.strip() for f in raw_fields.split(",") if f.strip()]
            if raw_fields
            else DEFAULT_FIELDS
        )

        values_to_type: list[tuple[str, str]] = []
        for col in field_order:
            # Case-insensitive column lookup
            matched_key = next((k for k in record if k.lower() == col.lower()), None)
            val = record[matched_key] if matched_key else ""
            values_to_type.append((col, val))

        if player:
            player.write_log("JARVIS: Click the first form field now — typing starts in 3 seconds...")

        time.sleep(3.0)

        pyautogui.PAUSE = 0.08
        for idx, (col_name, val) in enumerate(values_to_type):
            if val:
                pyautogui.write(val, interval=0.02)
            if idx < len(values_to_type) - 1:
                pyautogui.press("tab")

        summary = ", ".join(f"{k}={v}" for k, v in values_to_type if v)
        msg = f"Sir, auto-filled {len(values_to_type)} fields from row {row_num} ({summary[:120]})."
        if player:
            player.write_log(f"JARVIS: {msg}")
        return msg

    except Exception as e:
        return f"Sir, form auto-fill failed: {e}"