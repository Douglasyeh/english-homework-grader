"""Render PDF pages to PNG images. Does not run OCR or recognition."""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium

# ~200 DPI: enough for later region crops; not a final production setting.
RENDER_SCALE = 200 / 72


def render_pdf_pages(pdf_bytes: bytes, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(pdf_bytes)
    try:
        page_count = len(document)
        for page_index in range(page_count):
            page = document[page_index]
            try:
                bitmap = page.render(scale=RENDER_SCALE)
                image = bitmap.to_pil()
                dest = output_dir / f"page-{page_index:03d}.png"
                image.save(dest, format="PNG")
            finally:
                page.close()
        return page_count
    finally:
        document.close()
