"""Build and query a read-only OpenAI File Search index for POKROV canon.

The script is intentionally local/operator-facing. It never reads secret
locations and only sends an explicit allowlist of canonical docs to OpenAI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_VECTOR_STORE_NAME = "pokrov-canon-docs"

DEFAULT_SOURCE_PATHS = (
    "AGENTS.md",
    "DESIGN.md",
    "docs/README.md",
    "docs/product/portal-vpn-product.md",
    "docs/product/public-beta-prd.md",
    "docs/product/payment-and-access-key-contract.md",
    "docs/product/platform-availability.md",
    "docs/product/beta-known-limitations.md",
    "docs/architecture/system-overview.md",
    "docs/architecture/app-first-and-bonus-flows.md",
    "docs/architecture/api-contracts.md",
    "docs/architecture/payment-state-machine.md",
    "docs/architecture/support-feedback-flow.md",
    "docs/architecture/client-downloads-flow.md",
    "docs/operations/deployment-and-access.md",
    "docs/operations/monitoring-and-visibility.md",
    "docs/operations/public-beta-release-runbook.md",
    "docs/operations/lavatop-payment-operations.md",
    "docs/operations/payment-reconciliation.md",
    "docs/operations/android-release-audit.md",
    "docs/operations/runtime-app-download-smoke.md",
    "docs/operations/ru-origin-probe.md",
    "docs/operations/rollback-runbook.md",
    "docs/developer/developer-guide.md",
    "docs/developer/repository-map.md",
    "docs/developer/orchestration/README.md",
    "docs/developer/orchestration/orchestration-standard.md",
    "docs/developer/orchestration/wo-authoring-guide.md",
    "docs/developer/orchestration/flow-state.md",
    "docs/developer/orchestration/context-cost-harnesses.md",
    "docs/developer/work-orders/README.md",
    "docs/developer/work-orders/2026-04-open-beta-v4/13-launch-decision.md",
    "docs/launch/open-beta-release-notes.md",
    "docs/launch/support-macros.md",
    "docs/launch/known-issues.md",
    "docs/launch/post-release-monitoring.md",
    "docs/user/portal-vpn-user-guide-ru.md",
    "shared/copy.ts",
    "shared/portal-config.ts",
    "shared/product-facts.json",
    "shared/public-urls.json",
    "shared/tariff-catalog.json",
    "shared/access-matrix.json",
)

NEVER_PARTS = {
    ".git",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "ops-local",
    "VPN NODE SSH KEYS",
    "secrets for merchant",
}

NEVER_FILES = {
    "portal_bot/.env",
    "external/client-fork/app/windows/sign.pfx",
    "external/client-fork/app/windows/sign.cer",
}

OPENAI_INSTRUCTIONS = """You are the read-only POKROV canon assistant.

Answer only from the indexed files. If the indexed canon does not support an
answer, say that the answer is not in the indexed POKROV canon and name the
likely doc area to check manually.

Hard rules:
- Never ask for, print, infer, or preserve secrets, auth headers, Telegram
  initData, private emails, payment payloads, subscription URLs, SSH keys, or
  raw user identifiers.
- Do not propose deploy, payment, SSH, grant, revoke, refund, or user-changing
  actions as already performed. You may suggest a manual operator check.
- Keep public wording aligned with POKROV canon: avoid direct-meaning public
  product wording around "VPN"; legacy "POKROV VPN" is allowed only as a
  compatibility identifier.
- Do not claim store availability, stable 1.0.0, trusted Windows signing, raw
  Android physical-audit proof, or RU-origin readiness unless the indexed canon
  contains current redacted evidence.
- Prefer compact answers with cited file names and short snippets/paraphrases.
"""


@dataclass(frozen=True)
class SourceFile:
    path: str
    bytes: int
    sha256: str
    kind: str


def _relative_posix(path: Path, root: Path = REPO_ROOT) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _is_blocked(path: Path, root: Path = REPO_ROOT) -> bool:
    relative = _relative_posix(path, root) if _is_within(path, root) else path.as_posix()
    parts = set(Path(relative).parts)
    if parts & NEVER_PARTS:
        return True
    return relative in NEVER_FILES


def _source_kind(relative_path: str) -> str:
    if relative_path.startswith("docs/developer/work-orders/"):
        return "release-evidence"
    if relative_path.startswith("docs/launch/"):
        return "launch"
    if relative_path.startswith("docs/operations/"):
        return "operations"
    if relative_path.startswith("docs/architecture/"):
        return "architecture"
    if relative_path.startswith("docs/product/"):
        return "product"
    if relative_path.startswith("shared/"):
        return "shared-facts"
    if relative_path == "AGENTS.md":
        return "agent-contract"
    if relative_path == "DESIGN.md":
        return "design"
    return "canon"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_sources(paths: Iterable[str], root: Path = REPO_ROOT) -> list[SourceFile]:
    sources: list[SourceFile] = []
    seen: set[str] = set()
    for raw_path in paths:
        if not str(raw_path or "").strip():
            continue
        path = (root / raw_path).resolve()
        if not _is_within(path, root):
            raise ValueError(f"refusing out-of-repo source: {raw_path}")
        if _is_blocked(path, root):
            raise ValueError(f"refusing blocked source: {raw_path}")
        if not path.exists() or not path.is_file():
            continue
        relative = _relative_posix(path, root)
        if relative in seen:
            continue
        seen.add(relative)
        sources.append(
            SourceFile(
                path=relative,
                bytes=path.stat().st_size,
                sha256=_sha256(path),
                kind=_source_kind(relative),
            )
        )
    return sources


def build_inventory(root: Path = REPO_ROOT, extra_paths: Iterable[str] = ()) -> dict[str, Any]:
    sources = resolve_sources((*DEFAULT_SOURCE_PATHS, *extra_paths), root=root)
    return {
        "repo": str(root),
        "source_count": len(sources),
        "total_bytes": sum(source.bytes for source in sources),
        "sources": [asdict(source) for source in sources],
        "blocked_parts": sorted(NEVER_PARTS),
        "blocked_files": sorted(NEVER_FILES),
    }


def _load_openai_client() -> Any:
    try:
        from openai import OpenAI  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "The OpenAI SDK is required for sync/ask. Install it in the ops "
            "environment, for example: python -m pip install openai"
        ) from exc
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _object_id(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("id") or "")
    return str(getattr(obj, "id", "") or "")


def _object_status(obj: Any) -> str:
    if isinstance(obj, dict):
        return str(obj.get("status") or "")
    return str(getattr(obj, "status", "") or "")


def _poll_vector_file(client: Any, vector_store_id: str, file_id: str, timeout_sec: int) -> str:
    deadline = time.monotonic() + max(1, int(timeout_sec))
    last_status = "unknown"
    while time.monotonic() < deadline:
        vector_file = client.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=file_id,
        )
        last_status = _object_status(vector_file)
        if last_status in {"completed", "failed", "cancelled"}:
            return last_status
        time.sleep(1.0)
    return last_status or "timeout"


def sync_vector_store(
    *,
    vector_store_id: str,
    name: str,
    sources: list[SourceFile],
    poll: bool,
    poll_timeout_sec: int,
    root: Path = REPO_ROOT,
) -> dict[str, Any]:
    client = _load_openai_client()
    if vector_store_id:
        store_id = vector_store_id
        created = False
    else:
        store = client.vector_stores.create(
            name=name,
            metadata={"repo": "POKROV", "scope": "canon-docs"},
        )
        store_id = _object_id(store)
        created = True

    uploaded: list[dict[str, Any]] = []
    for source in sources:
        path = root / source.path
        with path.open("rb") as handle:
            uploaded_file = client.files.create(file=handle, purpose="assistants")
        file_id = _object_id(uploaded_file)
        vector_file = client.vector_stores.files.create(
            vector_store_id=store_id,
            file_id=file_id,
            attributes={
                "path": source.path,
                "kind": source.kind,
                "sha256": source.sha256[:16],
            },
        )
        status = _object_status(vector_file)
        if poll:
            status = _poll_vector_file(client, store_id, file_id, poll_timeout_sec)
        uploaded.append(
            {
                "path": source.path,
                "file_id": file_id,
                "status": status,
                "sha256": source.sha256,
                "bytes": source.bytes,
            }
        )

    return {
        "vector_store_id": store_id,
        "created": created,
        "uploaded_count": len(uploaded),
        "uploaded": uploaded,
    }


def ask_file_search(*, vector_store_id: str, question: str, model: str) -> dict[str, Any]:
    if not vector_store_id.strip():
        raise SystemExit("--vector-store-id is required for ask")
    if not question.strip():
        raise SystemExit("question is required")
    client = _load_openai_client()
    response = client.responses.create(
        model=model,
        instructions=OPENAI_INSTRUCTIONS,
        input=question,
        tools=[{"type": "file_search", "vector_store_ids": [vector_store_id]}],
    )
    output_text = str(getattr(response, "output_text", "") or "")
    usage = getattr(response, "usage", None)
    usage_payload = usage.model_dump() if hasattr(usage, "model_dump") else usage
    return {
        "response_id": _object_id(response),
        "model": model,
        "vector_store_id": vector_store_id,
        "answer": output_text,
        "usage": usage_payload,
    }


def _write_json(payload: dict[str, Any], output: str) -> None:
    encoded = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="POKROV read-only OpenAI File Search docs assistant.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory_parser = subparsers.add_parser("inventory", help="Print the canonical source allowlist.")
    inventory_parser.add_argument("--extra", action="append", default=[], help="Extra repo-relative file to include.")
    inventory_parser.add_argument("--output", default="", help="Optional JSON output path.")

    sync_parser = subparsers.add_parser("sync", help="Upload canonical sources into an OpenAI vector store.")
    sync_parser.add_argument("--vector-store-id", default=os.getenv("POKROV_OPENAI_VECTOR_STORE_ID", ""))
    sync_parser.add_argument("--name", default=os.getenv("POKROV_OPENAI_VECTOR_STORE_NAME", DEFAULT_VECTOR_STORE_NAME))
    sync_parser.add_argument("--extra", action="append", default=[], help="Extra repo-relative file to include.")
    sync_parser.add_argument("--no-poll", action="store_true", help="Do not poll vector-store file ingestion.")
    sync_parser.add_argument("--poll-timeout-sec", type=int, default=120)
    sync_parser.add_argument("--output", default="", help="Optional JSON manifest path.")

    ask_parser = subparsers.add_parser("ask", help="Ask a question against an existing vector store.")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--vector-store-id", default=os.getenv("POKROV_OPENAI_VECTOR_STORE_ID", ""))
    ask_parser.add_argument("--model", default=os.getenv("POKROV_OPENAI_MODEL", DEFAULT_MODEL))
    ask_parser.add_argument("--output", default="", help="Optional JSON output path.")

    args = parser.parse_args(argv)
    if args.command == "inventory":
        _write_json(build_inventory(extra_paths=args.extra), args.output)
        return 0
    if args.command == "sync":
        sources = resolve_sources((*DEFAULT_SOURCE_PATHS, *args.extra))
        payload = sync_vector_store(
            vector_store_id=args.vector_store_id,
            name=args.name,
            sources=sources,
            poll=not args.no_poll,
            poll_timeout_sec=args.poll_timeout_sec,
        )
        _write_json(payload, args.output)
        return 0
    if args.command == "ask":
        payload = ask_file_search(
            vector_store_id=args.vector_store_id,
            question=args.question,
            model=args.model,
        )
        _write_json(payload, args.output)
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
