from __future__ import annotations

from typing import List
from .ingest_pdf import PageText

def chunk_pages(pages: List[PageText], min_chars: int = 200) -> List[tuple[int,int,str]]:
    """Return list of (page_start, page_end, text). Merge short pages."""
    chunks: List[tuple[int,int,str]] = []
    buf_text = ""
    buf_start = None
    buf_end = None

    for p in pages:
        t = (p.text or "").strip()
        if not t:
            continue
        if buf_start is None:
            buf_start = p.page_no
            buf_end = p.page_no
            buf_text = t
        else:
            if len(buf_text) < min_chars:
                buf_end = p.page_no
                buf_text += "\n\n" + t
            else:
                chunks.append((buf_start, buf_end or buf_start, buf_text))
                buf_start = p.page_no
                buf_end = p.page_no
                buf_text = t

    if buf_start is not None and buf_text.strip():
        chunks.append((buf_start, buf_end or buf_start, buf_text))

    return chunks
