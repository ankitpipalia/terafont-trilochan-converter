"""
PDF utilities — PyMuPDF (fitz) page rendering and text extraction.

Used for OCR of scanned PDFs and text extraction from digital PDFs.
"""

from pathlib import Path


def render_pages(pdf_path, dpi=300, page_range=None):
    """Render PDF pages as PIL Images.

    Args:
        pdf_path: Path to PDF file
        dpi: Dots per inch for rendering (higher = better OCR accuracy)
        page_range: Optional tuple (start, end) — 1-indexed, inclusive

    Yields:
        (page_num, PIL.Image) tuples
    """
    import fitz  # PyMuPDF
    from PIL import Image
    from io import BytesIO

    doc = fitz.open(str(pdf_path))
    try:
        total_pages = doc.page_count

        if page_range:
            start = max(1, min(page_range[0], total_pages))
            end = min(page_range[1], total_pages)
            page_nums = range(start, end + 1)
        else:
            page_nums = range(1, total_pages + 1)

        for page_num in page_nums:
            page = doc[page_num - 1]
            zoom = dpi / 72  # 72 is the default PDF DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            image = Image.open(BytesIO(img_data))
            yield page_num, image
    finally:
        doc.close()


def extract_text_layer(pdf_path, page_num):
    """Extract text layer from a PDF page (for digital PDFs).

    Args:
        pdf_path: Path to PDF file
        page_num: 0-indexed page number

    Returns:
        Text string, or empty string if no text layer
    """
    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        if page_num < 0 or page_num >= doc.page_count:
            return ""
        text = doc[page_num].get_text()
        return text
    finally:
        doc.close()


def get_pdf_info(pdf_path):
    """Get basic info about a PDF file.

    Args:
        pdf_path: Path to PDF file

    Returns:
        Dict with keys: page_count, file_size, path
    """
    import fitz
    import os

    doc = fitz.open(str(pdf_path))
    try:
        info = {
            "page_count": doc.page_count,
            "file_size": os.path.getsize(str(pdf_path)),
            "path": str(pdf_path),
        }
        return info
    finally:
        doc.close()
