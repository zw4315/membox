from __future__ import annotations
from dotenv import load_dotenv
from pathlib import Path
import os
import argparse
import shutil
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter

DOCS_DIR = Path(
    os.getenv("MEMBOX_DOCS_DIR", "data/docs")
).expanduser()

def split_single_pdf(
    input_path: Path,
    output_dir_for_pdf: Path,
    pages_per_part: int = 4,
) -> None:
    """把一个 PDF 切成若干 part，结果写到 output_dir_for_pdf 里。"""
    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_path}")

    output_dir_for_pdf.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)

    if total_pages == 0:
        print(f"[WARN] PDF has 0 pages: {input_path}")
        return

    print(f"  - Total pages: {total_pages}, pages_per_part={pages_per_part}")

    part_index = 1

    for start in range(0, total_pages, pages_per_part):
        end = min(start + pages_per_part, total_pages)

        writer = PdfWriter()
        for page_idx in range(start, end):
            writer.add_page(reader.pages[page_idx])

        # 转成 1-based 页码用于文件名
        start_page_num = start + 1
        end_page_num = end

        part_str = f"{part_index:02d}"
        start_page_str = f"{start_page_num:03d}"
        end_page_str = f"{end_page_num:03d}"

        output_filename = f"part_{part_str}_p{start_page_str}-{end_page_str}.pdf"
        output_path = output_dir_for_pdf / output_filename

        with output_path.open("wb") as f:
            writer.write(f)

        print(
            f"    -> part {part_index:02d}: "
            f"pages {start_page_num}-{end_page_num} -> {output_path.name}"
        )

        part_index += 1


def already_processed(output_dir_for_pdf: Path) -> bool:
    """简单判断这个 PDF 是否已经被处理过：输出目录中是否已有 .pdf 文件。"""
    if not output_dir_for_pdf.exists():
        return False
    return any(output_dir_for_pdf.glob("*.pdf"))


def clean_output_dir(output_dir_for_pdf: Path) -> None:
    """强制重新处理时，清空某个输出目录。"""
    if not output_dir_for_pdf.exists():
        return
    for p in output_dir_for_pdf.iterdir():
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p)


def iter_pdfs_in_dir(directory: Path) -> Iterable[Path]:
    """列出目录下所有 .pdf 文件（不递归）。"""
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Split PDF(s) into parts, each containing N pages. "
            "Input can be a single PDF file or a directory of PDFs."
        )
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to input PDF file OR a directory containing PDFs.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Base directory to store results (default: ./output).",
    )
    parser.add_argument(
        "-n",
        "--pages-per-part",
        type=int,
        default=4,
        help="Number of pages per part (default: 4).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-splitting even if output already exists (will clear that output dir).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path: Path = args.input
    base_output_dir: Path = (args.output_dir or (input_path.parent if input_path.is_file() else input_path)).expanduser()
    pages_per_part: int = args.pages_per_part
    force: bool = args.force

    if input_path.is_file():
        # 单文件模式
        if input_path.suffix.lower() != ".pdf":
            raise ValueError(f"Input file is not a PDF: {input_path}")

        pdf_output_dir = base_output_dir / input_path.stem

        print(f"[FILE] {input_path.name}")
        print(f"  Output dir: {pdf_output_dir}")

        if already_processed(pdf_output_dir) and not force:
            print("  -> Skipped (already processed, use --force to redo).")
            return

        if force:
            print("  -> --force specified, cleaning output dir...")
            clean_output_dir(pdf_output_dir)

        split_single_pdf(
            input_path=input_path,
            output_dir_for_pdf=pdf_output_dir,
            pages_per_part=pages_per_part,
        )

    elif input_path.is_dir():
        # 目录批量模式
        pdfs = list(iter_pdfs_in_dir(input_path))
        if not pdfs:
            print(f"[DIR] No PDFs found in: {input_path}")
            return

        total = len(pdfs)
        print(f"[DIR] Found {total} PDF(s) in {input_path}")
        print(f"  Base output dir: {base_output_dir}")

        for idx, pdf in enumerate(pdfs, start=1):
            pdf_output_dir = base_output_dir / pdf.stem
            print(f"\n[{idx}/{total}] {pdf.name}")
            print(f"  Output dir: {pdf_output_dir}")

            if already_processed(pdf_output_dir) and not force:
                print("  -> Skipped (already processed, use --force to redo).")
                continue

            if force:
                print("  -> --force specified, cleaning output dir...")
                clean_output_dir(pdf_output_dir)

            split_single_pdf(
                input_path=pdf,
                output_dir_for_pdf=pdf_output_dir,
                pages_per_part=pages_per_part,
            )

        print("\nAll done.")
    else:
        raise FileNotFoundError(f"Input path not found: {input_path}")


if __name__ == "__main__":
    main()

