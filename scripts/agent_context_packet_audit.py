"""Audit prompt/context packets for prompt-cache friendly structure.

This is a lightweight harness for repo-owned agent prompts, external-model
packets, and work-order context bundles. It does not call any provider.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


BREAKPOINT_RE = re.compile(
    r"(CACHE[_ -]?BREAKPOINT|DYNAMIC[_ -]?SUFFIX|BEGIN[_ -]?DYNAMIC|<dynamic\b|BLOCK E: DYNAMIC)",
    re.IGNORECASE,
)

DYNAMIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("timestamp", re.compile(r"\b\d{4}-\d{2}-\d{2}[T ][0-9]{2}:[0-9]{2}", re.IGNORECASE)),
    ("current-date", re.compile(r"\b(current date|today'?s date|last updated)\b|\bdate\s*:", re.IGNORECASE)),
    ("session-id", re.compile(r"\b(session[_ -]?id|conversation[_ -]?id|thread[_ -]?id)\b", re.IGNORECASE)),
    ("request-id", re.compile(r"\b(request[_ -]?id|trace[_ -]?id|span[_ -]?id|run[_ -]?id)\b", re.IGNORECASE)),
    ("uuid", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", re.IGNORECASE)),
    ("cwd", re.compile(r"\b(cwd|working directory|repo path)\s*[:=]", re.IGNORECASE)),
    ("git-status", re.compile(r"\b(git status|current branch|dirty files|untracked files)\b", re.IGNORECASE)),
    ("provider-secret", re.compile(r"\b(api[_ -]?key|bearer token|authorization: bearer|x-goog-api-key)\b", re.IGNORECASE)),
]


@dataclass
class Finding:
    line: int
    kind: str
    text: str


@dataclass
class AuditResult:
    path: str
    passed: bool
    total_token_estimate: int
    stable_prefix_token_estimate: int
    breakpoint_line: int | None
    findings: list[Finding]
    warnings: list[str]


def estimate_tokens(text: str) -> int:
    """Return a deliberately rough token estimate for lint thresholds."""
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def find_breakpoint(lines: list[str]) -> int | None:
    for index, line in enumerate(lines, start=1):
        if BREAKPOINT_RE.search(line):
            return index
    return None


def audit_text(path: str, text: str, min_cacheable_tokens: int = 1024) -> AuditResult:
    lines = text.splitlines()
    breakpoint_line = find_breakpoint(lines)
    stable_lines = lines[: breakpoint_line - 1] if breakpoint_line else lines
    stable_text = "\n".join(stable_lines)
    findings: list[Finding] = []

    for line_number, line in enumerate(stable_lines, start=1):
        for kind, pattern in DYNAMIC_PATTERNS:
            if pattern.search(line):
                findings.append(Finding(line=line_number, kind=kind, text=line.strip()[:180]))

    warnings: list[str] = []
    stable_tokens = estimate_tokens(stable_text)
    if stable_tokens < min_cacheable_tokens:
        warnings.append(
            f"stable prefix is about {stable_tokens} tokens; OpenAI prompt caching starts at 1024+ tokens"
        )
    if breakpoint_line is None:
        warnings.append("no explicit cache breakpoint marker found; dynamic suffix boundary is implicit")

    return AuditResult(
        path=path,
        passed=not findings,
        total_token_estimate=estimate_tokens(text),
        stable_prefix_token_estimate=stable_tokens,
        breakpoint_line=breakpoint_line,
        findings=findings,
        warnings=warnings,
    )


def audit_file(file_path: Path, min_cacheable_tokens: int) -> AuditResult:
    text = file_path.read_text(encoding="utf-8")
    return audit_text(str(file_path), text, min_cacheable_tokens=min_cacheable_tokens)


def print_text_report(results: list[AuditResult]) -> None:
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.path}")
        print(f"  stable_prefix_tokens~{result.stable_prefix_token_estimate}")
        print(f"  total_tokens~{result.total_token_estimate}")
        print(f"  breakpoint_line={result.breakpoint_line or 'none'}")
        for warning in result.warnings:
            print(f"  warning: {warning}")
        for finding in result.findings:
            print(f"  line {finding.line}: {finding.kind}: {finding.text}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit prompt/context packets for prompt-cache friendly structure.")
    parser.add_argument("files", nargs="+", type=Path, help="Prompt packet files to audit.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--min-cacheable-tokens", type=int, default=1024, help="Warn below this stable-prefix token estimate.")
    args = parser.parse_args(argv)

    results = [audit_file(path, args.min_cacheable_tokens) for path in args.files]

    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        print_text_report(results)

    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
