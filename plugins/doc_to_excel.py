"""
JARVIS Plugin: All-in-One Document Reader, Speaker & Office Excel Extractor
- Reads PDFs, Scanned Images, Word (.docx), and Excel (.xlsx) files & speaks summaries aloud.
- Extracts EC, Check Slips, and Property Registration records into structured Excel (.xlsx)
  matching Registration & Stamps Office column standards.
"""
from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from google.genai import types
from core import gemini

PLUGIN = {
    "name": "extract_doc_to_excel",
    "description": (
        "Reads any document (PDF, scanned image, Word .docx, Excel .xlsx, text), speaks a clear "
        "summary aloud in the user's language (Telugu/English), OR extracts property registration / "
        "EC / Check Slip details (Executant, Claimant, unmasked ID, Relation details, Doc No, "
        "Survey No, Village) into a structured Excel (.xlsx) spreadsheet. Use whenever the user asks "
        "to read a document, summarize a PDF/file, or convert/extract PDF or images to Excel."
    ),
    "tier": "core",
    "brief": "Read & speak any document, or extract PDF/EC/Check-Slip records into Excel.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {
                "type": "STRING",
                "description": "Full path to the file (PDF, image, .docx, .xlsx, .txt) or folder of files."
            },
            "mode": {
                "type": "STRING",
                "description": (
                    "'extract_excel' to extract registration/EC/check-slip records into .xlsx (default for PDFs/images), "
                    "or 'read_speak' to read and summarize the document aloud."
                )
            },
            "output_excel": {
                "type": "STRING",
                "description": "Optional output .xlsx file path."
            },
            "language": {
                "type": "STRING",
                "description": "Language for spoken/text summary (e.g. 'Telugu', 'English'). Default: 'Telugu'."
            }
        },
        "required": ["file_path"],
    },
}

_EXTRACTION_PROMPT = """
You are an expert legal document clerk for the Registration and Stamps Department (Andhra Pradesh / India).
Analyze the attached document (Check Slip, Encumbrance Certificate / EC, or Property Registration Deed).
Extract all parties and document details accurately. Return ONLY valid JSON with this exact schema:

{
  "document_type": "Check Slip | EC | Sale Deed | Gift Deed | Mortgage | Other",
  "document_number": "",
  "document_year": "",
  "sro_office": "",
  "registration_date": "",
  "village_or_locality": "",
  "survey_or_door_no": "",
  "extent_or_area": "",
  "consideration_value": "",
  "market_value": "",
  "parties": [
    {
      "role": "executant | claimant | witness | identifier",
      "name": "",
      "relation_type": "S/o | W/o | D/o | C/o | H/o",
      "relation_name": "",
      "id_number": "",
      "age": "",
      "address": ""
    }
  ]
}

Rules:
- Keep 'role' strictly lowercase: 'executant' or 'claimant' (or 'witness'/'identifier').
- Extract the full 12-digit unmasked ID number if visible in the document (digits only or XXXX XXXX XXXX as written).
- Combine relation cleanly if needed, while filling relation_type and relation_name accurately.
- Include EVERY executant and claimant listed in the document.
- If a field is not present, return "".
"""


def _mime_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "application/octet-stream")


def _read_local_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".docx":
        import docx
        doc = docx.Document(path)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(c.text.strip() for c in row.cells))
        return "\n".join(parts)
    if ext in (".xlsx", ".xls"):
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        lines = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            lines.append(f"--- Sheet: {sheet} ---")
            for row in ws.iter_rows(values_only=True):
                if any(row):
                    lines.append(" | ".join(str(v or "") for v in row))
        return "\n".join(lines)
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_single_file(path: Path) -> dict:
    ext = path.suffix.lower()
    if ext in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        part = types.Part.from_bytes(data=path.read_bytes(), mime_type=_mime_for(path))
        contents = [part, _EXTRACTION_PROMPT]
    else:
        text_data = _read_local_text(path)
        contents = [f"{_EXTRACTION_PROMPT}\n\nDocument Content:\n{text_data[:30000]}"]

    resp = gemini.call(
        contents=contents,
        tier=gemini.SMART,
        timeout_ms=60_000,
    )
    raw = (resp.text or "").strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def _read_and_summarize(path: Path, language: str) -> str:
    ext = path.suffix.lower()
    prompt = (
        f"Read this document carefully and provide a clear, spoken-friendly summary in {language}. "
        "Highlight key names, document numbers, dates, amounts, and important points in 3-5 sentences."
    )
    if ext in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        part = types.Part.from_bytes(data=path.read_bytes(), mime_type=_mime_for(path))
        contents = [part, prompt]
    else:
        text_data = _read_local_text(path)
        contents = [f"{prompt}\n\nDocument Content:\n{text_data[:30000]}"]

    resp = gemini.call(
        contents=contents,
        tier=gemini.SMART,
        timeout_ms=45_000,
    )
    return (resp.text or "").strip()


def _write_to_excel(records: list[tuple[str, dict]], out_path: Path) -> None:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    if out_path.exists():
        wb = openpyxl.load_workbook(out_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Registration Records"
        # Column E (5) = Status (executant/claimant)
        # Column F (6) = ID Number (unmasked)
        # Column H (8) = Relation Type & Name
        headers = [
            "Doc No & Year",          # Col A (1)
            "SRO & Reg Date",         # Col B (2)
            "Village & Survey No",    # Col C (3)
            "Party Name",             # Col D (4)
            "Status",                 # Col E (5) -> executant / claimant
            "ID Number",         # Col F (6) -> unmasked ID
            "Age & Consideration",    # Col G (7)
            "Relation Details",       # Col H (8) -> Relation Type & Name
            "Address",                # Col I (9)
            "Source File",            # Col J (10)
        ]
        ws.append(headers)
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(color="FFFFFF", bold=True)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

    for filename, data in records:
        doc_no_yr = f"{data.get('document_number', '')}/{data.get('document_year', '')}".strip("/")
        sro_date  = f"{data.get('sro_office', '')} ({data.get('registration_date', '')})".strip(" ()")
        vil_surv  = f"{data.get('village_or_locality', '')} - Sy.{data.get('survey_or_door_no', '')}".strip(" -Sy.")
        val_info  = data.get("consideration_value") or data.get("market_value") or ""

        parties = data.get("parties") or [{}]
        for p in parties:
            status = (p.get("role") or "").strip().lower()
            id = (p.get("id_number") or "").strip()
            rel_full = f"{p.get('relation_type', '')} {p.get('relation_name', '')}".strip()
            age_val = f"Age: {p.get('age', '')} | Val: {val_info}".strip(" |Age:Val:")

            ws.append([
                doc_no_yr,
                sro_date,
                vil_surv,
                p.get("name", ""),
                status,
                id,
                age_val,
                rel_full,
                p.get("address", ""),
                filename,
            ])

    for col in ws.columns:
        max_len = max((len(str(cell.value or "")) for cell in col), default=12)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 42)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)


def run(parameters: dict, player=None, session_memory=None) -> str:
    raw_path = (parameters.get("file_path") or "").strip().strip('"')
    mode = (parameters.get("mode") or "extract_excel").strip().lower()
    output_excel = (parameters.get("output_excel") or "").strip().strip('"')
    language = (parameters.get("language") or "Telugu").strip()

    if not raw_path:
        return "Sir, please provide the file or folder path."

    target = Path(os.path.expanduser(raw_path))
    if not target.exists():
        return f"Sir, path not found: {target}"

    try:
        if mode == "read_speak":
            if not target.is_file():
                return "Sir, please provide a single file path to read and summarize."
            if player:
                player.write_log(f"JARVIS: Reading {target.name}...")
            summary = _read_and_summarize(target, language)
            if player:
                try:
                    player.show_content(f"DOCUMENT SUMMARY — {target.name}", summary)
                except Exception:
                    pass
            return summary

        # Default: extract_excel
        supported = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".docx", ".xlsx", ".txt"}
        files = [target] if target.is_file() else [
            f for f in sorted(target.iterdir()) if f.suffix.lower() in supported
        ]
        if not files:
            return "Sir, no supported files found at that path."

        extracted_batch = []
        for f in files:
            if player:
                player.write_log(f"JARVIS: Extracting {f.name} to Excel...")
            parsed = _extract_single_file(f)
            extracted_batch.append((f.name, parsed))

        if output_excel:
            out_path = Path(output_excel)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = target.parent if target.is_file() else target
            out_path = base_dir / f"Extracted_Records_{stamp}.xlsx"

        _write_to_excel(extracted_batch, out_path)
        total_parties = sum(len(d.get("parties") or []) for _, d in extracted_batch)
        msg = (
            f"Sir, {len(files)} document(s) nundi {total_parties} records extract chesi "
            f"{out_path.name} Excel file lo save chesanu."
        )
        if player:
            player.write_log(f"JARVIS: {msg}")
        return msg

    except Exception as e:
        return f"Sir, document operation failed: {e}"