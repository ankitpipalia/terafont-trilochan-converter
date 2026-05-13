"""
Gujarati Converter Desktop — Entry point.

Launches a pywebview window hosting the existing web UI (index.html)
and exposes the converter API for JS↔Python communication.

Usage:
    python -m app.main
"""

import os
import sys
import webview

from app.api import API


def _resolve_base_dir():
    """Resolve the base directory for UI assets.

    Handles both development mode and PyInstaller --onedir bundles.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller bundle — _MEIPASS points to the extracted dir
        return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.abspath(__file__))


def create_window():
    api = API()

    base_dir = _resolve_base_dir()
    ui_dir = os.path.join(base_dir, "ui")
    index_path = os.path.join(ui_dir, "index.html")

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"UI files not found at {index_path}")

    window = webview.create_window(
        title="Gujarati Font Converter",
        url=f"file://{index_path}",
        js_api=api,
        width=1280,
        height=860,
        min_size=(960, 640),
        background_color="#0f0f1a",
    )

    # Store window ref for cross-platform JS evaluation
    api.set_window(window)

    return window


def main():
    window = create_window()
    try:
        webview.start()
    except Exception as e:
        print(f"Error starting app: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
