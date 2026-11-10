#!/usr/bin/env python3
"""
Burst a mobile-UI mockup PDF deck into one PNG per page.

Used by the mobile-ui-implement skill (Mode A, step 1) so a design deck like
`PRS_PriceTagAudit_Mobile_UI2.pdf` becomes a set of images an agent can Read
and decompose screen by screen.

Usage:
    python pdf_extract.py DECK.pdf [-o OUT_DIR] [--dpi 200] [--prefix page]

Writes OUT_DIR/<prefix>-01.png, <prefix>-02.png, ... (zero-padded, 1-based).
After extraction, Read each page, discard non-screen pages (covers, section
dividers), and rename kept screens to mockups/NN-screen-name.png.

Requires: PyMuPDF  ->  pip install PyMuPDF
"""

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Burst a PDF deck into per-page PNGs.")
    parser.add_argument("pdf", help="Path to the source PDF deck.")
    parser.add_argument(
        "-o", "--out-dir", default="mockups",
        help="Output directory for the page PNGs (default: mockups).",
    )
    parser.add_argument(
        "--dpi", type=int, default=200,
        help="Render resolution in DPI (default: 200; use 300 for crisp text).",
    )
    parser.add_argument(
        "--prefix", default="page",
        help="Filename prefix for each page (default: page).",
    )
    args = parser.parse_args()

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("ERROR: PyMuPDF is not installed. Run: pip install PyMuPDF", file=sys.stderr)
        return 2

    pdf_path = Path(args.pdf)
    if not pdf_path.is_file():
        print(f"ERROR: file not found: {pdf_path}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    zoom = args.dpi / 72.0  # PDF points are 72 per inch
    matrix = fitz.Matrix(zoom, zoom)

    doc = fitz.open(pdf_path)
    page_count = doc.page_count
    width = max(2, len(str(page_count)))

    written = []
    for i, page in enumerate(doc, start=1):
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        name = f"{args.prefix}-{str(i).zfill(width)}.png"
        dest = out_dir / name
        pixmap.save(dest)
        written.append(dest)

    doc.close()

    print(f"Extracted {len(written)} page(s) at {args.dpi} DPI into {out_dir}/:")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
