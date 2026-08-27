"""Generate the support-facing error reference from the canonical catalog."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "shared/contracts/observability/error-catalog.json"
OUTPUT_PATH = REPO_ROOT / "shared/contracts/observability/SUPPORT-REFERENCE.md"


def _load_catalog(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    entries = payload.get("entries")
    if (
        payload.get("schema_version") != 1
        or not isinstance(payload.get("catalog_version"), str)
        or not isinstance(entries, list)
        or not entries
    ):
        raise ValueError("canonical error catalog is invalid")
    codes = [entry.get("code") for entry in entries if isinstance(entry, dict)]
    if len(codes) != len(entries) or len(set(codes)) != len(entries):
        raise ValueError("canonical error catalog has invalid or duplicate codes")
    canonical = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return {**payload, "_sha256": hashlib.sha256(canonical).hexdigest()}


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_reference(catalog_path: Path = CATALOG_PATH) -> str:
    catalog = _load_catalog(catalog_path)
    entries = sorted(catalog["entries"], key=lambda entry: str(entry["code"]))
    lines = [
        "# POKROV observability support reference",
        "",
        "Generated from `error-catalog.json`; do not edit by hand.",
        "",
        f"- catalog version: `{catalog['catalog_version']}`",
        f"- catalog SHA-256: `{catalog['_sha256']}`",
        f"- entries: `{len(entries)}`",
        "",
        "Regenerate with:",
        "",
        "```powershell",
        "python scripts/generate_observability_support_reference.py --write",
        "```",
        "",
        "| Code | Severity | Owner | Safe user message (RU) | Operator action | Release blocking |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            "| "
            + " | ".join(
                _cell(value)
                for value in (
                    f"`{entry['code']}`",
                    entry["severity"],
                    entry["owner"],
                    entry["public_message_ru"],
                    f"`{entry['operator_action']}`",
                    "yes" if entry["release_blocking"] else "no",
                )
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = render_reference(args.catalog.resolve())
        output = args.output.resolve()
        if args.write:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"WROTE {output}")
            return 0
        if not output.is_file() or output.read_text(encoding="utf-8") != rendered:
            print(f"STALE {output}", file=sys.stderr)
            return 1
        print(f"PASS {output}")
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
