"""Collect deterministic static-export asset evidence for POKROV web surfaces."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
import platform
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

from performance_budget_gate import (
    DEFAULT_CONTRACT,
    ContractError,
    _load_json,
    contract_sha256,
    validate_budget_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COLLECTOR_ID = "pokrov.web-static-assets"
COLLECTOR_VERSION = "1.0.0"


class ScriptSourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag.lower() != "script":
            return
        for name, value in attrs:
            if name.lower() == "src" and value:
                self.sources.append(value)


def _run_text(command: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _git_identity(repo_root: Path) -> tuple[str, str]:
    revision = _run_text(["git", "rev-parse", "HEAD"], cwd=repo_root).lower()
    status = _run_text(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo_root
    )
    return revision, "dirty" if status else "clean"


def _toolchain(repo_root: Path, surfaces: set[str]) -> str:
    node_version = _run_text(["node", "--version"], cwd=repo_root)
    versions: list[str] = []
    for surface in sorted(surfaces):
        package_path = repo_root / surface / "package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        next_version = package.get("dependencies", {}).get("next")
        if not isinstance(next_version, str) or not next_version:
            raise ContractError(f"{package_path}: missing Next.js version")
        versions.append(f"{surface}:next@{next_version}")
    return f"node@{node_version};" + ";".join(versions)


def _safe_child(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ContractError("static export references a path outside its root") from exc
    return candidate


def _route_html_path(output_root: Path, route: str) -> Path:
    relative = "index.html" if route == "/" else f"{route.strip('/')}/index.html"
    result = _safe_child(output_root, relative)
    if not result.is_file():
        raise ContractError(f"missing static route: {route}")
    return result


def _route_js_gzip_bytes(
    output_root: Path, routes: list[str]
) -> tuple[int, set[Path]]:
    maximum = 0
    read_files: set[Path] = set()
    for route in routes:
        html_path = _route_html_path(output_root, route)
        read_files.add(html_path)
        parser = ScriptSourceParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        route_files: set[Path] = set()
        for source in parser.sources:
            parsed = urlsplit(source)
            if parsed.scheme or parsed.netloc or not parsed.path.endswith(".js"):
                continue
            script_path = _safe_child(output_root, parsed.path.lstrip("/"))
            if not script_path.is_file():
                raise ContractError(f"route {route} references missing local JavaScript")
            route_files.add(script_path)
        if not route_files:
            raise ContractError(f"route {route} has no local JavaScript assets")
        read_files.update(route_files)
        route_total = sum(
            len(gzip.compress(path.read_bytes(), compresslevel=9, mtime=0))
            for path in route_files
        )
        maximum = max(maximum, route_total)
    return maximum, read_files


def _extension_sum(
    output_root: Path, extensions: list[str]
) -> tuple[int, set[Path]]:
    extension_set = set(extensions)
    paths = {
        path.resolve()
        for path in output_root.rglob("*")
        if path.is_file() and path.suffix.lower() in extension_set
    }
    return sum(path.stat().st_size for path in paths), paths


def _artifact_tree_sha256(repo_root: Path, paths: set[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        relative = path.relative_to(repo_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        file_digest = hashlib.sha256(path.read_bytes()).digest()
        digest.update(file_digest)
    return digest.hexdigest()


def collect(
    *,
    repo_root: Path,
    contract_path: Path,
    release_version: str,
    candidate_label: str,
) -> dict[str, object]:
    contract = _load_json(contract_path)
    budgets = validate_budget_contract(contract)
    selected = [
        budget
        for budget in budgets.values()
        if budget["scope"] == "local_static"
        and budget["collector_id"] == COLLECTOR_ID
    ]
    if not selected:
        raise ContractError("performance contract has no web static budgets")
    surfaces = {str(budget["surface"]) for budget in selected}
    outputs = {surface: (repo_root / surface / "out").resolve() for surface in surfaces}
    for surface, output_root in outputs.items():
        if not output_root.is_dir():
            raise ContractError(f"missing static export for {surface}: {output_root}")

    measurements: list[dict[str, object]] = []
    evidence_files: set[Path] = set()
    for budget in selected:
        output_root = outputs[str(budget["surface"])]
        collection = budget["collection"]
        if collection["kind"] == "critical_route_js_gzip":
            value, paths = _route_js_gzip_bytes(output_root, collection["routes"])
        elif collection["kind"] == "extension_sum":
            value, paths = _extension_sum(output_root, collection["extensions"])
        else:  # protected by contract validation
            raise ContractError("unsupported web collection kind")
        evidence_files.update(paths)
        measurements.append(
            {
                "baseline": None,
                "budget_id": budget["id"],
                "samples": [value],
                "state": "MEASURED",
                "unit": budget["unit"],
                "warmup_samples_discarded": 0,
            }
        )

    revision, worktree_state = _git_identity(repo_root)
    toolchain = _toolchain(repo_root, surfaces)
    return {
        "schema_version": contract["evidence_schema_version"],
        "budget_contract": {
            "id": contract["contract_id"],
            "sha256": contract_sha256(contract_path),
            "version": contract["contract_version"],
        },
        "release": {
            "candidate_label": candidate_label,
            "source_revision": revision,
            "version": release_version,
            "working_tree_state": worktree_state,
        },
        "environment": {
            "architecture": platform.machine() or "unknown",
            "artifact_sha256": _artifact_tree_sha256(repo_root, evidence_files),
            "build_mode": "release-static-export",
            "captured_at_utc": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
            "collector_id": COLLECTOR_ID,
            "collector_version": COLLECTOR_VERSION,
            "device_model": "local-build-host",
            "network_profile": "static-export-no-network",
            "origin": "local",
            "os_version": platform.platform(),
            "platform": "web",
            "toolchain": toolchain,
        },
        "measurements": measurements,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--release-version", default="1.2.0")
    parser.add_argument("--candidate-label", default="local-working-tree")
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = collect(
            repo_root=args.repo_root.resolve(),
            contract_path=args.contract.resolve(),
            release_version=args.release_version,
            candidate_label=args.candidate_label,
        )
    except (ContractError, OSError, subprocess.CalledProcessError) as exc:
        print(f"WEB_PERFORMANCE_COLLECTION_FAILED: {exc}", file=sys.stderr)
        return 2
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"WEB_PERFORMANCE_EVIDENCE: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
