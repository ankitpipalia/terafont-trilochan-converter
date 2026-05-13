# Architecture

A static web UI hosted inside a native Windows desktop shell, with a Python backend that adds OCR / PDF / file-dialog capabilities.

## High-level diagram

```
┌─────────────────────────────────────────────────────────┐
│  Native Window  (PyWebView + WebView2 on Windows)       │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Web UI  (app/ui/)                                │  │
│  │  ─ index.html · style.css                         │  │
│  │  ─ converter.js   (UI, conversion fallback)       │  │
│  │  ─ ocr.js         (OCR/PDF buttons + bridge)      │  │
│  └────────────────────┬──────────────────────────────┘  │
│                       │ pywebview JS ↔ Python bridge    │
│                       ▼                                 │
│  ┌───────────────────────────────────────────────────┐  │
│  │  app/api.py — exposed methods                     │  │
│  │  ─ convert_unicode_to_tera / convert_tera_to_unicode │
│  │  ─ pick_image / pick_pdf / pick_folder / save_text│  │
│  │  ─ ocr_image / ocr_pdf / ocr_folder               │  │
│  │  ─ get_settings / set_settings                    │  │
│  └─────────┬───────────────┬───────────────┬─────────┘  │
│            │               │               │            │
│            ▼               ▼               ▼            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ converter.py │ │ ocr/         │ │ pdf_utils.py │    │
│  │              │ │  ├ engine.py │ │ (PyMuPDF)    │    │
│  │ mapping      │ │  ├ paddle    │ │              │    │
│  │ tables +     │ │  ├ tesseract │ │ render_pages │    │
│  │ 6 functions  │ │  └ preprocess│ │ text_layer   │    │
│  └──────────────┘ └──────┬───────┘ └──────────────┘    │
│                          │                              │
│                  ┌───────▼────────┐                     │
│                  │ workers.py     │                     │
│                  │ (thread pool)  │                     │
│                  └────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

## Conversion logic — `app/converter.py`

The converter is built around **four** lookup tables and a syllable-aware main loop:

1. **`unicode_to_tera_map`** — single-character mappings (vowels, consonants, matras, digits, Gujarati punctuation only — ASCII passes through).
2. **`half_forms`** — consonants whose **half-form** glyph is used when followed by `્` + consonant. Verified from examples (ન→g, સ→:, લ→<, etc.).
3. **`conjunct_patterns`** — special-shape ligatures that aren't derivable from the rules (ક્ષ→1F, જ્ઞ→7, ત્ર→+, શ્ર→z, રૂ→~, જી→Ò). Sorted longest-first; checked before everything else.
4. **`retroflex`** — the 5 retroflex consonants (ટ ઠ ડ ઢ ણ) that use `=` instead of `|` for subscript-r.

### Cluster rule (`encode_cluster`)

When the main loop sees `c1 + ્ + c2`:

| Condition | Output |
|-----------|--------|
| `c2 == 'ર'` AND `c1` is retroflex | `tera(c1) + '='` |
| `c2 == 'ર'` | `tera(c1) + '|'` |
| `c1` has a half-form | `halfForm(c1) + tera(c2)` |
| Otherwise | `tera(c1) + tera(c2)` (virama dropped) |

### Special handling

- **Short-i (`િ`)** is placed visually *before* the consonant. The main loop emits `l` before the cluster glyphs.
- **Reph (`ર્`)** is emitted as `"` *after* the full syllable. `preprocess_reph` replaces `ર + ્ + consonant` with a private-use marker; the main loop scans the syllable and appends `"` at the end.
- **Orphan `્ + ર`** in 3-consonant clusters like `સ્ત્ર` emits `=` (the subscript-r continuation glyph).

`convert_cluster()` is a helper that mirrors the main loop and is called from inside the reph handler.

## UI design

Same `app/ui/` tree powers **both** the standalone web page and the desktop app:

- In the browser: pure JS conversion (uses `converter.js`'s in-browser logic). OCR / PDF buttons show a "requires desktop" message.
- In the desktop app: `window.pywebview.api.*` is available. OCR / PDF / file dialogs are routed to Python; conversion can use either path (Python is the source of truth).

## OCR pipeline

```
file path  →  PIL Image  →  preprocess  →  engine.recognize()  →  text dict
                              │
                              ├─ grayscale
                              ├─ median blur
                              ├─ adaptive threshold
                              └─ deskew (Hough lines)
```

- **PaddleOCR** is the primary engine (best Gujarati accuracy per the [benchmark](https://ijrpr.com/uploads/V6ISSUE10/IJRPR53627.pdf): 92 % word accuracy vs Tesseract's 76 %).
- **Tesseract** is the fallback if PaddleOCR fails to initialize. Uses `pytesseract` with `lang="guj"` and a bundled `guj.traineddata`.
- The engine is **pre-warmed** in a background thread at startup (`api.py:_warm_engine`) so the first user action feels instant.

## PDF pipeline

1. `pdf_utils.render_pages(pdf_path, dpi=300)` yields `(page_num, PIL.Image)` tuples via PyMuPDF.
2. For each page, `pdf_utils.extract_text_layer(...)` checks for an embedded text layer (digital PDFs) — if present, skip OCR for that page.
3. Otherwise, preprocess + OCR.
4. Combined output is joined with `\n\n` between pages.

Progress is reported back to the UI via `window._onOCRProgress(jobId, progress, current, total)`.

## Threading

`workers.OCRWorker` wraps a `ThreadPoolExecutor`. Each OCR call (PDF or folder) becomes a future. Progress + completion callbacks invoke `window.evaluate_js(...)` to call back into JS — the bridge is cross-platform via `app/main.py`'s `api.set_window(window)`.

## Build & distribution

- **Development:** `python -m app.main`
- **CI tests:** `pytest -v` — 120 golden tests, runs in <1s
- **Windows installer:** PyInstaller (`build/pyinstaller-slim.spec` or `build/pyinstaller.spec`) → Inno Setup (`build/installer-slim.iss` or `build/installer.iss`)
- **Triggered by:** pushing a `v*` tag — `.github/workflows/release.yml` does the rest

See [`HANDOFF.md`](HANDOFF.md) for the deep history of how the mapping tables were reverse-engineered.
