"""
Gujarati Converter Desktop — API exposed to the webview.

All methods on this class are callable from JavaScript via
`window.pywebview.api.<method_name>()`.
"""

import os
import sys
import json
import logging
import threading
import time

from app.converter import convert_unicode_to_tera, convert_tera_to_unicode

# OCR/PDF deps are heavy and optional in slim builds. Import lazily so the
# app can still run for text conversion only.
try:
    from app.ocr.engine import create_engine
    from app.ocr.preprocess import preprocess_for_ocr
    from app.workers import OCRWorker
    from app.pdf_utils import extract_text_layer, get_pdf_info
    _OCR_DEPS_AVAILABLE = True
except ImportError as _e:
    create_engine = None
    preprocess_for_ocr = None
    OCRWorker = None
    extract_text_layer = None
    get_pdf_info = None
    _OCR_DEPS_AVAILABLE = False
    logging.getLogger(__name__).info(
        "OCR/PDF dependencies not installed — slim build (%s)", _e
    )

logger = logging.getLogger(__name__)


class API:
    """Python API exposed to the frontend via pywebview."""

    def __init__(self):
        self._engine = None
        self._worker = OCRWorker() if _OCR_DEPS_AVAILABLE else None
        self._engine_lock = threading.Lock()
        self._window_ref = None
        if _OCR_DEPS_AVAILABLE:
            # Pre-warm engine on a background thread
            threading.Thread(target=self._warm_engine, daemon=True).start()
        else:
            logger.info("Running in slim mode — OCR/PDF features disabled")

    def set_window(self, window):
        """Store a reference to the pywebview Window for JS evaluation.

        This is the cross-platform way to evaluate JS — avoids the
        macOS-only webview.platforms.cocoa attribute.
        """
        self._window_ref = window

    def _eval_js(self, js_code):
        """Evaluate JS in the WebView window (cross-platform)."""
        if self._window_ref:
            self._window_ref.evaluate_js(js_code)

    def _warm_engine(self):
        """Pre-warm the OCR engine in a background thread."""
        if not _OCR_DEPS_AVAILABLE:
            return
        try:
            with self._engine_lock:
                self._engine = create_engine()
            logger.info("OCR engine pre-warmed successfully")
        except RuntimeError as e:
            logger.warning(f"OCR engine not available: {e}")
            self._engine = None

    def _get_engine(self):
        """Get the OCR engine (lazy init if warm-up failed)."""
        if not _OCR_DEPS_AVAILABLE:
            return None
        with self._engine_lock:
            if self._engine is None:
                try:
                    self._engine = create_engine()
                except RuntimeError:
                    return None
            return self._engine

    # ── Conversion ──────────────────────────────────────────────────────

    def convert_unicode_to_tera(self, text):
        """Convert Unicode Gujarati text to TeraFont Trilochan."""
        if not text:
            return ""
        return convert_unicode_to_tera(text)

    def convert_tera_to_unicode(self, text):
        """Convert TeraFont Trilochan text to Unicode Gujarati."""
        if not text:
            return ""
        return convert_tera_to_unicode(text)

    # ── File dialogs (return paths) ─────────────────────────────────────

    def pick_image(self):
        """Open a file dialog for image files. Returns selected path or None."""
        from webview import create_file_dialog, OPEN_DIALOG
        paths = create_file_dialog(OPEN_DIALOG, file_types=(
            "Images (*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.webp)",
            "*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.webp",
        ))
        return paths[0] if paths else None

    def pick_pdf(self):
        """Open a file dialog for PDF files. Returns selected path or None."""
        from webview import create_file_dialog, OPEN_DIALOG
        paths = create_file_dialog(OPEN_DIALOG, file_types=(
            "PDF Files (*.pdf)",
            "*.pdf",
        ))
        return paths[0] if paths else None

    def pick_folder(self):
        """Open a folder selection dialog. Returns selected path or None."""
        from webview import create_file_dialog, FOLDER_DIALOG
        paths = create_file_dialog(FOLDER_DIALOG)
        return paths[0] if paths else None

    def save_text(self, content, filename):
        """Save text content to a file. Returns the saved path or None."""
        from webview import create_file_dialog, SAVE_DIALOG
        paths = create_file_dialog(SAVE_DIALOG, save_filename=filename)
        if paths:
            path = paths[0]
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return path
        return None

    # ── Settings ────────────────────────────────────────────────────────

    def get_settings(self):
        """Return user settings as a dict."""
        settings_path = _get_settings_path()
        if os.path.exists(settings_path):
            with open(settings_path) as f:
                return json.load(f)
        return {
            "engine": "paddle",
            "dpi": 300,
            "theme": "dark",
            "last_folder": None,
            "ocr_enabled": True,
        }

    def set_settings(self, settings):
        """Persist user settings to disk."""
        settings_path = _get_settings_path()
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w") as f:
            json.dump(settings, f)

    # ── OCR ─────────────────────────────────────────────────────────────

    def ocr_image(self, path):
        """Run OCR on an image file. Returns {text, confidence, duration_ms}."""
        if not path or not os.path.exists(path):
            return {"text": "", "confidence": 0, "duration_ms": 0}

        engine = self._get_engine()
        if not engine:
            return {"text": "", "confidence": 0, "duration_ms": 0,
                    "error": "OCR engine not available"}

        try:
            from PIL import Image
            with Image.open(path) as img:
                preprocessed = preprocess_for_ocr(img)
            result = engine.recognize(preprocessed)
            return result
        except Exception as e:
            logger.error(f"OCR image failed: {e}")
            return {"text": "", "confidence": 0, "duration_ms": 0,
                    "error": str(e)}

    def ocr_pdf(self, path, page_range=None):
        """OCR a multi-page PDF. Runs in background, returns job_id.

        Progress via: window._onOCRProgress(jobId, progress, current, total)
        Done via:     window._onOCRDone(jobId, result)
        """
        if not path or not os.path.exists(path):
            return ""

        engine = self._get_engine()
        if not engine:
            return ""

        def _notify_progress(job_id, progress, current_page, total_pages):
            pct = int(progress * 100)
            self._eval_js(
                f'window._onOCRProgress("{job_id}", {progress}, {current_page}, {total_pages}, "{pct}%");'
            )

        def _notify_done(job_id, result):
            import json as _json
            self._eval_js(
                f'window._onOCRDone("{job_id}", {_json.dumps(result)});'
            )

        return self._worker.ocr_pdf(
            pdf_path=path,
            engine=engine,
            preprocess_fn=preprocess_for_ocr,
            dpi=300,
            page_range=page_range,
            on_progress=_notify_progress,
            on_done=_notify_done,
        )

    def ocr_folder(self, path, recursive=False):
        """OCR all images in a folder. Runs in background, returns job_id."""
        if not path or not os.path.isdir(path):
            return ""

        engine = self._get_engine()
        if not engine:
            return ""

        def _notify_progress(job_id, progress, current, total):
            self._eval_js(
                f'window._onOCRProgress("{job_id}", {progress}, {current}, {total});'
            )

        def _notify_done(job_id, result):
            import json as _json
            self._eval_js(
                f'window._onOCRDone("{job_id}", {_json.dumps(result)});'
            )

        return self._worker.ocr_folder(
            folder_path=path,
            engine=engine,
            preprocess_fn=preprocess_for_ocr,
            recursive=recursive,
            on_progress=_notify_progress,
            on_done=_notify_done,
        )

    def get_pdf_info(self, path):
        """Get PDF file info. Returns {page_count, file_size, path}."""
        if not _OCR_DEPS_AVAILABLE or not path or not os.path.exists(path):
            return {}
        return get_pdf_info(path)

    def has_ocr(self):
        """Check if OCR is available. Returns False in slim builds."""
        if not _OCR_DEPS_AVAILABLE:
            return False
        return self._get_engine() is not None


def _get_settings_path():
    """Get the settings file path using platform-appropriate convention."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "GujaratiConverter", "settings.json")
