from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RE_SCRIPT = re.compile(r"(?<![A-Za-z0-9_./-])(?:python\s+)?(scripts/[A-Za-z0-9_.\-]+\.py)")
RE_LEGACY_ENTRY = re.compile(r"\b(deploy_all_fixes\.py)\b")


def _load_manifest(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid manifest format ({path}): {exc}") from exc


def _collect_doc_files(repo_root: Path) -> list[Path]:
    files = [repo_root / "ADMIN_GUIDE.md", repo_root / "USER_GUIDE_RU.md"]
    files.extend(sorted((repo_root / "docs").glob("**/*.md")))
    return [p for p in files if p.exists()]


def _iter_refs(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    refs = [m.group(1) for m in RE_SCRIPT.finditer(text)]
    refs.extend(m.group(1) for m in RE_LEGACY_ENTRY.finditer(text))
    return refs


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate docs reference only active scripts from scripts/manifest.yaml")
    ap.add_argument("--manifest", default="scripts/manifest.yaml")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / args.manifest
    if not manifest_path.exists():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    manifest = _load_manifest(manifest_path)
    active = set(manifest.get("active", []))
    deprecated = set(manifest.get("deprecated", []))
    archive_only = set(manifest.get("archive_only", []))
    denylist = set(manifest.get("denylist", []))

    problems: list[str] = []
    for doc in _collect_doc_files(repo_root):
        for ref in _iter_refs(doc):
            if ref in denylist or ref in deprecated or ref in archive_only:
                problems.append(f"{doc}: forbidden reference `{ref}`")
                continue
            if ref.startswith("scripts/") and ref not in active:
                problems.append(f"{doc}: reference `{ref}` missing from active manifest")
                continue
            if ref.startswith("scripts/"):
                target = repo_root / ref
                if not target.exists():
                    problems.append(f"{doc}: missing file `{ref}`")

    if problems:
        print("Script manifest check failed:")
        for p in problems:
            print(f"- {p}")
        return 1

    print("Script manifest check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
