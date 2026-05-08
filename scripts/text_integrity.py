from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_SUFFIXES = {".css", ".html", ".js", ".jsx", ".json", ".md", ".ts", ".tsx"}

# UTF-8 Russian text decoded through a single-byte codepage often becomes a
# compact run of Cyrillic capital Er/Es pairs, for example the common
# escaped-codepoint form of "POKROV" after a bad decode.
MOJIBAKE_MARKERS = (
    "\u0420\u00a0\u0420\u040b\u0420\u00a0\u0421\u201c",
    "\u0420\u040e\u0420\u0453",
)

MOJIBAKE_PATTERNS = (
    re.compile(r"(?:[\u0420\u0421][^\s]){4,}"),
    re.compile(r"\ufffd"),
)

SKIP_PARTS = {
    ".cache",
    ".dart_tool",
    ".git",
    ".next",
    ".pytest_cache",
    "archive",
    "archive-artifacts",
    "audit-artifacts",
    "build",
    "coverage",
    "dist",
    "flat-docs",
    "node_modules",
    "out",
    "root-guides",
    "test-results",
}


@dataclass(frozen=True)
class TextIntegrityIssue:
    path: Path
    marker: str
    line: int
    snippet: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line}: possible mojibake marker {self.marker!r}: {self.snippet}"


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)


def iter_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists() or _is_skipped(path):
            continue
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                yield path
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix.lower() in TEXT_SUFFIXES and not _is_skipped(child):
                yield child


def scan_mojibake(paths: Iterable[Path]) -> list[TextIntegrityIssue]:
    issues: list[TextIntegrityIssue] = []
    for path in iter_text_files(paths):
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for marker in MOJIBAKE_MARKERS:
                if marker in line:
                    issues.append(
                        TextIntegrityIssue(
                            path=path,
                            marker=marker,
                            line=line_number,
                            snippet=line.strip()[:180],
                        )
                    )
                    break
            else:
                marker = None
            if marker:
                continue
            for pattern in MOJIBAKE_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        TextIntegrityIssue(
                            path=path,
                            marker=pattern.pattern,
                            line=line_number,
                            snippet=line.strip()[:180],
                        )
                    )
                    break
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan active text files for likely mojibake.")
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to scan.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    paths = args.paths or [
        root / "webapp" / "src",
        root / "marketing" / "src",
        root / "shared",
        root / "copy",
        root / "docs" / "design",
    ]
    issues = scan_mojibake(paths)
    for issue in issues:
        print(issue.format(root))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
