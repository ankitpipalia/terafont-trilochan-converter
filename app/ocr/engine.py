"""
OCR engine factory — picks the best available engine.

Primary: PaddleOCR (best Gujarati accuracy)
Fallback: Tesseract (if Paddle fails)
"""

from app.ocr.paddle_engine import PaddleEngine
from app.ocr.tesseract_engine import TesseractEngine


class OCREngine:
    """Abstract base for OCR engines. All engines implement recognize()."""

    def recognize(self, image_path, on_progress=None):
        """Recognize text from an image. Must be implemented by subclasses."""
        raise NotImplementedError


def create_engine(engine_name="paddle", tessdata_prefix=None):
    """Create the best available OCR engine.

    Args:
        engine_name: 'paddle', 'tesseract', or 'auto' (try paddle, fallback to tesseract)
        tessdata_prefix: Path to tessdata for tesseract fallback

    Returns:
        OCREngine instance

    Raises:
        RuntimeError: If no OCR engine is available
    """
    if engine_name == "tesseract":
        engine = TesseractEngine(tessdata_prefix=tessdata_prefix)
        if not engine._available:
            raise RuntimeError("Tesseract OCR is not available on this system")
        return engine

    # Default: try Paddle first, fall back to Tesseract
    paddle = PaddleEngine()
    if paddle.is_available:
        return paddle

    if engine_name == "paddle":
        raise RuntimeError(
            f"PaddleOCR failed to initialize: {paddle.init_error}\n"
            "Install paddlepaddle and ensure it's available."
        )

    # Fallback to Tesseract
    tesseract = TesseractEngine(tessdata_prefix=tessdata_prefix)
    if tesseract._available:
        return tesseract

    raise RuntimeError("No OCR engine available. Install PaddleOCR or Tesseract.")
