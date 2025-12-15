from __future__ import annotations

from dataclasses import dataclass
from typing import List
from pathlib import Path
import subprocess
import shutil

@dataclass
class PageText:
    page_no: int  # 1-based
    text: str

def _extract_with_pymupdf(pdf_path: str) -> List[PageText]:
    import fitz  # PyMuPDF
    doc = fitz.open(pdf_path)
    out: List[PageText] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = page.get_text("text") or ""
        out.append(PageText(page_no=i+1, text=text))
    doc.close()
    return out

def _extract_with_pypdf(pdf_path: str) -> List[PageText]:
    from pypdf import PdfReader
    reader = PdfReader(pdf_path)
    out: List[PageText] = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        out.append(PageText(page_no=i+1, text=text))
    return out

def _extract_with_pdftotext(pdf_path: str) -> List[PageText]:
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        raise RuntimeError("pdftotext not found")
    proc = subprocess.run([pdftotext, "-layout", pdf_path, "-"], check=True, stdout=subprocess.PIPE)
    txt = proc.stdout.decode("utf-8", errors="ignore")
    pages = txt.split("\f")
    out: List[PageText] = []
    for i, t in enumerate(pages):
        t = t.strip()
        if t:
            out.append(PageText(page_no=i+1, text=t))
    return out

def extract_pdf_pages(pdf_path: str) -> List[PageText]:
    pdf_path = str(Path(pdf_path).expanduser().resolve())
    errors = []
    for fn in (_extract_with_pymupdf, _extract_with_pypdf, _extract_with_pdftotext):
        try:
            pages = fn(pdf_path)
            if pages:
                return pages
        except Exception as e:
            errors.append(f"{fn.__name__}: {e}")
    raise RuntimeError("Failed to extract PDF text. Tried: " + " | ".join(errors))
