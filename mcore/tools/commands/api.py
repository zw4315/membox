from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

def add_parser(sub: argparse._SubParsersAction) -> None:
    host = os.getenv("MEMBOX_HOST", "127.0.0.1")
    port = os.getenv("MEMBOX_PORT", "8000")
    if host == "0.0.0.0":
        host = "127.0.0.1"
    base_default = os.getenv("MEMBOX_API", f"http://{host}:{port}")
    pa = sub.add_parser("api", help="HTTP API client")
    pa.add_argument("--base", default=base_default, help="API base URL")
    pa_sub = pa.add_subparsers(dest="api_cmd", required=True)

    pa_ing = pa_sub.add_parser("ingest", help="Ingest a PDF or directory")
    pa_ing.add_argument("path")
    pa_ing.add_argument("--glob", default="*.pdf")
    pa_ing.add_argument("--force", action="store_true")
    pa_ing.add_argument("--min-chars", type=int, default=200)

    pa_s = pa_sub.add_parser("search", help="Search indexed content")
    pa_s.add_argument("query")
    pa_s.add_argument("--topk", type=int, default=10)
    pa_s.add_argument("--doc", default=None)
    pa_s.add_argument("--path-prefix", default=None)
    pa_s.add_argument("--snippet-tokens", type=int, default=24)
    pa_s.add_argument("--max-chars", type=int, default=400)
    pa_s.add_argument("--format", choices=["text", "json"], default="text")

    pa_r = pa_sub.add_parser("reindex", help="Reindex path or existing docs")
    pa_r.add_argument("--path", default=None)
    pa_r.add_argument("--glob", default="*.pdf")
    pa_r.add_argument("--force", action="store_true", default=True, help="Force rebuild (default: true)")
    pa_r.add_argument("--no-force", dest="force", action="store_false", help="Do not force rebuild")
    pa_r.add_argument("--min-chars", type=int, default=200)

def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {detail}") from e

def run(args) -> int:
    base = args.base.rstrip("/")

    if args.api_cmd == "ingest":
        payload = {
            "path": args.path,
            "glob": args.glob,
            "force": bool(args.force),
            "min_chars": args.min_chars,
        }
        out = _post_json(f"{base}/ingest", payload)

    elif args.api_cmd == "search":
        payload = {
            "query": args.query,
            "topk": args.topk,
            "doc": args.doc,
            "path_prefix": args.path_prefix,
            "snippet_tokens": args.snippet_tokens,
            "max_chars": args.max_chars,
        }
        out = _post_json(f"{base}/search", payload)

        if args.format == "text":
            hits = out.get("hits", [])
            for i, r in enumerate(hits, 1):
                page = ""
                if r.get("page_start") is not None:
                    if r.get("page_end") and r["page_end"] != r["page_start"]:
                        page = f"  p.{r['page_start']}-{r['page_end']}"
                    else:
                        page = f"  p.{r['page_start']}"
                print(f"{i:>2}. score={r.get('score', 0):.3f}  {r.get('source_path', '')}{page}")
                print(f"    {r.get('snippet', '')}")
            return 0

    elif args.api_cmd == "reindex":
        payload = {
            "path": args.path,
            "glob": args.glob,
            "force": bool(args.force),
            "min_chars": args.min_chars,
        }
        out = _post_json(f"{base}/reindex", payload)

    else:
        raise SystemExit("Unknown api command")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0
