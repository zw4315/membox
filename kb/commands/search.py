from __future__ import annotations

import sqlite3
from ..db import init_db

def run(conn: sqlite3.Connection, args) -> int:
    init_db(conn)
    q = args.query.strip()

    where = []
    params = []

    if args.doc:
        row = conn.execute("SELECT doc_id FROM doc WHERE source_path=? OR doc_id=?", (args.doc, args.doc)).fetchone()
        if not row:
            print(f"No such doc: {args.doc}")
            return 2
        where.append("f.doc_id = ?")
        params.append(row["doc_id"])

    if args.path_prefix:
        where.append("d.source_path LIKE ?")
        params.append(args.path_prefix.rstrip("/") + "%")

    where_sql = (" AND " + " AND ".join(where)) if where else ""

    snip_tokens = max(8, int(args.show // 8))
    sql = f"""
    SELECT d.source_path, f.page_start, f.chunk_id,
           snippet(chunk_fts, 0, '[', ']', '…', ?) AS snip
    FROM chunk_fts f
    JOIN doc d ON d.doc_id = f.doc_id
    WHERE chunk_fts MATCH ? {where_sql}
    LIMIT ?
    """
    rows = conn.execute(sql, (snip_tokens, q, *params, args.topk)).fetchall()

    if args.format == "json":
        import json
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        return 0

    for i, r in enumerate(rows, 1):
        print(f"{i:>2}. {r['source_path']}  p.{r['page_start']}")
        print(f"    {r['snip']}")
    return 0
