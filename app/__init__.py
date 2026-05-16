"""Gujarati Converter Desktop — package init.

Sets up centralized logging on import. Writes to a rotating file in
%APPDATA%/GujaratiConverter/logs/ on Windows, ~/.gujarati_converter/logs/
elsewhere. Also mirrors to stderr at INFO level.
"""

import logging
import logging.handlers
import os
import sys

__version__ = "0.1.0"


def _log_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.path.expanduser("~")
    return os.path.join(base, "GujaratiConverter", "logs")


def log_dir() -> str:
    """Return the directory where log files are written. Public helper."""
    return _log_dir()


def _configure_logging() -> None:
    log_directory = _log_dir()
    try:
        os.makedirs(log_directory, exist_ok=True)
    except OSError:
        # Read-only home? Just log to stderr.
        log_directory = None

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_directory:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                os.path.join(log_directory, "app.log"),
                maxBytes=2_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(logging.DEBUG)
            handlers.append(file_handler)
        except OSError:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,  # override anything set earlier
    )


_configure_logging()
