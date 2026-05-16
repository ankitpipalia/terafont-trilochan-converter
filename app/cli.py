"""Command-line interface for the Gujarati Converter.

Usage:
    gujarati-converter --to-tera input.txt -o output.txt
    gujarati-converter --to-unicode input.txt -o output.txt
    gujarati-converter --to-tera --stdin
    cat in.txt | gujarati-converter --to-tera
    gujarati-converter --version

If launched with no arguments, the GUI starts.
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

from app.converter import convert_unicode_to_tera, convert_tera_to_unicode

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gujarati-converter",
        description=(
            "Convert Gujarati text between Unicode and TeraFont Trilochan. "
            "Run without arguments to launch the GUI."
        ),
    )
    direction = p.add_mutually_exclusive_group(required=False)
    direction.add_argument("--to-tera", action="store_true",
                           help="Convert Unicode → TeraFont (default)")
    direction.add_argument("--to-unicode", action="store_true",
                           help="Convert TeraFont → Unicode")

    p.add_argument("input", nargs="?", default=None,
                   help="Input file path (use --stdin for piped input)")
    p.add_argument("-o", "--output", default=None,
                   help="Output file path (defaults to stdout)")
    p.add_argument("--stdin", action="store_true",
                   help="Read input from stdin")
    p.add_argument("--version", action="store_true",
                   help="Print version and exit")
    return p


def run(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.version:
        from app import __version__
        print(f"gujarati-converter {__version__}")
        return 0

    # Decide direction
    to_unicode = args.to_unicode and not args.to_tera

    # Read input
    if args.stdin:
        text = sys.stdin.read()
    elif args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                text = f.read()
        except OSError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
    else:
        # No input AND no --stdin → caller probably wants the GUI; signal
        # the entry point to fall through.
        return -1

    # Convert
    output = convert_tera_to_unicode(text) if to_unicode else convert_unicode_to_tera(text)

    # Write output
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
        except OSError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    rc = run()
    sys.exit(0 if rc < 0 else rc)


def has_cli_args() -> bool:
    """Return True if the command-line arguments look like CLI mode."""
    for arg in sys.argv[1:]:
        if arg in ("--to-tera", "--to-unicode", "--stdin", "--version", "-o", "--output"):
            return True
        if arg.startswith("-") and arg not in ("-h", "--help"):
            return True
        # Positional file argument
        if not arg.startswith("-"):
            return True
    return False
