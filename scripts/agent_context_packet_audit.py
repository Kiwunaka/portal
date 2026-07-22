"""Audit prompt/context packets for prompt-cache friendly structure.

This is a lightweight harness for repo-owned agent prompts, external-model
packets, and work-order context bundles. It does not call any provider.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT_MAX_BYTES = 8192
ROOT_MAX_LINES = 120
ROUTER_MAX_BYTES = 12288
ROUTER_MAX_LINES = 240

DOCUMENT_CLASSES = (
    "CANONICAL",
    "ACTIVE_EXECUTION",
    "EVIDENCE",
    "HISTORICAL_REFERENCE",
    "OPERATOR_PLAYBOOK",
    "EXPERIMENTAL",
)

MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

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


def physical_line_count(text: str) -> int:
    return len(text.splitlines())


def parse_markdown_table(
    text: str,
    header: tuple[str, ...],
) -> list[dict[str, str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
        if cells != header:
            continue
        rows: list[dict[str, str]] = []
        for row_line in lines[index + 2 :]:
            if not row_line.startswith("|"):
                break
            values = tuple(cell.strip() for cell in row_line.strip("|").split("|"))
            if len(values) != len(header):
                break
            rows.append(dict(zip(header, values, strict=True)))
        return rows
    return []


def find_broken_local_markdown_links(
    root: Path,
    relative_paths: Iterable[str],
) -> list[str]:
    broken: list[str] = []
    workspace_prefix = root.resolve().as_posix().rstrip("/") + "/"
    for relative_path in relative_paths:
        document = (root / relative_path).resolve()
        text = document.read_text(encoding="utf-8")
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            normalized = target.replace("\\", "/")
            if normalized.startswith(workspace_prefix):
                candidate = root / normalized.removeprefix(workspace_prefix)
            elif re.match(r"^[A-Za-z]:/", normalized):
                candidate = Path(normalized)
            else:
                candidate = document.parent / normalized
            if not candidate.exists():
                broken.append(f"{relative_path} -> {target}")
    return sorted(set(broken))


def tracked_agents_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--", "AGENTS.md", ":(glob)**/AGENTS.md"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return sorted(set(completed.stdout.splitlines()))


def audit_platform_context(root: Path) -> list[str]:
    errors: list[str] = []
    agents_path = root / "AGENTS.md"
    router_path = root / "docs" / "developer" / "agent-context-map.md"
    registry_path = root / "docs" / "README.md"

    # Path.read_text() applies universal-newline normalization. Budget the
    # repository content, not the platform-specific CRLF checkout expansion on
    # Windows; the direct contract tests use the same representation.
    agents_text = agents_path.read_text(encoding="utf-8")
    router_text = router_path.read_text(encoding="utf-8")
    registry_text = registry_path.read_text(encoding="utf-8")

    if len(agents_text.encode("utf-8")) > ROOT_MAX_BYTES:
        errors.append(f"AGENTS.md exceeds {ROOT_MAX_BYTES} bytes")
    if physical_line_count(agents_text) > ROOT_MAX_LINES:
        errors.append(f"AGENTS.md exceeds {ROOT_MAX_LINES} lines")
    if len(router_text.encode("utf-8")) > ROUTER_MAX_BYTES:
        errors.append(f"agent-context-map.md exceeds {ROUTER_MAX_BYTES} bytes")
    if physical_line_count(router_text) > ROUTER_MAX_LINES:
        errors.append(f"agent-context-map.md exceeds {ROUTER_MAX_LINES} lines")

    for required in (
        "docs/developer/agent-context-map.md",
        "POKROV-app",
        "secrets",
        "archive",
        "evidence",
        "MANUAL_OWNER_TEST",
        "git status",
        "git diff",
    ):
        if required.casefold() not in agents_text.casefold():
            errors.append(f"AGENTS.md missing required semantic anchor: {required}")

    for forbidden in (
        "Current Release Gate Snapshot",
        "Must-Read Order",
        "Preferred model routing",
        "Copy rewrite prompt pattern",
        "Active Plans Quick Access",
    ):
        if forbidden.casefold() in agents_text.casefold():
            errors.append(f"AGENTS.md contains volatile section: {forbidden}")

    if "| Task | Read first | Inspect | Verify | Docs impact |" not in router_text:
        errors.append("agent-context-map.md lacks task router table")
    if "| Class | Owner | Document | Review state |" not in registry_text:
        errors.append("docs/README.md lacks registry table")
    if tracked_agents_files(root) != ["AGENTS.md"]:
        errors.append("tracked platform AGENTS.md set is not root-only")
    errors.extend(
        find_broken_local_markdown_links(
            root,
            ("AGENTS.md", "docs/README.md", "docs/developer/agent-context-map.md"),
        )
    )
    return errors


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
    parser.add_argument("files", nargs="*", type=Path, help="Prompt packet files to audit.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--min-cacheable-tokens", type=int, default=1024, help="Warn below this stable-prefix token estimate.")
    parser.add_argument(
        "--platform-context-root",
        type=Path,
        help="Audit the platform AGENTS/router/registry contract.",
    )
    args = parser.parse_args(argv)

    if bool(args.files) == bool(args.platform_context_root):
        parser.error("provide packet files or --platform-context-root, not both")

    if args.platform_context_root:
        errors = audit_platform_context(args.platform_context_root.resolve())
        if args.json:
            print(json.dumps({"errors": errors}, ensure_ascii=False, indent=2))
        else:
            status = "PASS" if not errors else "FAIL"
            print(f"{status} platform-context")
            for error in errors:
                print(f"  {error}")
        return 0 if not errors else 1

    results = [audit_file(path, args.min_cacheable_tokens) for path in args.files]

    if args.json:
        print(json.dumps([asdict(result) for result in results], ensure_ascii=False, indent=2))
    else:
        print_text_report(results)

    return 0 if all(result.passed for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
