# Gujarati Font Converter

> Convert Gujarati text between **Unicode** (Shruti / Noto) and **TeraFont Trilochan** — instantly, offline, with optional OCR for scanned images and PDFs.

A modern desktop app (**Windows · macOS · Linux**) and standalone web page for the Gujarati legal-document community. Built around the actual TeraFont Trilochan keyboard layout and verified against real legal documents with **133 golden word-level tests** locked in.

---

## ✨ Features

- ⚡ **Instant conversion** — Unicode ↔ TeraFont Trilochan, both directions
- 📄 **No word limit** — handles full legal documents
- 🔒 **100 % private** — runs entirely on your computer, nothing uploaded
- 📦 **Works offline** — once installed, no internet needed
- 📝 **DOCX import + export** — open Word documents, save with TeraFont applied
- 📕 **PDF export** with TeraFont Trilochan embedded
- 🖼️ **OCR from images** *(full build)* — extract Gujarati text from photos/scans
- 📚 **OCR from PDFs** *(full build)* — multi-page with text-layer fast-path
- 📁 **Batch folder OCR** *(full build)* — point at a folder of images
- ⌨️ **CLI mode** — `gujarati-converter --to-tera input.txt -o output.txt`
- 🌓 **Dark / light themes** with smooth transitions
- 🔍 **Find & Replace**, drag-and-drop, keyboard shortcuts, live stats
- 🎯 **Accurate** — extensive golden-test suite based on actual legal documents

---

## 📥 Download (for end users)

Grab the latest from **[Releases](../../releases)**:

| Platform | File | What it is |
|----------|------|------------|
| **Windows** | `GujaratiConverterSetup.exe` | Installer — recommended |
| **Windows** | `GujaratiConverter-windows-*.zip` | Portable — extract anywhere, run the `.exe` |
| **macOS** | `GujaratiConverter-macos-*.zip` | Unsigned — see macOS workaround below |
| **Linux** | `GujaratiConverter-linux-*.tar.gz` | Requires GTK 3 + WebKit2; extract and run |

**Install (Windows):**
1. Download the `.exe`.
2. Double-click → "Next → Next → Finish".
3. Launch from Start Menu or Desktop shortcut.

> **Windows SmartScreen warning:** the build is unsigned (signing costs ~$200/yr — skipped for a free project). Click **More info → Run anyway**. The app runs entirely on your machine — no data is sent anywhere.

**macOS users:** the build is unsigned, so Gatekeeper blocks the embedded Python dylib with *"library load disallowed by system policy"*. Strip the quarantine attribute once:

```bash
unzip GujaratiConverter-macos-*.zip
xattr -dr com.apple.quarantine GujaratiConverter/
./GujaratiConverter/GujaratiConverter
```

(Real fix requires a paid Apple Developer cert — skipped on a free project.)

---

## 🌐 Web version (no install)

The same UI is hosted on **GitHub Pages**: see the link in the repo sidebar, or run locally:

```bash
git clone https://github.com/ankitpipalia/terafont-trilochan-converter.git
cd terafont-trilochan-converter/app/ui
python3 -m http.server 8080
# Open http://localhost:8080
```

Conversion works; OCR/PDF/DOCX *export* don't (they need the Python backend).

---

## ⌨️ CLI mode

The installed `.exe` also works as a command-line tool. Useful for scripting and batch jobs:

```bash
# Unicode → TeraFont
gujarati-converter --to-tera input.txt -o output.txt
gujarati-converter --to-tera --stdin < input.txt > output.txt
echo "ગુજરાત" | gujarati-converter --to-tera --stdin

# TeraFont → Unicode
gujarati-converter --to-unicode input.txt -o output.txt

# Version check
gujarati-converter --version
```

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
# Expect: 133 passed, 7 xfailed
```

The 7 `xfailed` tests document a known limitation: TeraFont → Unicode round-trip is fundamentally lossy (e.g., the letter `h` could be either ASCII `h` or Gujarati `ઝ`). Treat reverse conversion as best-effort, not lossless. See `docs/ARCHITECTURE.md`.

### Run tests in Docker (no local Python required)

```bash
docker compose run --rm test
```

---

## 🚢 Cutting a release

Releases are **fully automated**. GitHub Actions watches `pyproject.toml` — bump the version, push, and a complete cross-platform release is built and published:

```bash
# 1. Bump the version in pyproject.toml (e.g., 0.1.0 → 0.2.0)
vim pyproject.toml

# 2. Commit + push to main
git commit -am "release: v0.2.0"
git push origin main
```

What happens next, end-to-end (~3–4 minutes):

| Step | Where |
|------|-------|
| `check-version` reads `pyproject.toml`, sees `v0.2.0` is a new tag | Ubuntu runner |
| Parallel builds: Windows installer + .zip, macOS .zip, Linux .tar.gz | 3 runners |
| Tests run on every platform (must stay green) | each runner |
| Release `v0.2.0` is published with all 4 artifacts attached | GitHub |
| Tag `v0.2.0` is created automatically pointing at your commit | GitHub |

**No release wanted?** If the version is the same as the latest tag, the workflow short-circuits at `check-version` and skips all build jobs. So docs-only commits and refactors are free.

### Manual / fallback ways to trigger a release

```bash
# Force a build at the current pyproject.toml version, even if tag exists
gh workflow run release.yml -f force_release=true

# Or push a tag explicitly (e.g., for hotfix from a previous commit)
git tag v0.2.1 <sha>
git push origin v0.2.1
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
