from __future__ import annotations

import sqlite3
from mcore.db import init_db
from mcore.embedder import hashed_bow_embedding
from mcore.vector_store import fetch_all_embeddings, cosine_topk, upsert_embeddings

def _ensure_embeddings_for_doc(conn: sqlite3.Connection, doc_id: str, model: str, dim: int) -> None:
    rows = conn.execute("""
      SELECT c.chunk_id, c.text
      FROM chunk c
      LEFT JOIN embedding e ON e.chunk_id = c.chunk_id AND e.embedding_model = ?
      WHERE c.doc_id = ? AND e.chunk_id IS NULL
      ORDER BY c.chunk_index
    """, (model, doc_id)).fetchall()
    if not rows:
        return
    items = []
    for r in rows:
        items.append((r["chunk_id"], model, dim, hashed_bow_embedding(r["text"], dim=dim)))
    upsert_embeddings(conn, items)

def run(conn: sqlite3.Connection, args) -> int:
    init_db(conn)
    model = args.embed_model
    dim = args.dim

    if args.query:
        qvec = hashed_bow_embedding(args.query, dim=dim)
    else:
        if args.chunk_id:
            row = conn.execute("SELECT doc_id, text FROM chunk WHERE chunk_id=?", (args.chunk_id,)).fetchone()
            if not row:
                print(f"No such chunk_id: {args.chunk_id}")
                return 2
            doc_id = row["doc_id"]
            base_text = row["text"]
        else:
            if not args.doc or not args.page:
                print("Need either --query, or (--doc AND --page), or --chunk-id")
                return 2
            drow = conn.execute("SELECT doc_id FROM doc WHERE source_path=? OR doc_id=?", (args.doc, args.doc)).fetchone()
            if not drow:
                print(f"No such doc: {args.doc}")
                return 2
            doc_id = drow["doc_id"]
            crow = conn.execute("""
              SELECT chunk_id, text
              FROM chunk
              WHERE doc_id=? AND page_start<=? AND page_end>=?
              ORDER BY ABS(page_start-?) ASC
              LIMIT 1
            """, (doc_id, args.page, args.page, args.page)).fetchone()
            if not crow:
                print(f"No chunk found for page {args.page}")
                return 2
            base_text = crow["text"]

        qvec = hashed_bow_embedding(base_text, dim=dim)
        _ensure_embeddings_for_doc(conn, doc_id, model, dim)

    ids, got_dim, mat = fetch_all_embeddings(conn, model)
    if not ids:
        if not args.bootstrap:
            print("No embeddings found. Re-run with --bootstrap once, or add embedding during index (later).")
            return 2
        rows = conn.execute("SELECT chunk_id, text FROM chunk").fetchall()
        items = [(r["chunk_id"], model, dim, hashed_bow_embedding(r["text"], dim=dim)) for r in rows]
        upsert_embeddings(conn, items)
        ids, got_dim, mat = fetch_all_embeddings(conn, model)

    top = cosine_topk(qvec, ids, mat, k=args.topk)

    # fetch info
    out = []
    for chunk_id, score in top:
        r = conn.execute("""
          SELECT d.source_path, c.page_start, c.page_end, c.chunk_id, substr(c.text, 1, ?) AS preview
          FROM chunk c JOIN doc d ON d.doc_id=c.doc_id
          WHERE c.chunk_id=?
        """, (args.show, chunk_id)).fetchone()
        if r:
            out.append((score, r))

    if args.format == "json":
        import json
        print(json.dumps([
            {
              "score": s,
              "source_path": r["source_path"],
              "page_start": r["page_start"],
              "page_end": r["page_end"],
              "chunk_id": r["chunk_id"],
              "preview": r["preview"],
            } for s, r in out
        ], ensure_ascii=False, indent=2))
        return 0

    for i, (s, r) in enumerate(out, 1):
        print(f"{i:>2}. score={s:.3f}  {r['source_path']}  p.{r['page_start']}-{r['page_end']}")
        print("    " + r["preview"].replace("\n", " ")[:args.show])
    return 0
