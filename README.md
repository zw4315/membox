# mm-mvp (Python + argparse + uv)

A minimal knowledge-base MVP:

 - `mm index <pdf-or-dir>`: ingest PDF(s) into SQLite, build FTS index
 - `mm search "<query>"`: keyword search via SQLite FTS5
 - `mm related ...`: related chunks using lightweight embeddings (offline, no external model)

## Install (uv)

```bash
# Create venv
uv venv .venv
# Activate (bash/zsh)
source .venv/bin/activate

# Install editable
uv pip install -e .

# (Optional) for best PDF extraction quality
# uv pip install pymupdf pypdf
```

## Run

```bash
mm index /path/to/file.pdf --db data/mb.sqlite
mm search "socket listen backlog" --db data/mb.sqlite -n 10
mm related --doc /path/to/file.pdf --page 12 --db data/mb.sqlite --bootstrap -n 10
mm related --query "concept" --db data/mb.sqlite --bootstrap -n 10
```

## Notes

- PDF text extraction tries (in order): PyMuPDF (`fitz`), `pypdf`, `pdftotext` command.
- Embeddings are a lightweight hashed bag-of-words baseline so the MVP works offline.
  Later you can swap in real embeddings by editing `mcore/embedder.py`.
- `mm related --query "concept" --bootstrap` uses your query text as the vector seed.
  On first run it computes embeddings for all chunks (`--bootstrap`), then returns the most similar chunks.

## Common errors and usage

- `mm` alone prints help; a subcommand is required (`index`, `search`, `related`, `api`).
- `related` needs one of:
  - `--query "text"`
  - `--chunk-id <id>`
  - `--doc /path/to/file.pdf --page 12`
- If `related` says no embeddings, re-run once with `--bootstrap`.
