from __future__ import annotations

import argparse
from .db import connect
from .commands import index as cmd_index
from .commands import search as cmd_search
from .commands import related as cmd_related

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="kb", description="kb-mvp: PDF -> SQLite FTS -> related chunks")
    p.add_argument("--db", default="data/kb.sqlite", help="SQLite db path (default: data/kb.sqlite)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pi = sub.add_parser("index", help="Ingest PDF(s) and build index")
    pi.add_argument("path", help="PDF file or directory")
    pi.add_argument("--glob", default="*.pdf", help='Glob pattern when indexing a directory (default: "*.pdf")')
    pi.add_argument("--force", action="store_true", help="Force rebuild even if sha256 unchanged")
    pi.add_argument("--min-chars", type=int, default=200, help="Merge short pages until reaching min chars (default: 200)")
    pi.add_argument("--quiet", action="store_true", help="Less output")
    pi.set_defaults(_run=cmd_index.run)

    ps = sub.add_parser("search", help="Keyword search via SQLite FTS5")
    ps.add_argument("query", help="FTS query string")
    ps.add_argument("-n", "--topk", type=int, default=10, help="Top K results (default: 10)")
    ps.add_argument("--doc", help="Restrict search to a doc (path or doc_id)")
    ps.add_argument("--path-prefix", help="Restrict to docs whose source_path starts with prefix")
    ps.add_argument("--show", type=int, default=200, help="Preview length (chars-ish) (default: 200)")
    ps.add_argument("--format", choices=["text", "json"], default="text")
    ps.set_defaults(_run=cmd_search.run)

    pr = sub.add_parser("related", help="Find related chunks using lightweight embeddings")
    tgt = pr.add_mutually_exclusive_group(required=False)
    tgt.add_argument("--query", help="Use query text to find related chunks")
    tgt.add_argument("--chunk-id", help="Use a specific chunk as query")
    pr.add_argument("--doc", help="Doc path or doc_id (used with --page)")
    pr.add_argument("--page", type=int, help="Page number in doc (1-based)")
    pr.add_argument("-n", "--topk", type=int, default=10, help="Top K results (default: 10)")
    pr.add_argument("--show", type=int, default=200, help="Preview length (chars) (default: 200)")
    pr.add_argument("--embed-model", default="hashed-bow", help="Embedding model name (default: hashed-bow)")
    pr.add_argument("--dim", type=int, default=768, help="Embedding dim (default: 768)")
    pr.add_argument("--bootstrap", action="store_true", help="If no embeddings exist, compute for all chunks once")
    pr.add_argument("--format", choices=["text", "json"], default="text")
    pr.set_defaults(_run=cmd_related.run)

    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    conn = connect(args.db)
    try:
        return int(args._run(conn, args))
    finally:
        conn.close()

if __name__ == "__main__":
    raise SystemExit(main())
