#!/usr/bin/env python3
"""Search text inside files that match one or more glob-style patterns.

Examples:
  python search_files.py "TODO" "*.txt" "*.cpp"
  python search_files.py "main" "src/*.py" "*.md" --ignore-case
"""

from __future__ import annotations

import argparse
import fnmatch
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search file contents for a query inside files matching patterns."
    )
    parser.add_argument(
        "query",
        help="Text to search for inside matching files.",
    )
    parser.add_argument(
        "patterns",
        nargs="+",
        help='One or more glob patterns (for example: "*.txt" "*.cpp").',
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to search from (default: current directory).",
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Case-insensitive content search.",
    )
    return parser.parse_args()


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def matches_pattern(path: Path, root: Path, patterns: list[str]) -> bool:
    rel_path = path.relative_to(root).as_posix()
    filename = path.name

    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern) or fnmatch.fnmatch(rel_path, pattern):
            return True
    return False


def search_file(path: Path, query: str, ignore_case: bool) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []

    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line_num, line in enumerate(handle, start=1):
                haystack = line.lower() if ignore_case else line
                needle = query.lower() if ignore_case else query
                if needle in haystack:
                    matches.append((line_num, line.rstrip("\n")))
    except OSError as exc:
        print(f"WARN: could not read {path}: {exc}")

    return matches


def main() -> int:
    args = parse_args()
    root = Path(args.root).resolve()

    if not root.exists() or not root.is_dir():
        print(f"ERROR: root path does not exist or is not a directory: {root}")
        return 1

    total_matches = 0
    matched_files = 0

    for path in iter_files(root):
        if not matches_pattern(path, root, args.patterns):
            continue

        line_matches = search_file(path, args.query, args.ignore_case)
        if not line_matches:
            continue

        matched_files += 1
        for line_num, text in line_matches:
            rel = path.relative_to(root).as_posix()
            print(f"{rel}:{line_num}: {text}")
            total_matches += 1

    if total_matches == 0:
        print("No matches found.")

    print(f"\nMatched files: {matched_files}")
    print(f"Total matches: {total_matches}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
