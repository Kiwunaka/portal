from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_SUFFIXES = {".css", ".html", ".js", ".jsx", ".json", ".md", ".ts", ".tsx"}

MOJIBAKE_MARKERS = (
    "Р Сџ",
    "Р Сњ",
    "Р РЋ",
    "Р С›",
    "Р вЂ”",
    "Р С™",
    "Р Т‘",
    "Р Вµ",
    "Р С•",
    "РЎРѓ",
    "РЎвЂљ",
    "РЎР‚",
    "РЎвЂ№",
    "РЎРЏ",
    "РЎР‹",
    "РЎвЂ°",
    "РІР‚",
    "Р’В·",
    "вЂ",
    "Гђ",
    "Г‘",
    "пїЅ",
)

MOJIBAKE_PATTERNS = (
    # UTF-8 Russian decoded through a single-byte codepage often appears as
    # long alternating Р*/С* fragments, for example "РџРѕРґ...".
    re.compile(r"(?:Р.|С.|вЂ|В·){4,}"),
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
