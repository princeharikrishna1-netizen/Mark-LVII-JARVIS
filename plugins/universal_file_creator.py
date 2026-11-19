"""
JARVIS Plugin: Universal File Creator (Auto-Adjusted PDF & Multi-Format Support)
- Automatically handles layout and spacing to prevent ReportLab width errors.
"""
from pathlib import Path
import os

PLUGIN = {
    "name": "universal_file_creator",
    "version": "2.0.0",
    "description": "Creates files in PDF, Markdown, Text or CSV formats with automatic layout correction."
}

TOOL = {
    "name": "create_any_file",
    "description": "Creates a file of any format (pdf, txt, md, csv) with automatic error handling and layout adjustment.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_format": {
                "type": "STRING",
                "description": "Format of the file: pdf, md, txt, csv."
            },
            "topic_or_instructions": {
                "type": "STRING",
                "description": "Content or instructions for the file generation."
            },
            "output_path": {
                "type": "STRING",
                "description": "Optional file output path or name."
            }
        },
        "required": ["file_format", "topic_or_instructions"]
    }
}

def run(args, player=None, session_memory=None):
    fmt = args.get("file_format", "txt").lower()
    content = args.get("topic_or_instructions", "")
    out_path = args.get("output_path", f"Project_Report.{fmt}")
    
    # Resolve path to Desktop if simple name given
    if not os.path.isabs(out_path) and not out_path.startswith("Desktop"):
        out_path = str(Path.home() / "Desktop" / out_path)
    elif out_path.startswith("Desktop"):
        out_path = str(Path.home() / out_path)

    try:
        if fmt == "pdf":
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                
                doc = SimpleDocTemplate(out_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                styles = getSampleStyleSheet()
                
                # Custom safe style with auto-wrapping
                safe_style = ParagraphStyle(
                    'SafeStyle',
                    parent=styles['Normal'],
                    fontSize=10,
                    leading=14,
                    wordWrap='CJK'
                )
                
                story = []
                # Split content into paragraphs to avoid overflow
                for line in content.split('\n'):
                    if line.strip():
                        story.append(Paragraph(line, safe_style))
                        story.append(Spacer(1, 6))
                        
                doc.build(story)
                msg = f"సార్, PDF ఫైల్ విజయవంతంగా క్రియేట్ చేయబడింది: {out_path}"
            except ImportError:
                # Fallback to text if ReportLab fails or has layout issues
                fallback_path = out_path.replace(".pdf", ".txt")
                with open(fallback_path, "w", encoding="utf-8") as f:
                    f.write(content)
                msg = f"ReportLab లేఅవుట్ సమస్య కారణంగా PDF బదులుగా టెక్స్ట్ ఫైల్ సేవ్ చేయబడింది: {fallback_path}"
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            msg = f"సార్, {fmt.upper()} ఫైల్ విజయవంతంగా సేవ్ చేయబడింది: {out_path}"
            
    except Exception as e:
        msg = f"క్షమించండి Hari, ఫైల్ క్రియేట్ చేయడంలో ఎర్రర్ వచ్చింది: {str(e)}"

    if player and hasattr(player, "write_log"):
        player.write_log(f"SYS: {msg}")
        
    return msg