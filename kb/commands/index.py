from __future__ import annotations

import sqlite3
from .common import print_kv
from ..indexer import index_pdf, list_pdfs
from ..db import init_db

def run(conn: sqlite3.Connection, args) -> int:
    init_db(conn)
    pdfs = list_pdfs(args.path, glob_pat=args.glob)
    total = indexed = unchanged = 0
    for p in pdfs:
        total += 1
        info = index_pdf(conn, p, force=args.force, min_chars=args.min_chars)
        if info["status"] == "indexed":
            indexed += 1
        else:
            unchanged += 1
        if not args.quiet:
            print_kv(info)
    if not args.quiet:
        print(f"\nDone. total={total} indexed={indexed} unchanged={unchanged}")
    return 0
