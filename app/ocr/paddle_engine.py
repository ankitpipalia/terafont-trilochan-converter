"""
PaddleOCR adapter — primary OCR engine.

Wraps PaddleOCR's PP-OCRv4 model. First-call init is ~8-12s on CPU;
subsequent pages are ~0.5-2s each. Singleton pattern to avoid re-init.
"""

import time
import logging

logger = logging.getLogger(__name__)


class PaddleEngine:
    """PaddleOCR engine wrapper.

    Usage:
        engine = PaddleEngine()
        result = engine.recognize(image_path)  # Accepts path string or PIL Image
    """

    def __init__(self, use_gpu=False):
        self._ocr = None
        self._init_error = None
        self._use_gpu = use_gpu
        self._init_once()

    def _init_once(self):
        """Lazy-initialize the PaddleOCR model (first-call only).

        Uses lang='ml' (multilingual) which includes Gujarati support.
        """
        if self._ocr is not None:
            return

        try:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ml",  # Multilingual model covers Gujarati
                use_gpu=False,
                show_log=False,
                det_db_box_thresh=0.5,
                rec_img_shape=[3, 48, 320],
                use_space_char=True,
            )
            logger.info("PaddleOCR engine initialized successfully")
        except Exception as e:
            self._init_error = str(e)
            logger.error(f"PaddleOCR init failed: {e}")
            self._ocr = None

    def recognize(self, image_input, on_progress=None):
        """Run OCR on an image.

        Args:
            image_input: path (str) or PIL Image
            on_progress: optional callback(progress: float)

        Returns:
            Dict with keys: text (str), confidence (float 0-100),
                           duration_ms (int), error (str, optional)
        """
        if not self._ocr:
            return {
                "text": "",
                "confidence": 0,
                "duration_ms": 0,
                "error": "PaddleOCR not initialized",
            }

        start = time.time()

        if on_progress:
            on_progress(0.2)

        # Convert PIL Image to numpy if needed
        if hasattr(image_input, "mode"):
            # PIL Image — convert to numpy array
            import numpy as np
            img = np.array(image_input.convert("RGB"))
        else:
            # Path string
            img = image_input

        try:
            results = self._ocr.ocr(img, cls=True)
        except Exception as e:
            return {
                "text": "",
                "confidence": 0,
                "duration_ms": 0,
                "error": str(e),
            }

        if on_progress:
            on_progress(0.8)

        # Parse results — PaddleOCR returns None if no text found
        if not results or not results[0]:
            duration = (time.time() - start) * 1000
            return {"text": "", "confidence": 0, "duration_ms": int(duration)}

        # Extract text and confidence from all detected regions
        # PaddleOCR format: [[bbox, (text_str, confidence)], ...]
        texts = []
        confidences = []
        for line in results[0]:
            if line and len(line) >= 2:
                text_str = line[1][0]  # The full text string
                conf = line[1][1]      # Confidence float
                if text_str:
                    texts.append(text_str)
                    confidences.append(conf)

        duration = (time.time() - start) * 1000

        if on_progress:
            on_progress(1.0)

        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        combined_text = "\n".join(texts)

        return {
            "text": combined_text,
            "confidence": round(avg_conf * 100, 1),
            "duration_ms": int(duration),
        }

    @property
    def is_available(self):
        return self._ocr is not None

    @property
    def init_error(self):
        return self._init_error
