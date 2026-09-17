"""Command-line interface and machine-readable output."""

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .checker import check


def _escape(value: str, property_value: bool = False) -> str:
    value = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return value.replace(":", "%3A").replace(",", "%2C") if property_value else value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check repository-local Markdown links without network requests.")
    parser.add_argument("paths", nargs="*", help="Files or directories relative to --root (default: all)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root (default: working directory)")
    parser.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="Exclude root-relative source paths; repeatable")
    parser.add_argument("--format", choices=["text", "json", "github"], default="text")
    parser.add_argument("--version", action="version", version=f"docroute {__version__}")
    args = parser.parse_args(argv)
    try:
        report = check(args.root, args.paths, args.exclude)
    except (ValueError, OSError, RuntimeError) as exc:
        if args.format == "json":
            print(json.dumps({"schema_version": 1, "error": str(exc)}))
        else:
            print(f"docroute: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        for issue in report.issues:
            message = f"{issue.code}: {issue.message} ({issue.target})"
            if issue.suggestion:
                message += f"; did you mean {issue.suggestion}?"
            if args.format == "github":
                # Annotation paths must be relative to the Actions working directory.
                import os
                path = Path(os.path.relpath(args.root.resolve() / issue.file, Path.cwd())).as_posix()
                print(f"::error file={_escape(path, True)},line={issue.line}::{_escape(message)}")
            else:
                print(f"{issue.file}:{issue.line}: {message}")
        print(f"{report.files_checked} file(s), {report.links_checked} local link(s), "
              f"{report.links_skipped} external link(s) skipped, {len(report.issues)} issue(s)")
    return 1 if report.issues else 0
