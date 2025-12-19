from __future__ import annotations

import argparse
import os
import sys
import textwrap
from pathlib import Path

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

from mcore.db import connect
from mcore.tools.commands import index as cmd_index
from mcore.tools.commands import search as cmd_search
from mcore.tools.commands import related as cmd_related
from mcore.tools.commands import api as cmd_api

load_dotenv()

class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass

class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.print_help(sys.stderr)
        self.exit(2, f"\nerror: {message}\n")

def build_parser() -> argparse.ArgumentParser:
    repo_root = Path(__file__).resolve().parents[2]
    default_db = os.getenv("MEMBOX_DB_PATH", str(repo_root / "data" / "membox.sqlite"))
    epilog = textwrap.dedent(
        """\
        Examples:
          mm index ./data/pdfs
          mm search "redis index"
          mm api search "vector db"
        """
    )
    p = Parser(
        prog="mm",
        description="membox: PDF -> SQLite FTS -> related chunks",
        epilog=epilog,
        formatter_class=HelpFormatter,
    )
    p.add_argument("--db", default=default_db, help="SQLite db path")
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

    cmd_api.add_parser(sub)

    return p

def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "api":
        return cmd_api.run(args)

    conn = connect(args.db)
    try:
        return int(args._run(conn, args))
    finally:
        conn.close()

if __name__ == "__main__":
    raise SystemExit(main())
