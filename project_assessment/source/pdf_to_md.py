#!/usr/bin/env python3
"""
PDF to Markdown Converter - Root level script
Converts all NEW PDF files (no existing .md counterpart) recursively.
Skips virtual environments and already-converted files.
"""

import sys
import os
from pathlib import Path

try:
    import pymupdf
except ImportError:
    print("Error: PyMuPDF not found. Installing...")
    os.system(f"{sys.executable} -m pip install pymupdf")
    import pymupdf

SKIP_DIRS = {'.venv', 'venv', '__pycache__', '.git', 'node_modules'}


def pdf_to_markdown(pdf_path):
    pdf_path = Path(pdf_path)
    output_path = pdf_path.with_suffix('.md')

    print(f"Converting: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    markdown_content = []
    title = pdf_path.stem.replace('_', ' ').replace('-', ' ')
    markdown_content.append(f"# {title}\n\n")
    markdown_content.append(f"*Converted from PDF: {pdf_path.name}*\n\n")
    markdown_content.append("---\n\n")

    for page_num in range(len(doc)):
        page = doc[page_num]
        markdown_content.append(f"## Page {page_num + 1}\n\n")
        text = page.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        markdown_content.append('\n'.join(lines))
        markdown_content.append("\n\n---\n\n")

    doc.close()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(markdown_content))

    print(f"  Created: {output_path.name}")
    return output_path


def find_new_pdfs(root='.'):
    root = Path(root)
    new_pdfs = []
    for pdf_path in root.rglob('*.pdf'):
        # Skip virtual envs and hidden dirs
        if any(part in SKIP_DIRS for part in pdf_path.parts):
            continue
        md_path = pdf_path.with_suffix('.md')
        if not md_path.exists():
            new_pdfs.append(pdf_path)
    return new_pdfs


def main():
    root = Path('.')
    print(f"Scanning for new PDFs in: {root.resolve()}\n")

    new_pdfs = find_new_pdfs(root)

    if not new_pdfs:
        print("No new PDF files found (all PDFs already have .md counterparts).")
        return

    print(f"Found {len(new_pdfs)} new PDF(s) to convert:\n")
    for p in new_pdfs:
        print(f"  {p}")
    print()

    successful = 0
    errors = 0
    for pdf_file in new_pdfs:
        try:
            pdf_to_markdown(pdf_file)
            successful += 1
        except Exception as e:
            print(f"  ERROR processing {pdf_file.name}: {e}")
            errors += 1

    print(f"\n{'='*60}")
    print(f"Done: {successful} converted, {errors} errors")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
