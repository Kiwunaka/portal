from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path


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

    for root, dirs, files in os.walk(repo_root):
        rel_root = Path(root).resolve().relative_to(repo_root.resolve()).as_posix()
        rel_root = "." if rel_root == "." else rel_root

        # Prune large/generated folders we never want to scan deeply.
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        if rel_root in forbidden_exact_dirs:
            violations.append(f"Forbidden artifact directory exists: {rel_root}/")

        if "__pycache__" in dirs:
            violations.append(f"Forbidden artifact directory exists: {rel_root}/__pycache__/")

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
        for ext in ("*.ts", "*.tsx", "*.js", "*.jsx", "*.html", "*.mdx"):
            files.extend(base.rglob(ext))
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
                    rel = path.resolve().relative_to(repo_root.resolve()).as_posix()
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
