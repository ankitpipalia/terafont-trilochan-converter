# -*- mode: python ; coding: utf-8 -*-
#
# SLIM build — no PaddleOCR, no PyMuPDF, no OpenCV.
# Produces a ~80 MB onedir distribution suitable for first-time release.
#
# Usage (from repo root):
#   pyinstaller build/pyinstaller-slim.spec --noconfirm \
#               --workpath build/_work --distpath dist
#
# Output: dist/GujaratiConverter/GujaratiConverter.exe

import os

# Resolve everything relative to the spec file itself so the build works
# regardless of which directory pyinstaller is invoked from.
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
PROJECT_ROOT = os.path.dirname(SPEC_DIR)

block_cipher = None

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'app', 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        # Bundle the entire UI folder. PyInstaller places these at
        # {_MEIPASS}/ui/ which app/main.py resolves at runtime.
        (os.path.join(PROJECT_ROOT, 'app', 'ui', 'index.html'), 'ui'),
        (os.path.join(PROJECT_ROOT, 'app', 'ui', 'style.css'), 'ui'),
        (os.path.join(PROJECT_ROOT, 'app', 'ui', 'converter.js'), 'ui'),
        (os.path.join(PROJECT_ROOT, 'app', 'ui', 'ocr.js'), 'ui'),
        (os.path.join(PROJECT_ROOT, 'app', 'ui', 'TRILOCHA.TTF'), 'ui'),
    ],
    hiddenimports=[
        # PyWebView platform backends are loaded dynamically
        'webview.platforms.edgechromium',
        'webview.platforms.mshtml',
        'webview.platforms.winforms',
        # docs.py loads these lazily; PyInstaller can't infer
        'docx',
        'docx.oxml.ns',
        'reportlab.pdfbase.ttfonts',
        'reportlab.lib.pagesizes',
        'reportlab.pdfgen.canvas',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Aggressively exclude unused libs to keep the bundle small.
        'matplotlib',
        'jupyter',
        'notebook',
        'IPython',
        'h5py',
        'scipy',
        'numpy',
        'pandas',
        'PIL.ImageQt',
        'cv2',
        'paddleocr',
        'paddle',
        'fitz',
        'pytesseract',
        'tkinter',
        'unittest',
        'setuptools',
        'pkg_resources',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GujaratiConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,                   # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=os.path.join(SPEC_DIR, 'version_info.txt'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GujaratiConverter',
)
