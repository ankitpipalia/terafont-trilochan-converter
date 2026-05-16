"""User-settings persistence with schema + safe defaults.

Settings live at:
    %APPDATA%/GujaratiConverter/settings.json   (Windows)
    ~/GujaratiConverter/settings.json           (macOS / Linux)

Unknown keys are silently dropped on load; missing keys fall back to defaults.
Corrupt JSON is logged and replaced with defaults.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

logger = logging.getLogger(__name__)


DEFAULT_SETTINGS: dict[str, Any] = {
    "engine": "paddle",          # OCR engine: "paddle" | "tesseract"
    "dpi": 300,                  # PDF render DPI (150 / 300 / 600)
    "theme": "dark",             # "dark" | "light"
    "default_mode": "unicodeToTera",  # initial conversion direction
    "last_folder": None,         # remembered last open folder
    "recent_files": [],          # up to RECENT_FILES_MAX entries
    "ocr_lang": "guj",
    "auto_convert": True,
    "show_confidence": True,
}

RECENT_FILES_MAX = 10
VALID_ENGINES = {"paddle", "tesseract"}
VALID_THEMES = {"dark", "light"}
VALID_DPI = {150, 300, 600}
VALID_MODES = {"unicodeToTera", "teraToUnicode", "auto"}


def settings_path() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "GujaratiConverter", "settings.json")


def _coerce(loaded: dict[str, Any]) -> dict[str, Any]:
    """Merge `loaded` over defaults; drop unknown keys and invalid values."""
    out = dict(DEFAULT_SETTINGS)
    for key, default_value in DEFAULT_SETTINGS.items():
        if key not in loaded:
            continue
        value = loaded[key]
        # Type-check against the default; reject mismatched types.
        if not isinstance(value, type(default_value)) and default_value is not None:
            logger.warning("settings.%s: bad type, using default", key)
            continue
        # Whitelist enums
        if key == "engine" and value not in VALID_ENGINES:
            continue
        if key == "theme" and value not in VALID_THEMES:
            continue
        if key == "dpi" and value not in VALID_DPI:
            continue
        if key == "default_mode" and value not in VALID_MODES:
            continue
        if key == "recent_files":
            value = [str(p) for p in value if isinstance(p, str)][:RECENT_FILES_MAX]
        out[key] = value
    return out


def load() -> dict[str, Any]:
    path = settings_path()
    if not os.path.exists(path):
        return dict(DEFAULT_SETTINGS)
    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if not isinstance(loaded, dict):
            raise ValueError("settings file is not a JSON object")
        return _coerce(loaded)
    except (OSError, json.JSONDecodeError, ValueError) as e:
        logger.warning("settings load failed (%s) — using defaults", e)
        return dict(DEFAULT_SETTINGS)


def save(settings: dict[str, Any]) -> None:
    path = settings_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Validate before writing
        clean = _coerce(settings)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(clean, f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.error("settings save failed: %s", e)


def add_recent_file(path: str) -> dict[str, Any]:
    """Add a path to the recent-files list and return the new settings."""
    s = load()
    rec = [p for p in s.get("recent_files", []) if p != path]
    rec.insert(0, path)
    s["recent_files"] = rec[:RECENT_FILES_MAX]
    save(s)
    return s


def reset() -> dict[str, Any]:
    """Restore defaults and persist."""
    save(DEFAULT_SETTINGS)
    return dict(DEFAULT_SETTINGS)
