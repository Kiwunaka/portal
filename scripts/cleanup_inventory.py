from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


CLASS_SAFE = "safe"
CLASS_INTENTIONAL_RESET = "intentional-reset"
CLASS_ALL = "all"


@dataclass(frozen=True)
class CleanupMatch:
    cleanup_class: str
    kind: str
    path: str
    reason: str


@dataclass(frozen=True)
class DirRule:
    cleanup_class: str
    reason: str
    exact_paths: tuple[PurePosixPath, ...] = ()
    basenames: tuple[str, ...] = ()
    basename_prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FileRule:
    cleanup_class: str
    reason: str
    exact_paths: tuple[PurePosixPath, ...] = ()
    basename_prefixes: tuple[str, ...] = ()
    basename_suffixes: tuple[str, ...] = ()
    glob_patterns: tuple[str, ...] = ()


DIR_RULES: tuple[DirRule, ...] = (
    DirRule(
        cleanup_class=CLASS_SAFE,
        reason="generated Python cache",
        basenames=("__pycache__",),
    ),
    DirRule(
        cleanup_class=CLASS_SAFE,
        reason="generated pytest cache",
        basenames=(".pytest_cache",),
    ),
    DirRule(
        cleanup_class=CLASS_SAFE,
        reason="generated frontend build cache",
        basenames=(".next",),
    ),
    DirRule(
        cleanup_class=CLASS_SAFE,
        reason="generated test artifacts",
        basenames=("test-results",),
    ),
    DirRule(
        cleanup_class=CLASS_SAFE,
        reason="repo-local disposable scratch",
        basenames=(".tmp",),
        basename_prefixes=(".tmp-",),
    ),
    DirRule(
        cleanup_class=CLASS_SAFE,
        reason="generated static export output",
        exact_paths=(
            PurePosixPath("webapp/out"),
            PurePosixPath("webapp/dist"),
            PurePosixPath("marketing/out"),
        ),
    ),
    DirRule(
        cleanup_class=CLASS_INTENTIONAL_RESET,
        reason="legacy client Flutter workspace cache",
        exact_paths=(PurePosixPath("external/client-fork/app/.dart_tool"),),
    ),
    DirRule(
        cleanup_class=CLASS_INTENTIONAL_RESET,
        reason="legacy client local build output",
        exact_paths=(PurePosixPath("external/client-fork/app/build"),),
    ),
    DirRule(
        cleanup_class=CLASS_INTENTIONAL_RESET,
        reason="legacy client Flutter ephemeral host output",
        exact_paths=(PurePosixPath("external/client-fork/app/windows/flutter/ephemeral"),),
    ),
)


FILE_RULES: tuple[FileRule, ...] = (
    FileRule(
        cleanup_class=CLASS_SAFE,
        reason="temporary local test database",
        glob_patterns=("portal_api_test_*.db",),
    ),
    FileRule(
        cleanup_class=CLASS_SAFE,
        reason="TypeScript incremental cache",
        basename_suffixes=(".tsbuildinfo",),
    ),
    FileRule(
        cleanup_class=CLASS_SAFE,
        reason="repo-local disposable scratch",
        basename_prefixes=(".tmp-",),
    ),
)


PROTECTED_DIRS: tuple[PurePosixPath, ...] = (
    PurePosixPath(".git"),
    PurePosixPath("docs/audit-artifacts"),
    PurePosixPath("external/client-fork/app/out"),
    PurePosixPath("external/client-fork/app/windows"),
    PurePosixPath("ops-local"),
    PurePosixPath("VPN NODE SSH KEYS"),
    PurePosixPath("secrets for merchant"),
)

PROTECTED_EXCEPTIONS: tuple[PurePosixPath, ...] = (
    PurePosixPath("external/client-fork/app/windows/flutter/ephemeral"),
)

PROTECTED_FILES: tuple[PurePosixPath, ...] = (
    PurePosixPath("portal_bot/.env"),
)

AVAILABLE_CLASSES: tuple[str, ...] = (
    CLASS_SAFE,
    CLASS_INTENTIONAL_RESET,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Inventory repo-local cleanup candidates without deleting anything. "
            "Protected zones and retained evidence are pruned automatically."
        )
    )
    parser.add_argument(
        "--class",
        dest="classes",
        action="append",
        choices=(CLASS_SAFE, CLASS_INTENTIONAL_RESET, CLASS_ALL),
        help=(
            "Cleanup class to report. Repeat for multiple classes. "
            "Defaults to safe."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print inventory only. This is the default unless --apply is passed.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Delete the selected cleanup candidates after validating every resolved "
            "target stays inside the repository root and outside protected zones."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root to scan. Defaults to the parent of this script.",
    )
    return parser.parse_args()


def _repo_root_from_args(raw_root: str | None) -> Path:
    if raw_root:
        return Path(raw_root).resolve()
    return Path(__file__).resolve().parents[1]


def _rel_path(path: Path, repo_root: Path) -> PurePosixPath:
    rel = path.relative_to(repo_root)
    return PurePosixPath(rel.as_posix())


def _is_same_or_child(path: PurePosixPath, prefix: PurePosixPath) -> bool:
    return path == prefix or prefix in path.parents


def _is_linkish(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    return path.is_symlink() or (callable(is_junction) and is_junction())


def _is_protected(rel_path: PurePosixPath) -> bool:
    if any(_is_same_or_child(rel_path, allowed) for allowed in PROTECTED_EXCEPTIONS):
        return False
    if rel_path in PROTECTED_FILES:
        return True
    return any(_is_same_or_child(rel_path, protected) for protected in PROTECTED_DIRS)


def _has_exception_descendant(rel_path: PurePosixPath) -> bool:
    return any(exception != rel_path and _is_same_or_child(exception, rel_path) for exception in PROTECTED_EXCEPTIONS)


def _selected_classes(raw_classes: list[str] | None) -> tuple[str, ...]:
    if not raw_classes:
        return (CLASS_SAFE,)
    if CLASS_ALL in raw_classes:
        return AVAILABLE_CLASSES
    ordered = [cleanup_class for cleanup_class in AVAILABLE_CLASSES if cleanup_class in raw_classes]
    return tuple(ordered)


def _match_dir(rel_path: PurePosixPath) -> CleanupMatch | None:
    for rule in DIR_RULES:
        if (
            rel_path in rule.exact_paths
            or rel_path.name in rule.basenames
            or any(rel_path.name.startswith(prefix) for prefix in rule.basename_prefixes)
        ):
            return CleanupMatch(
                cleanup_class=rule.cleanup_class,
                kind="dir",
                path=f"{rel_path.as_posix()}/",
                reason=rule.reason,
            )
    return None


def _match_file(rel_path: PurePosixPath) -> CleanupMatch | None:
    for rule in FILE_RULES:
        if rel_path in rule.exact_paths:
            return CleanupMatch(rule.cleanup_class, "file", rel_path.as_posix(), rule.reason)
        if any(rel_path.name.startswith(prefix) for prefix in rule.basename_prefixes):
            return CleanupMatch(rule.cleanup_class, "file", rel_path.as_posix(), rule.reason)
        if any(rel_path.name.endswith(suffix) for suffix in rule.basename_suffixes):
            if "node_modules" in rel_path.parts:
                continue
            return CleanupMatch(rule.cleanup_class, "file", rel_path.as_posix(), rule.reason)
        if any(rel_path.match(pattern) for pattern in rule.glob_patterns):
            return CleanupMatch(rule.cleanup_class, "file", rel_path.as_posix(), rule.reason)
    return None


def _walk_inventory(repo_root: Path, selected_classes: Iterable[str]) -> list[CleanupMatch]:
    selected = set(selected_classes)
    matches: list[CleanupMatch] = []

    for root, dirs, files in os.walk(repo_root, topdown=True, followlinks=False):
        root_path = Path(root)
        rel_root = _rel_path(root_path, repo_root)

        kept_dirs: list[str] = []
        for dirname in sorted(dirs):
            child_path = root_path / dirname
            child_rel = rel_root / dirname if rel_root.as_posix() != "." else PurePosixPath(dirname)
            if _is_linkish(child_path):
                continue
            if _is_protected(child_rel):
                if _has_exception_descendant(child_rel):
                    kept_dirs.append(dirname)
                continue

            match = _match_dir(child_rel)
            if match is not None:
                if match.cleanup_class in selected:
                    matches.append(match)
                continue

            kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in sorted(files):
            child_rel = rel_root / filename if rel_root.as_posix() != "." else PurePosixPath(filename)
            if _is_protected(child_rel):
                continue
            match = _match_file(child_rel)
            if match is not None and match.cleanup_class in selected:
                matches.append(match)

    return matches


def _ensure_safe_apply_target(repo_root: Path, match: CleanupMatch) -> Path:
    rel_path = PurePosixPath(match.path.rstrip("/"))
    if rel_path.is_absolute() or ".." in rel_path.parts:
        raise RuntimeError(f"Refusing unsafe cleanup path: {match.path}")
    if _is_protected(rel_path):
        raise RuntimeError(f"Refusing protected cleanup path: {match.path}")

    repo_resolved = repo_root.resolve()
    target = (repo_resolved / Path(*rel_path.parts)).resolve(strict=False)
    try:
        common = os.path.commonpath([str(repo_resolved), str(target)])
    except ValueError as exc:
        raise RuntimeError(f"Refusing cleanup outside repository: {match.path}") from exc
    if os.path.normcase(common) != os.path.normcase(str(repo_resolved)):
        raise RuntimeError(f"Refusing cleanup outside repository: {match.path}")
    return target


def _apply_matches(repo_root: Path, matches: list[CleanupMatch]) -> list[str]:
    deleted: list[str] = []
    for match in matches:
        target = _ensure_safe_apply_target(repo_root, match)
        if not target.exists() and not target.is_symlink():
            continue
        if match.kind == "dir":
            if _is_linkish(target):
                raise RuntimeError(f"Refusing to recursively delete link-like directory: {match.path}")
            shutil.rmtree(target)
        elif match.kind == "file":
            target.unlink()
        else:
            raise RuntimeError(f"Unknown cleanup item kind for {match.path}: {match.kind}")
        deleted.append(match.path)
    return deleted


def _walk_app_next_alias(selected_classes: Iterable[str]) -> list[CleanupMatch]:
    selected = set(selected_classes)
    alias_root = Path(__file__).resolve().parents[1] / "app-next"
    if not alias_root.exists() or not alias_root.is_dir():
        return []

    matches: list[CleanupMatch] = []

    for root, dirs, files in os.walk(alias_root, topdown=True, followlinks=False):
        root_path = Path(root)
        try:
            alias_rel = root_path.relative_to(alias_root)
        except ValueError:
            continue

        alias_prefix = PurePosixPath("app-next")
        rel_root = alias_prefix / PurePosixPath(alias_rel.as_posix()) if alias_rel.as_posix() != "." else alias_prefix

        kept_dirs: list[str] = []
        for dirname in sorted(dirs):
            child_path = root_path / dirname
            child_rel = rel_root / dirname
            if _is_linkish(child_path):
                continue

            if dirname == ".dart_tool" and CLASS_INTENTIONAL_RESET in selected:
                matches.append(
                    CleanupMatch(
                        cleanup_class=CLASS_INTENTIONAL_RESET,
                        kind="dir",
                        path=f"{child_rel.as_posix()}/",
                        reason="app-next Flutter workspace cache",
                    )
                )
                continue

            if dirname == "build" and CLASS_INTENTIONAL_RESET in selected:
                matches.append(
                    CleanupMatch(
                        cleanup_class=CLASS_INTENTIONAL_RESET,
                        kind="dir",
                        path=f"{child_rel.as_posix()}/",
                        reason="app-next local build output",
                    )
                )
                continue

            kept_dirs.append(dirname)
        dirs[:] = kept_dirs

        for filename in sorted(files):
            child_rel = rel_root / filename
            if (
                CLASS_INTENTIONAL_RESET in selected
                and child_rel.parent == PurePosixPath("app-next/config/local")
                and filename != ".gitkeep"
            ):
                matches.append(
                    CleanupMatch(
                        cleanup_class=CLASS_INTENTIONAL_RESET,
                        kind="file",
                        path=child_rel.as_posix(),
                        reason="app-next regenerated local-only config",
                    )
                )

    return matches


def _json_payload(repo_root: Path, selected_classes: tuple[str, ...], matches: list[CleanupMatch]) -> dict:
    summary = {cleanup_class: 0 for cleanup_class in selected_classes}
    for match in matches:
        summary[match.cleanup_class] = summary.get(match.cleanup_class, 0) + 1

    return {
        "mode": "dry-run",
        "inventory_only": True,
        "root": str(repo_root),
        "selected_classes": list(selected_classes),
        "protected_dirs": [path.as_posix() for path in PROTECTED_DIRS],
        "protected_exceptions": [path.as_posix() for path in PROTECTED_EXCEPTIONS],
        "protected_files": [path.as_posix() for path in PROTECTED_FILES],
        "summary": summary,
        "items": [asdict(match) for match in matches],
    }


def _json_apply_payload(
    repo_root: Path,
    selected_classes: tuple[str, ...],
    matches: list[CleanupMatch],
    deleted: list[str],
) -> dict:
    payload = _json_payload(repo_root, selected_classes, matches)
    payload["mode"] = "apply"
    payload["inventory_only"] = False
    payload["deleted_count"] = len(deleted)
    payload["deleted"] = deleted
    return payload


def _render_text(
    repo_root: Path,
    selected_classes: tuple[str, ...],
    matches: list[CleanupMatch],
    *,
    mode: str = "dry-run",
) -> str:
    by_class = {cleanup_class: [] for cleanup_class in selected_classes}
    for match in matches:
        by_class.setdefault(match.cleanup_class, []).append(match)

    mode_line = (
        "Mode: apply (selected files/directories were validated before deletion)"
        if mode == "apply"
        else "Mode: dry-run (inventory only; no files are deleted)"
    )
    lines = [
        "Cleanup inventory report",
        f"Root: {repo_root}",
        mode_line,
        f"Selected classes: {', '.join(selected_classes)}",
        "Protected zones: "
        + ", ".join([path.as_posix() for path in PROTECTED_DIRS] + [path.as_posix() for path in PROTECTED_FILES]),
    ]
    if PROTECTED_EXCEPTIONS:
        lines.append(
            "Protected exceptions: " + ", ".join(path.as_posix() for path in PROTECTED_EXCEPTIONS)
        )

    for cleanup_class in selected_classes:
        items = by_class.get(cleanup_class, [])
        lines.append("")
        lines.append(f"[{cleanup_class}] {len(items)} match(es)")
        if not items:
            lines.append("- none")
            continue
        for item in items:
            lines.append(f"- {item.kind}: {item.path} ({item.reason})")

    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    if args.apply and args.dry_run:
        raise SystemExit("--apply and --dry-run cannot be combined")

    repo_root = _repo_root_from_args(args.root)
    if not repo_root.exists():
        raise SystemExit(f"Repository root does not exist: {repo_root}")

    selected_classes = _selected_classes(args.classes)
    matches = _walk_inventory(repo_root, selected_classes)
    matches.extend(_walk_app_next_alias(selected_classes))
    matches.sort(key=lambda item: (item.cleanup_class, item.path))

    if args.apply:
        deleted = _apply_matches(repo_root, matches)
        if args.format == "json":
            print(json.dumps(_json_apply_payload(repo_root, selected_classes, matches, deleted), indent=2))
        else:
            print(_render_text(repo_root, selected_classes, matches, mode="apply"))
            print("")
            print(f"Deleted {len(deleted)} item(s).")
    elif args.format == "json":
        print(json.dumps(_json_payload(repo_root, selected_classes, matches), indent=2))
    else:
        print(_render_text(repo_root, selected_classes, matches))

    return 0


if __name__ == "__main__":
    sys.exit(main())
