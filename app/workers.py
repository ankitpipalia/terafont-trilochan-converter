"""
Background workers for OCR and PDF processing.

Uses threading to keep the UI responsive. Progress callbacks are sent
to the UI via pywebview events.
"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future

logger = logging.getLogger(__name__)


class Worker:
    """Base class for background workers using a thread pool."""

    def __init__(self, max_workers=2):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._futures = {}

    def submit(self, fn, *args, job_id=None, on_progress=None, on_done=None):
        """Submit a task to run in the background.

        Args:
            fn: Callable to run
            *args: Arguments to pass to fn
            job_id: Optional unique ID for the job
            on_progress: Callback(job_id, progress: float)
            on_done: Callback(job_id, result)

        Returns:
            job_id string
        """
        if job_id is None:
            job_id = f"job_{id(fn)}_{id(args)}"

        def _wrapped():
            try:
                result = fn(*args)
                if on_done:
                    on_done(job_id, result)
            except Exception as e:
                logger.error(f"Worker task failed: {e}")
                if on_done:
                    on_done(job_id, {"error": str(e)})

        future = self._executor.submit(_wrapped)
        self._futures[job_id] = future
        return job_id

    def get_status(self, job_id):
        """Get the status of a job."""
        future = self._futures.get(job_id)
        if future is None:
            return "unknown"
        if future.done():
            if future.exception():
                return "error"
            return "completed"
        return "running"

    def is_running(self, job_id):
        """Check if a specific job is still running."""
        future = self._futures.get(job_id)
        return future is not None and not future.done()


class OCRWorker(Worker):
    """Worker specifically for batch OCR (PDF pages, image folders)."""

    def ocr_pdf(self, pdf_path, engine, preprocess_fn, dpi=300, page_range=None,
                on_progress=None, on_done=None):
        """OCR a multi-page PDF."""
        from app.pdf_utils import render_pages, extract_text_layer

        def _run():
            try:
                pages = list(render_pages(pdf_path, dpi=dpi, page_range=page_range))
                total = len(pages)
                if total == 0:
                    return {"text": "", "pages": [], "error": "No pages found"}

                total_text = []
                page_results = []
                errors = []

                for i, (page_num, image) in enumerate(pages):
                    progress = (i + 1) / total

                    # Check for text layer — skip OCR if digital text exists
                    text_layer = extract_text_layer(pdf_path, page_num - 1)
                    if text_layer and text_layer.strip():
                        page_results.append({
                            "page": page_num,
                            "text": text_layer.strip(),
                            "source": "text_layer",
                        })
                        total_text.append(text_layer.strip())
                    else:
                        preprocessed = preprocess_fn(image)
                        result = engine.recognize(preprocessed)
                        text = result.get("text", "")
                        page_results.append({
                            "page": page_num,
                            "text": text,
                            "confidence": result.get("confidence", 0),
                            "source": "ocr",
                        })
                        if text:
                            total_text.append(text)

                    # Report progress with all expected args
                    if on_progress:
                        on_progress(f"pdf_{pdf_path}", progress, i + 1, total)

                return {
                    "text": "\n\n".join(total_text),
                    "pages": page_results,
                    "total_pages": total,
                }

            except Exception as e:
                logger.error(f"OCR PDF failed: {e}")
                return {"text": "", "pages": [], "error": str(e)}

        return self.submit(
            _run,
            job_id=f"pdf_{pdf_path}",
            on_progress=on_progress,
            on_done=on_done,
        )

    def ocr_folder(self, folder_path, engine, preprocess_fn, recursive=False,
                   on_progress=None, on_done=None):
        """OCR all images in a folder."""
        from pathlib import Path

        image_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.webp'}

        def _run():
            try:
                images = []
                folder = Path(folder_path)
                if recursive:
                    for ext in image_extensions:
                        images.extend(folder.rglob(f"*{ext}"))
                        images.extend(folder.rglob(f"*{ext.upper()}"))
                else:
                    for ext in image_extensions:
                        images.extend(folder.glob(f"*{ext}"))
                        images.extend(folder.glob(f"*{ext.upper()}"))

                images = sorted(set(images))
                total = len(images)
                if total == 0:
                    return {"text": "", "files": [], "error": "No images found"}

                total_text = []
                file_results = []

                for i, image_path in enumerate(images):
                    progress = (i + 1) / total
                    preprocessed = preprocess_fn(image_path)
                    result = engine.recognize(preprocessed)
                    text = result.get("text", "")
                    if text:
                        total_text.append(f"--- {image_path.name} ---\n{text}")
                    file_results.append({
                        "file": str(image_path),
                        "text": text,
                        "confidence": result.get("confidence", 0),
                    })

                    if on_progress:
                        on_progress(
                            f"folder_{folder_path}",
                            progress,
                            i + 1,
                            total,
                        )

                return {
                    "text": "\n\n".join(total_text),
                    "files": file_results,
                    "total_files": total,
                }

            except Exception as e:
                logger.error(f"OCR folder failed: {e}")
                return {"text": "", "files": [], "error": str(e)}

        return self.submit(
            _run,
            job_id=f"folder_{folder_path}",
            on_progress=on_progress,
            on_done=on_done,
        )
