from __future__ import annotations

import sqlite3
from pathlib import Path

from .util import now_iso, uuid4, sha256_file, norm_path
from .ingest_pdf import extract_pdf_pages
from .chunking import chunk_pages

def upsert_doc(conn: sqlite3.Connection, source_path: str, sha256: str, title: str | None = None, mime: str | None = None) -> tuple[str, bool]:
    source_path = norm_path(source_path)
    row = conn.execute("SELECT doc_id, sha256 FROM doc WHERE source_path = ?", (source_path,)).fetchone()
    now = now_iso()
    if row is None:
        doc_id = uuid4()
        conn.execute(
            "INSERT INTO doc(doc_id, source_path, title, mime, sha256, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
            (doc_id, source_path, title, mime, sha256, now, now),
        )
        conn.commit()
        return doc_id, True
    doc_id = row["doc_id"]
    if row["sha256"] != sha256:
        conn.execute("UPDATE doc SET sha256=?, updated_at=? WHERE doc_id=?", (sha256, now, doc_id))
        conn.commit()
        return doc_id, True
    return doc_id, False

def delete_doc_chunks(conn: sqlite3.Connection, doc_id: str) -> None:
    conn.execute("DELETE FROM chunk WHERE doc_id = ?", (doc_id,))
    conn.commit()

def index_pdf(conn: sqlite3.Connection, pdf_path: str, force: bool = False, min_chars: int = 200) -> dict:
    pdf_path = norm_path(pdf_path)
    sha = sha256_file(pdf_path)
    title = Path(pdf_path).name
    doc_id, changed = upsert_doc(conn, pdf_path, sha, title=title, mime="application/pdf")
    if force:
        changed = True
    if not changed:
        return {"doc_id": doc_id, "source_path": pdf_path, "status": "unchanged"}

    delete_doc_chunks(conn, doc_id)

    pages = extract_pdf_pages(pdf_path)
    chunks = chunk_pages(pages, min_chars=min_chars)

    now = now_iso()
    for idx, (ps, pe, text) in enumerate(chunks):
        chunk_id = uuid4()
        conn.execute(
            "INSERT INTO chunk(chunk_id, doc_id, chunk_index, page_start, page_end, text, char_count, created_at) VALUES(?,?,?,?,?,?,?,?)",
            (chunk_id, doc_id, idx, ps, pe, text, len(text), now),
        )
    conn.commit()
    return {"doc_id": doc_id, "source_path": pdf_path, "status": "indexed", "chunks": len(chunks)}

def list_pdfs(path: str, glob_pat: str = "*.pdf") -> list[str]:
    p = Path(path).expanduser().resolve()
    if p.is_file():
        return [str(p)]
    if not p.is_dir():
        raise FileNotFoundError(str(p))
    return [str(x) for x in sorted(p.rglob(glob_pat))]
