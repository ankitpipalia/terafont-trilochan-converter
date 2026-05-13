# Gujarati Font Converter

> Convert Gujarati text between **Unicode** (Shruti / Noto) and **TeraFont Trilochan** — instantly, offline, with optional OCR for scanned images and PDFs.

A modern desktop app (Windows) and standalone web page for the Gujarati legal-document community. Built around the actual TeraFont Trilochan keyboard layout and verified against real legal documents with **120 golden word-level tests** locked in.

---

## ✨ Features

- ⚡ **Instant conversion** — Unicode ↔ TeraFont Trilochan, both directions
- 📄 **No word limit** — handles full legal documents
- 🔒 **100 % private** — runs entirely on your computer, nothing uploaded
- 📦 **Works offline** — once installed, no internet needed
- 🖼️ **OCR from images** — extract Gujarati text from photos / scans *(full build only)*
- 📚 **OCR from PDFs** — multi-page documents with text-layer fast-path *(full build only)*
- 📁 **Batch folder OCR** — point at a folder of images, get all the text *(full build only)*
- 🌓 **Dark / light themes** with smooth transitions
- 🔍 **Find & Replace**, drag-and-drop, keyboard shortcuts, live stats
- 🎯 **Accurate** — extensive golden-test suite based on actual legal documents

---

## 📥 Download (for end users)

Grab the latest installer from **[Releases](../../releases)**:

| File | What it is |
|------|-----------|
| `GujaratiConverterSetup.exe` | Windows installer (Slim, ~80 MB). Conversion only — no OCR. |
| `GujaratiConverterSetup-Full.exe` | Windows installer (Full, ~400 MB). Includes OCR engine. |
| `GujaratiConverter-portable.zip` | Portable version. Extract anywhere, run the `.exe`. No installation needed. |

**Install:**
1. Download the `.exe`.
2. Double-click → "Next → Next → Finish".
3. Launch from Start Menu or Desktop shortcut.

> **Note:** Windows SmartScreen may show "Windows protected your PC" the first time because the app isn't code-signed (signing costs ~$200/yr — skipped for a free project). Click **More info → Run anyway**.

---

## 🚀 Quick start (web version)

Don't want to install anything? The same UI works in any modern browser:

```bash
git clone https://github.com/<your-user>/gujarati-font-converter.git
cd gujarati-font-converter/app/ui
python3 -m http.server 8080
# Open http://localhost:8080
```

(Conversion works; OCR/PDF do not, because they require the Python backend.)

---

## ⌨️ Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Convert |
| `Ctrl + O` | Upload `.txt` file |
| `Ctrl + S` | Download output |
| `Ctrl + P` | Print |
| `Ctrl + F` | Find & Replace |
| `Ctrl + Shift + C` | Copy output |
| `Ctrl + Shift + I` | OCR an image |
| `Ctrl + K` | Swap input ↔ output |
| `Ctrl + /` | Toggle theme |
| `Esc` | Clear / close dialog |
| `?` | Show shortcuts |

---

## 🛠 Developer setup

### Prerequisites

- Python **3.10** or **3.11** (3.12+ has wheel issues with PaddleOCR; 3.14 works locally but isn't recommended for builds)
- (For full build) ~2 GB free disk for PaddleOCR models

### Install (slim — fast, no OCR)

```bash
git clone https://github.com/<your-user>/gujarati-font-converter.git
cd gujarati-font-converter
python -m venv .venv
source .venv/bin/activate           # macOS / Linux
# .venv\Scripts\activate            # Windows

pip install -r requirements-slim.txt
python -m app.main
```

### Install (full — includes OCR)

```bash
pip install -r requirements.txt
python -m app.main
```

### Run tests

```bash
pip install pytest
pytest -v
# Expect: 120 passed
```

### Run tests in Docker (no local Python required)

```bash
docker compose run --rm test
```

---

## 🏗 Building Windows installers

The recommended path is **GitHub Actions** — push a tag, the workflow builds installers on a Windows runner, and attaches them to a GitHub Release:

```bash
git tag v0.1.0
git push origin v0.1.0
# → check the Actions tab, then Releases
```

### Building locally on Windows (advanced)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-slim.txt
pip install pyinstaller

# Build the .exe directory
pyinstaller build/pyinstaller-slim.spec --noconfirm

# Wrap with Inno Setup (download from https://jrsoftware.org/isdl.php)
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer-slim.iss
# → produces dist/GujaratiConverterSetup.exe
```

---

## 📐 Architecture

See **[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)** for the full architecture.

Quick summary:

```
┌──────────────────────────────────────────────────────┐
│ Native window (PyWebView + WebView2 on Windows)      │
│ ┌──────────────────────────────────────────────────┐ │
│ │ Web UI (app/ui/) — same code as the web version  │ │
│ └──────────────────┬───────────────────────────────┘ │
│                    │ JS ↔ Python bridge              │
│                    ▼                                 │
│ ┌──────────────────────────────────────────────────┐ │
│ │ app/converter.py   — Conversion logic            │ │
│ │ app/ocr/           — PaddleOCR + Tesseract       │ │
│ │ app/pdf_utils.py   — PyMuPDF rendering           │ │
│ │ app/workers.py     — Background thread pool      │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

Mapping tables live in [`app/converter.py`](app/converter.py); 120 golden tests in [`tests/test_converter.py`](tests/test_converter.py). For deep history of how the mapping was reverse-engineered see [`docs/HANDOFF.md`](docs/HANDOFF.md).

---

## 🤝 Contributing

Pull requests welcome. Before submitting:

1. `pytest -v` must pass 120/120.
2. If you change `app/converter.py`, add a golden test in `tests/test_converter.py`.
3. Don't commit your own example legal documents (anything in `examples/` is gitignored by default).

---

## 📜 License

MIT — see [`LICENSE`](LICENSE).

The bundled `TRILOCHA.TTF` font belongs to its respective owner and is included for rendering compatibility. If you own this font and want it removed, please open an issue.

---

## 🙏 Acknowledgements

- Built with [PyWebView](https://pywebview.flowrl.com/), [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), [PyMuPDF](https://pymupdf.readthedocs.io/), and [PyInstaller](https://pyinstaller.org/).
- Mapping table verified against manually-converted Gujarati legal documents.
- Thanks to the Gujarati community for keeping TeraFont alive in courts and government offices.
