"""Document format I/O: DOCX read/write + PDF write.

All heavy imports are lazy so the slim build still works (the corresponding
buttons in the UI show a graceful "not available" toast).

DOCX support:    pip install python-docx
PDF export:      pip install reportlab
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


# ─── DOCX (python-docx) ─────────────────────────────────────────────────

def docx_available() -> bool:
    try:
        import docx  # noqa: F401  (python-docx package)
        return True
    except ImportError:
        return False


def read_docx(path: str) -> str:
    """Extract all paragraph text from a .docx. Preserves paragraph order
    and joins with \\n. Tables and headers are read flat."""
    import docx  # type: ignore
    doc = docx.Document(path)
    parts: list[str] = []
    for para in doc.paragraphs:
        parts.append(para.text)
    # Include table cells (common in legal forms)
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text for cell in row.cells if cell.text)
            if row_text:
                parts.append(row_text)
    return "\n".join(parts)


def write_docx(path: str, text: str, font_name: str = "TeraFont Trilochan",
               font_size_pt: int = 12) -> None:
    """Write a flat .docx where every paragraph uses the given font.

    Legal docs usually need TeraFont Trilochan applied uniformly.
    """
    import docx  # type: ignore
    from docx.shared import Pt

    doc = docx.Document()
    for line in text.split("\n"):
        para = doc.add_paragraph()
        run = para.add_run(line if line else "")
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)
        # Also set East-Asian / complex script fonts (Word's quirk)
        try:
            from docx.oxml.ns import qn
            r_pr = run._element.get_or_add_rPr()
            rfonts = r_pr.find(qn("w:rFonts"))
            if rfonts is None:
                from docx.oxml import OxmlElement
                rfonts = OxmlElement("w:rFonts")
                r_pr.append(rfonts)
            rfonts.set(qn("w:ascii"), font_name)
            rfonts.set(qn("w:hAnsi"), font_name)
            rfonts.set(qn("w:cs"), font_name)
            rfonts.set(qn("w:eastAsia"), font_name)
        except Exception:
            # Best-effort — the rfonts dance fails sometimes on old python-docx
            pass
    doc.save(path)


def _find_bundled_font(name: str) -> str:
    """Locate a bundled font, handling both dev and PyInstaller-frozen cases."""
    import sys
    # PyInstaller --onedir extracts datas to _MEIPASS/ui/ (per the .spec)
    if getattr(sys, "frozen", False):
        candidates = [
            os.path.join(getattr(sys, "_MEIPASS", ""), "ui", name),
            os.path.join(os.path.dirname(sys.executable), "_internal", "ui", name),
            os.path.join(os.path.dirname(sys.executable), "ui", name),
        ]
    else:
        candidates = [os.path.join(os.path.dirname(__file__), "ui", name)]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return candidates[0]


# ─── PDF export (reportlab) ─────────────────────────────────────────────

def pdf_available() -> bool:
    try:
        import reportlab  # noqa: F401
        return True
    except ImportError:
        return False


def write_pdf(path: str, text: str, font_path: Optional[str] = None,
              font_size: int = 12, page_size_name: str = "A4") -> None:
    """Render `text` to a PDF with TeraFont embedded.

    Args:
        path:       Output file path.
        text:       Body text.
        font_path:  Path to TRILOCHA.TTF. If None, looks next to this file.
        font_size:  Body font size (pt).
        page_size_name: "A4" or "letter".
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.pdfgen import canvas

    if font_path is None:
        font_path = _find_bundled_font("TRILOCHA.TTF")

    if not os.path.exists(font_path):
        raise FileNotFoundError(f"Font file not found: {font_path}")

    page_size = LETTER if page_size_name.lower() == "letter" else A4

    # Register the font (only once per process — reportlab tolerates re-register)
    font_name = "TeraFontTrilochan"
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception as e:
        logger.warning("Font registration retry: %s", e)

    c = canvas.Canvas(path, pagesize=page_size)
    width, height = page_size

    # Margins (1 inch on each side)
    margin = 72.0
    line_height = font_size * 1.4
    x = margin
    y = height - margin

    c.setFont(font_name, font_size)

    # Simple line-by-line layout. Wrap long lines naively at the page width.
    usable_width = width - 2 * margin
    for line in text.split("\n"):
        if y < margin + line_height:
            c.showPage()
            c.setFont(font_name, font_size)
            y = height - margin

        # Naive wrap: if the line is too wide, split at last space before width
        while line:
            chunk, remainder = _split_for_width(c, font_name, font_size, line, usable_width)
            c.drawString(x, y, chunk)
            y -= line_height
            line = remainder
            if line and y < margin + line_height:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - margin

    c.save()


def _split_for_width(c, font_name: str, font_size: int, line: str,
                     max_width: float) -> tuple[str, str]:
    """Split `line` into (head, tail) so head fits within max_width."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    if stringWidth(line, font_name, font_size) <= max_width:
        return line, ""

    # Walk backwards from the end to find a break point at a space.
    cut = len(line)
    while cut > 0:
        if line[cut - 1] == " ":
            if stringWidth(line[:cut - 1], font_name, font_size) <= max_width:
                return line[:cut - 1], line[cut:]
        cut -= 1

    # No space found → hard-break at character level.
    cut = len(line)
    while cut > 0 and stringWidth(line[:cut], font_name, font_size) > max_width:
        cut -= 1
    return line[:cut], line[cut:]
