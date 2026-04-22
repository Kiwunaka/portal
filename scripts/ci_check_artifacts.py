from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path)))


def _safe_resolve(path: Path) -> Path | None:
    try:
        return path.resolve(strict=False)
    except (OSError, RuntimeError):
        return None


def _is_within_repo_root(path: Path, repo_root: Path) -> bool:
    try:
        return os.path.commonpath([_path_key(path), _path_key(repo_root)]) == _path_key(repo_root)
    except ValueError:
        return False


def _iter_repo_tree(
    start_dir: Path,
    repo_root: Path,
    *,
    ignore_dirs: set[str] | None = None,
) -> Iterator[tuple[Path, list[str], list[str]]]:
    repo_root = repo_root.resolve()
    ignore_dirs = ignore_dirs or set()
    start_dir = start_dir.resolve()

    start_resolved = _safe_resolve(start_dir)
    if start_resolved is None or not _is_within_repo_root(start_resolved, repo_root):
        return

    visited_real_dirs = {_path_key(start_resolved)}
    stack = [start_dir]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                ordered_entries = sorted(entries, key=lambda entry: (entry.name.lower(), entry.name))
        except OSError:
            continue

        dir_names: list[str] = []
        file_names: list[str] = []
        children_to_scan: list[Path] = []

        for entry in ordered_entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    dir_names.append(entry.name)
                    if entry.name in ignore_dirs:
                        continue

                    child = Path(entry.path)
                    child_resolved = _safe_resolve(child)
                    if child_resolved is None or not _is_within_repo_root(child_resolved, repo_root):
                        continue

                    child_key = _path_key(child_resolved)
                    if child_key in visited_real_dirs:
                        continue

                    # Track real locations for every descended directory so junction aliases stay loop-free.
                    visited_real_dirs.add(child_key)
                    children_to_scan.append(child)
                    continue

                file_names.append(entry.name)
            except OSError:
                continue

        yield current, dir_names, file_names

        for child in reversed(children_to_scan):
            stack.append(child)


def _collect_artifact_violations(repo_root: Path) -> list[str]:
    violations: list[str] = []
    ignore_dirs = {".git", ".venv", "venv", "node_modules", ".next"}
    forbidden_exact_dirs = {
        ".pytest_cache",
        ".mypy_cache",
        "webapp/dist",
        "webapp/out",
        "marketing/out",
        ".tmp/bench",
    }

    for root, dirs, files in _iter_repo_tree(repo_root, repo_root, ignore_dirs=ignore_dirs):
        rel_root = root.relative_to(repo_root).as_posix()
        rel_root = "." if rel_root == "." else rel_root

        for dir_name in dirs:
            rel_dir = (Path(rel_root) / dir_name).as_posix() if rel_root != "." else dir_name
            if rel_dir in forbidden_exact_dirs:
                violations.append(f"Forbidden artifact directory exists: {rel_dir}/")
            if dir_name == "__pycache__":
                violations.append(f"Forbidden artifact directory exists: {rel_dir}/")

        for name in files:
            rel = (Path(rel_root) / name).as_posix() if rel_root != "." else name
            if name.endswith(".pyc"):
                violations.append(f"Forbidden artifact file exists: {rel}")
            if fnmatch.fnmatch(name, "portal_api_test_*.db"):
                violations.append(f"Forbidden artifact file exists: {rel}")

    return sorted(set(violations))


def _public_copy_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    fixed = [repo_root / "portal_bot" / "bot.py", repo_root / "portal_bot" / "helpbot.py"]
    files.extend([p for p in fixed if p.exists()])

    for base in (repo_root / "webapp" / "src", repo_root / "marketing" / "src"):
        if not base.exists():
            continue
        for root, _, names in _iter_repo_tree(base, repo_root):
            for name in names:
                if fnmatch.fnmatch(name, "*.ts") or fnmatch.fnmatch(name, "*.tsx"):
                    files.append(root / name)
                elif fnmatch.fnmatch(name, "*.js") or fnmatch.fnmatch(name, "*.jsx"):
                    files.append(root / name)
                elif fnmatch.fnmatch(name, "*.html") or fnmatch.fnmatch(name, "*.mdx"):
                    files.append(root / name)
    # Deduplicate while preserving stable order
    return sorted(set(files))


def _collect_copy_violations(repo_root: Path) -> list[str]:
    violations: list[str] = []
    patterns = [
        re.compile(r"\b100%\b", flags=re.IGNORECASE),
        re.compile(r"гарантирован\w*", flags=re.IGNORECASE),
        re.compile(r"без\s+ограничений", flags=re.IGNORECASE),
    ]
    for path in _public_copy_files(repo_root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for idx, line in enumerate(text.splitlines(), start=1):
            for pattern in patterns:
                if pattern.search(line):
                    rel = path.relative_to(repo_root).as_posix()
                    violations.append(f"Forbidden absolute claim found: {rel}:{idx}")
    return sorted(set(violations))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail CI if generated artifacts or forbidden absolute public claims are present."
    )
    parser.add_argument(
        "--check-copy",
        action="store_true",
        help="Also check public-facing copy for absolute promises (100%, гарантировано, без ограничений).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    violations = _collect_artifact_violations(repo_root)
    if args.check_copy:
        violations.extend(_collect_copy_violations(repo_root))

    if violations:
        print("Guardrail check failed:")
        for item in violations:
            print(f"- {item}")
        return 1

    print("Guardrail check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
