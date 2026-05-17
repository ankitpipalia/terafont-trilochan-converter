"""HTTP server mode for self-hosted deployments.

Exposes the same API surface as the PyWebView bridge, but over REST.
The web UI (app/ui/) loads `api-bridge.js` which shims
`window.pywebview.api.*` calls onto fetch() requests against this server.

Run locally:
    pip install -r requirements.txt
    uvicorn app.server:app --host 0.0.0.0 --port 8000

Or in Docker (production):
    docker compose -f docker-compose.prod.yml up -d

OCR / DOCX / PDF are all available if the corresponding Python packages
are installed (they are in the full build / production Docker image).
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import __version__
from app.converter import convert_tera_to_unicode, convert_unicode_to_tera

logger = logging.getLogger(__name__)

# Lazily-loaded OCR engine + doc support (matches api.py's pattern).
_engine = None
_engine_error: Optional[str] = None

try:
    from app.ocr.engine import create_engine
    from app.ocr.preprocess import preprocess_for_ocr
    from app.pdf_utils import extract_text_layer, get_pdf_info, render_pages
    _OCR_AVAILABLE = True
except ImportError as e:
    _OCR_AVAILABLE = False
    _engine_error = str(e)
    create_engine = None
    preprocess_for_ocr = None
    extract_text_layer = None
    get_pdf_info = None
    render_pages = None

try:
    from app import docs as _docs
    _DOCS_AVAILABLE = True
except ImportError:
    _docs = None
    _DOCS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────
# Lifecycle: pre-warm OCR engine in the background
# ─────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-warm OCR engine at startup."""
    global _engine, _engine_error
    if _OCR_AVAILABLE:
        try:
            logger.info("Pre-warming OCR engine...")
            _engine = create_engine()
            logger.info("OCR engine ready.")
        except Exception as e:
            _engine_error = str(e)
            logger.warning("OCR engine init failed: %s", e)
    yield
    # No teardown for now; daemonized engine dies with process.


app = FastAPI(
    title="Gujarati Font Converter",
    version=__version__,
    description="Self-hosted REST API for Unicode ↔ TeraFont Trilochan with OCR.",
    lifespan=lifespan,
)

# CORS: by default allow same-origin; admins can override with env var
_origins = os.environ.get("CORS_ALLOW_ORIGINS", "").split(",") if os.environ.get("CORS_ALLOW_ORIGINS") else []
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


# ─────────────────────────────────────────────────────────────────────
# Request/response models
# ─────────────────────────────────────────────────────────────────────

class ConvertRequest(BaseModel):
    text: str


class ConvertResponse(BaseModel):
    text: str


class ExportRequest(BaseModel):
    content: str
    filename: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────
# Health / capabilities
# ─────────────────────────────────────────────────────────────────────

@app.get("/api/version")
def version():
    return {"version": __version__}


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": __version__,
        "ocr": _engine is not None,
        "ocr_error": _engine_error,
    }


@app.get("/api/capabilities")
def capabilities():
    return {
        "ocr": _engine is not None,
        "docx": _DOCS_AVAILABLE and _docs.docx_available(),
        "pdf": _DOCS_AVAILABLE and _docs.pdf_available(),
    }


# ─────────────────────────────────────────────────────────────────────
# Conversion
# ─────────────────────────────────────────────────────────────────────

@app.post("/api/convert/unicode-to-tera", response_model=ConvertResponse)
def api_unicode_to_tera(req: ConvertRequest):
    return ConvertResponse(text=convert_unicode_to_tera(req.text or ""))


@app.post("/api/convert/tera-to-unicode", response_model=ConvertResponse)
def api_tera_to_unicode(req: ConvertRequest):
    return ConvertResponse(text=convert_tera_to_unicode(req.text or ""))


# ─────────────────────────────────────────────────────────────────────
# File upload helpers
# ─────────────────────────────────────────────────────────────────────

async def _save_upload(upload: UploadFile, suffix: str = "") -> str:
    """Stream an upload to a temp file. Returns the path."""
    if not suffix and upload.filename:
        suffix = Path(upload.filename).suffix
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="gconv-")
    try:
        with os.fdopen(fd, "wb") as f:
            while chunk := await upload.read(1024 * 1024):  # 1 MiB chunks
                f.write(chunk)
    except Exception:
        os.unlink(path)
        raise
    return path


# ─────────────────────────────────────────────────────────────────────
# Document import (txt / docx)
# ─────────────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    """Accept .txt or .docx, return extracted text."""
    suffix = Path(file.filename or "").suffix.lower()
    path = await _save_upload(file, suffix=suffix)
    try:
        if suffix == ".docx":
            if not _DOCS_AVAILABLE or not _docs.docx_available():
                raise HTTPException(503, "DOCX support not installed on server")
            return {"text": _docs.read_docx(path), "source": "docx"}
        # default: treat as utf-8 text
        with open(path, "r", encoding="utf-8") as f:
            return {"text": f.read(), "source": "text"}
    except UnicodeDecodeError:
        raise HTTPException(400, "File is not valid UTF-8 text")
    except Exception as e:
        logger.exception("upload failed")
        raise HTTPException(500, str(e))
    finally:
        os.unlink(path)


# ─────────────────────────────────────────────────────────────────────
# Document export (docx / pdf)
# ─────────────────────────────────────────────────────────────────────

@app.post("/api/export/docx")
def export_docx(req: ExportRequest):
    if not _DOCS_AVAILABLE or not _docs.docx_available():
        raise HTTPException(503, "DOCX support not installed on server")
    fd, path = tempfile.mkstemp(suffix=".docx", prefix="gconv-out-")
    os.close(fd)
    try:
        _docs.write_docx(path, req.content or "")
        filename = req.filename or "output.docx"
        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
            background=_unlink_when_done(path),
        )
    except Exception as e:
        os.unlink(path)
        raise HTTPException(500, str(e))


@app.post("/api/export/pdf")
def export_pdf(req: ExportRequest):
    if not _DOCS_AVAILABLE or not _docs.pdf_available():
        raise HTTPException(503, "PDF support not installed on server")
    fd, path = tempfile.mkstemp(suffix=".pdf", prefix="gconv-out-")
    os.close(fd)
    try:
        _docs.write_pdf(path, req.content or "")
        filename = req.filename or "output.pdf"
        return FileResponse(
            path,
            media_type="application/pdf",
            filename=filename,
            background=_unlink_when_done(path),
        )
    except Exception as e:
        os.unlink(path)
        raise HTTPException(500, str(e))


def _unlink_when_done(path: str):
    """Return a BackgroundTask that deletes `path` after the response is sent."""
    from fastapi import BackgroundTasks  # noqa: F401 — import for typing
    from starlette.background import BackgroundTask
    return BackgroundTask(lambda: os.path.exists(path) and os.unlink(path))


# ─────────────────────────────────────────────────────────────────────
# OCR
# ─────────────────────────────────────────────────────────────────────

@app.post("/api/ocr/image")
async def ocr_image(file: UploadFile = File(...)):
    if _engine is None:
        raise HTTPException(503, _engine_error or "OCR engine not available")
    suffix = Path(file.filename or "").suffix.lower() or ".png"
    path = await _save_upload(file, suffix=suffix)
    try:
        from PIL import Image
        with Image.open(path) as img:
            preprocessed = preprocess_for_ocr(img)
        result = _engine.recognize(preprocessed)
        return result
    except Exception as e:
        logger.exception("ocr_image failed")
        raise HTTPException(500, str(e))
    finally:
        os.unlink(path)


@app.post("/api/ocr/pdf")
async def ocr_pdf(file: UploadFile = File(...), dpi: int = 300):
    """Synchronous PDF OCR. For very large PDFs run behind a reverse proxy
    with a longer timeout. (Async job queue is on the roadmap.)"""
    if _engine is None:
        raise HTTPException(503, _engine_error or "OCR engine not available")
    if not _OCR_AVAILABLE:
        raise HTTPException(503, "PDF rendering not available")

    path = await _save_upload(file, suffix=".pdf")
    try:
        pages_out = []
        combined = []
        for page_num, image in render_pages(path, dpi=dpi):
            # Prefer the digital text layer when present
            layer = extract_text_layer(path, page_num - 1)
            if layer and layer.strip():
                pages_out.append({"page": page_num, "text": layer.strip(), "source": "text_layer"})
                combined.append(layer.strip())
                continue
            preprocessed = preprocess_for_ocr(image)
            result = _engine.recognize(preprocessed)
            txt = result.get("text", "")
            pages_out.append({
                "page": page_num,
                "text": txt,
                "confidence": result.get("confidence", 0),
                "source": "ocr",
            })
            if txt:
                combined.append(txt)
        return {
            "text": "\n\n".join(combined),
            "pages": pages_out,
            "total_pages": len(pages_out),
        }
    except Exception as e:
        logger.exception("ocr_pdf failed")
        raise HTTPException(500, str(e))
    finally:
        os.unlink(path)


@app.post("/api/ocr/pdf-info")
async def ocr_pdf_info(file: UploadFile = File(...)):
    if not _OCR_AVAILABLE:
        raise HTTPException(503, "PDF support not available")
    path = await _save_upload(file, suffix=".pdf")
    try:
        return get_pdf_info(path)
    finally:
        os.unlink(path)


# ─────────────────────────────────────────────────────────────────────
# Static web UI (mounted last so /api/* takes priority)
# ─────────────────────────────────────────────────────────────────────

_ui_dir = Path(__file__).parent / "ui"
if _ui_dir.exists():
    app.mount("/", StaticFiles(directory=str(_ui_dir), html=True), name="ui")


# ─────────────────────────────────────────────────────────────────────
# Dev entry point
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=False)
