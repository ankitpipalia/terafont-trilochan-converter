"""
Tesseract OCR adapter — fallback engine.

Uses pytesseract with bundled guj.traineddata if available.
Only activated if PaddleOCR fails to initialize.
"""

import os
import logging

logger = logging.getLogger(__name__)


class TesseractEngine:
    """Tesseract OCR engine wrapper (fallback)."""

    def __init__(self, tessdata_prefix=None):
        self._tessdata_prefix = tessdata_prefix
        self._available = self._check_available()

    def _check_available(self):
        """Check if Tesseract is available on the system."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def recognize(self, image_input, on_progress=None):
        """Run OCR on an image.

        Args:
            image_input: path (str) or PIL Image
            on_progress: optional callback

        Returns:
            Dict with keys: text, confidence, duration_ms, error
        """
        import time

        if not self._available:
            return {
                "text": "",
                "confidence": 0,
                "duration_ms": 0,
                "error": "Tesseract not available",
            }

        start = time.time()

        try:
            import pytesseract
            from PIL import Image

            # image_input may already be a PIL Image (from preprocess)
            if hasattr(image_input, "mode"):
                img = image_input
            else:
                img = Image.open(image_input)

            # Build config for tessdata prefix
            kwargs = {}
            if self._tessdata_prefix:
                kwargs["config"] = f"--tessdata-dir {self._tessdata_prefix}"

            text = pytesseract.image_to_string(img, lang="guj", **kwargs)
            duration = (time.time() - start) * 1000

            return {
                "text": text.strip(),
                "confidence": 0,
                "duration_ms": int(duration),
            }
        except Exception as e:
            duration = (time.time() - start) * 1000
            return {
                "text": "",
                "confidence": 0,
                "duration_ms": int(duration),
                "error": str(e),
            }
