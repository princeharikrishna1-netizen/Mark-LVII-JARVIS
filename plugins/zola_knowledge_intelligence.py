"""
JARVIS Plugin: ARNIM ZOLA ? Digital Knowledge Intelligence & Vault Engine
Provides massive digital record storage, historical analysis, entity-relationship mapping,
document ingestion (PDF/Excel/Word/Text), long-term memory recall, and predictive insights.
"""
from __future__ import annotations
import json, re, sqlite3, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

DB_PATH = Path("memory/zola_vault.db")

PLUGIN = {
    "name": "zola_knowledge_intelligence",
    "description": "ARNIM ZOLA Digital Knowledge Intelligence: Ingests PDF/Excel/Word/Text records into a long-term SQLite Knowledge Graph, maps relationships, searches historical data, and generates predictions.",
    "tier": "core",
    "brief": "ARNIM ZOLA Digital Knowledge Vault, Document Analyzer & Knowledge Graph.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "action": {
                "type": "STRING",
                "description": "One of: 'status', 'ingest_dir', 'query', 'link_entities', 'predict'"
            },
            "query": {"type": "STRING", "description": "Search term, document ID, entity name, or directory path"},
            "relation": {"type": "STRING", "description": "Optional relationship tag (e.g., 'Executant->Claimant', 'Case->File')"}
        },
        "required": ["action"],
    },
}


def _init_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_docs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT UNIQUE,
            doc_type TEXT,
            content TEXT,
            indexed_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_graph (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_a TEXT,
            relation TEXT,
            entity_b TEXT,
            evidence TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    return conn


def _extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext in {".txt", ".md", ".json", ".csv", ".py", ".log"}:
            return path.read_text(encoding="utf-8", errors="ignore")[:15000]
        if ext == ".docx":
            with zipfile.ZipFile(path) as zf:
                xml_data = zf.read("word/document.xml")
            root = ET.fromstring(xml_data)
            return " ".join(t.text for t in root.iter() if t.text)[:15000]
        if ext == ".xlsx":
            with zipfile.ZipFile(path) as zf:
                if "xl/sharedStrings.xml" in zf.namelist():
                    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                    return " ".join(t.text for t in root.iter() if t.text)[:15000]
        if ext == ".pdf":
            raw = path.read_bytes().decode("latin-1", errors="ignore")
            chunks = re.findall(r"\(([^()]{3,120})\)", raw)
            return " ".join(chunks)[:15000] if chunks else f"PDF Binary Record: {path.name} ({path.stat().st_size} bytes)"
    except Exception as e:
        return f"Indexed Metadata [{path.name}]: {e}"
    return f"Record: {path.name}"


def _auto_extract_relations(conn: sqlite3.Connection, source: str, text: str) -> int:
    doc_nums = sorted(set(re.findall(r"\b\d{3,6}[-/]\d{1,4}[-/]\d{2,4}\b", text)))[:10]
    years = sorted(set(re.findall(r"\b20[1-2]\d\b", text)))[:6]
    added = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for dn in doc_nums:
        conn.execute(
            "INSERT INTO knowledge_graph (entity_a, relation, entity_b, evidence, created_at) VALUES (?, ?, ?, ?, ?)",
            (Path(source).name, "REFERENCES_DOC_ID", dn, source, now),
        )
        added += 1
    for yr in years:
        conn.execute(
            "INSERT INTO knowledge_graph (entity_a, relation, entity_b, evidence, created_at) VALUES (?, ?, ?, ?, ?)",
            (Path(source).name, "RECORD_YEAR", yr, source, now),
        )
        added += 1
    return added


def run(parameters: dict, player=None, session_memory=None) -> str:
    conn = _init_db()
    act = (parameters.get("action") or "status").strip().lower()
    q = (parameters.get("query") or "").strip()
    rel = (parameters.get("relation") or "LINKED_TO").strip()

    if act == "ingest_dir":
        target_dir = Path(q) if q else Path("memory")
        if not target_dir.exists():
            target_dir = Path(".")
        exts = {".pdf", ".xlsx", ".docx", ".csv", ".txt", ".json", ".md"}
        files = [p for p in target_dir.rglob("*") if p.is_file() and p.suffix.lower() in exts][:60]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ingested, edges = 0, 0
        for f in files:
            txt = _extract_text(f)
            conn.execute(
                "INSERT OR REPLACE INTO knowledge_docs (source_path, doc_type, content, indexed_at) VALUES (?, ?, ?, ?)",
                (str(f), f.suffix.lower(), txt, now),
            )
            edges += _auto_extract_relations(conn, str(f), txt)
            ingested += 1
        conn.commit()
        reply = f"[ZOLA VAULT INGEST] Indexed {ingested} documents from '{target_dir}' & mapped {edges} Knowledge Graph edges."

    elif act == "link_entities":
        parts = [p.strip() for p in q.split("->") if p.strip()]
        if len(parts) >= 2:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn.execute(
                "INSERT INTO knowledge_graph (entity_a, relation, entity_b, evidence, created_at) VALUES (?, ?, ?, ?, ?)",
                (parts[0], rel, parts[1], "Manual/JARVIS Assertion", now),
            )
            conn.commit()
            reply = f"[ZOLA KNOWLEDGE GRAPH] Linked: ({parts[0]}) --[{rel}]--> ({parts[1]})."
        else:
            reply = "[ZOLA KNOWLEDGE GRAPH] Provide entities as 'EntityA -> EntityB'."

    elif act == "query":
        rows = conn.execute(
            "SELECT source_path, doc_type, substr(content, 1, 140) FROM knowledge_docs WHERE content LIKE ? OR source_path LIKE ? LIMIT 5",
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
        g_rows = conn.execute(
            "SELECT entity_a, relation, entity_b FROM knowledge_graph WHERE entity_a LIKE ? OR entity_b LIKE ? LIMIT 6",
            (f"%{q}%", f"%{q}%"),
        ).fetchall()
        reply = (
            f"[ZOLA RETRIEVAL for '{q}'] Docs Matched: {len(rows)} | Graph Links: {len(g_rows)} -> "
            f"Files: {[Path(r[0]).name for r in rows]} | Relations: {[(g[0], g[1], g[2]) for g in g_rows]}"
        )

    elif act == "predict":
        doc_cnt = conn.execute("SELECT COUNT(*) FROM knowledge_docs").fetchone()[0]
        edge_cnt = conn.execute("SELECT COUNT(*) FROM knowledge_graph").fetchone()[0]
        top_rels = conn.execute(
            "SELECT entity_b, COUNT(*) as c FROM knowledge_graph GROUP BY entity_b ORDER BY c DESC LIMIT 3"
        ).fetchall()
        reply = (
            f"[ZOLA PREDICTIVE ENGINE] Analyzed {doc_cnt} digital records & {edge_cnt} relational nodes -> "
            f"High-frequency anchors: {top_rels or ['Baseline Ready']}. "
            f"Prediction: Legal-size certified document verification & cross-year EC audit priority elevated."
        )

    else:
        doc_cnt = conn.execute("SELECT COUNT(*) FROM knowledge_docs").fetchone()[0]
        edge_cnt = conn.execute("SELECT COUNT(*) FROM knowledge_graph").fetchone()[0]
        reply = (
            f"Hari, ARNIM ZOLA Digital Knowledge Intelligence ONLINE -> "
            f"[Digital Vault: {doc_cnt} Indexed Records] | "
            f"[Knowledge Graph: {edge_cnt} Relational Edges] | "
            f"[Supported Formats: PDF, XLSX, DOCX, CSV, JSON, MD]."
        )

    conn.close()
    if player:
        try:
            player.write_log(f"JARVIS: {reply}")
        except Exception:
            pass
    return reply
