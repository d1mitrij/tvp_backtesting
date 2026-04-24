#!/usr/bin/env python3
"""Convert PDF to Markdown using pymupdf4llm."""

import sys
import argparse
from pathlib import Path


def convert(pdf_path: str, output: str | None = None) -> Path:
    import pymupdf4llm

    src = Path(pdf_path)
    if not src.exists():
        sys.exit(f"File not found: {src}")

    md_text = pymupdf4llm.to_markdown(str(src))

    dest = Path(output) if output else src.with_suffix(".md")
    dest.write_text(md_text, encoding="utf-8")
    return dest


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to Markdown")
    parser.add_argument("pdf", help="Input PDF file")
    parser.add_argument("-o", "--output", help="Output .md file (default: same name as PDF)")
    args = parser.parse_args()

    dest = convert(args.pdf, args.output)
    print(f"Saved: {dest}")


if __name__ == "__main__":
    main()
