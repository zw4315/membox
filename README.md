# kb-mvp (Python + argparse + uv)

A minimal knowledge-base MVP:

- `kb index <pdf-or-dir>`: ingest PDF(s) into SQLite, build FTS index
- `kb search "<query>"`: keyword search via SQLite FTS5
- `kb related ...`: related chunks using lightweight embeddings (offline, no external model)

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
kb index /path/to/file.pdf --db data/kb.sqlite
kb search "socket listen backlog" --db data/kb.sqlite -n 10
kb related --doc /path/to/file.pdf --page 12 --db data/kb.sqlite --bootstrap -n 10
```

## Notes

- PDF text extraction tries (in order): PyMuPDF (`fitz`), `pypdf`, `pdftotext` command.
- Embeddings are a lightweight hashed bag-of-words baseline so the MVP works offline.
  Later you can swap in real embeddings by editing `kb/embedder.py`.
