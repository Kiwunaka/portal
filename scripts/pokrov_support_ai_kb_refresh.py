from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "shared" / "support-ai-knowledge.json"
DEFAULT_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_PI_BIN = "pi"

SOURCE_DOCS = (
    "AGENTS.md",
    "docs/README.md",
    "docs/product/portal-vpn-product.md",
    "docs/architecture/system-overview.md",
    "docs/architecture/app-first-and-bonus-flows.md",
    "docs/architecture/support-feedback-flow.md",
    "docs/operations/deployment-and-access.md",
    "docs/user/portal-vpn-user-guide-ru.md",
    "docs/user/compatibility-clients-guide-ru.md",
    "shared/product-facts.json",
    "shared/public-urls.json",
    "shared/access-matrix.json",
    "shared/tariff-catalog.json",
)
FORBIDDEN_PATH_PARTS = (
    "portal_bot/.env",
    "VPN NODE SSH KEYS",
    "secrets for merchant",
    "ops-local",
    "docs/audit-artifacts",
    "external/client-fork/app/windows",
)
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}\b", re.IGNORECASE),
    re.compile(r"\b(?:vless|vmess|trojan|ss|ssr)://[^\s<>)]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class SourceDoc:
    path: Path
    text: str


class KnowledgeValidationError(ValueError):
    pass


def _is_forbidden_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(part in normalized for part in FORBIDDEN_PATH_PARTS)


def collect_source_docs(repo_root: Path = REPO_ROOT) -> list[Path]:
    docs: list[Path] = []
    for rel in SOURCE_DOCS:
        if _is_forbidden_path(rel):
            continue
        path = repo_root / rel
        if path.exists() and path.is_file():
            docs.append(Path(rel))
    return docs


def read_source_docs(paths: Iterable[Path], *, repo_root: Path = REPO_ROOT, max_chars_per_file: int = 50000) -> list[SourceDoc]:
    out: list[SourceDoc] = []
    for rel_path in paths:
        rel = Path(rel_path)
        rel_posix = rel.as_posix()
        if _is_forbidden_path(rel_posix):
            continue
        path = repo_root / rel
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            text = pattern.sub("[redacted]", text)
        out.append(SourceDoc(path=rel, text=text[:max_chars_per_file]))
    return out


def build_pi_prompt(source_docs: list[SourceDoc]) -> str:
    sources = []
    for doc in source_docs:
        sources.append(f"### {doc.path.as_posix()}\n\n{doc.text.strip()}\n")
    source_bundle = "\n\n---\n\n".join(sources)
    return f"""You are the Pi harness preparing the production support knowledge base for POKROV.

Runtime route after this refresh:
- Production support service: OpenRouter chat completions.
- Model default: {DEFAULT_MODEL}.
- Output file: shared/support-ai-knowledge.json.

Task:
Read the supplied POKROV canon excerpts and produce one sanitized support knowledge JSON file for user support.
The JSON will be used by a server-side support assistant in Telegram, WebApp, and app ticket flows.

Hard rules:
- Answer knowledge must be in Russian user-support terms, but JSON keys stay English.
- Do not use VPN as a direct public product description except legacy compatibility labels.
- Do not claim store availability, stable 1.0.0, trusted Windows signing, raw Android physical-audit proof, or RU-origin readiness.
- Do not ask users for card details, private connection URLs, QR codes, raw subscription links, Telegram initData, passwords, private keys, or payment payloads.
- Keep account-specific, payment-specific, and unclear cases escalated to manual support.
- Prefer safe next steps: POKROV app, cabinet, official Telegram support, support ticket.
- Do not include secrets, raw identifiers, private links, internal deploy commands, SSH details, or operator-only notes.
- Do not output markdown fences. Return JSON only.

Required JSON shape:
{{
  "version": "{date.today().isoformat()}",
  "scope": "public_support",
  "language": "ru",
  "rules": ["..."],
  "fallback": {{"title": "manual_support", "body": "..."}},
  "topics": [
    {{"id": "official_surfaces", "keywords": ["..."], "body": "..."}}
  ]
}}

Topic guidance:
- 8 to 14 topics.
- Each topic id must be lowercase snake_case.
- Each topic body should be concise enough for chat context.
- Include Russian and transliterated keywords where useful.

Source canon:

{source_bundle}
"""


def extract_json_payload(raw: str) -> dict[str, Any]:
    text = str(raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise KnowledgeValidationError("Pi response did not contain a JSON object")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise KnowledgeValidationError("knowledge payload must be a JSON object")
    validate_payload(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    required = {"version", "scope", "language", "rules", "fallback", "topics"}
    missing = required - set(payload)
    if missing:
        raise KnowledgeValidationError(f"knowledge payload missing keys: {sorted(missing)}")
    if payload.get("scope") != "public_support":
        raise KnowledgeValidationError("scope must be public_support")
    if payload.get("language") != "ru":
        raise KnowledgeValidationError("language must be ru")
    if not isinstance(payload.get("rules"), list) or not payload["rules"]:
        raise KnowledgeValidationError("rules must be a non-empty list")
    if not isinstance(payload.get("fallback"), dict) or not str(payload["fallback"].get("body") or "").strip():
        raise KnowledgeValidationError("fallback.body is required")
    topics = payload.get("topics")
    if not isinstance(topics, list) or not topics:
        raise KnowledgeValidationError("topics must be a non-empty list")
    for topic in topics:
        if not isinstance(topic, dict):
            raise KnowledgeValidationError("each topic must be an object")
        topic_id = str(topic.get("id") or "")
        if not re.fullmatch(r"[a-z0-9_]{2,64}", topic_id):
            raise KnowledgeValidationError(f"invalid topic id: {topic_id!r}")
        if not isinstance(topic.get("keywords"), list) or not topic["keywords"]:
            raise KnowledgeValidationError(f"topic {topic_id} must have keywords")
        if not str(topic.get("body") or "").strip():
            raise KnowledgeValidationError(f"topic {topic_id} must have body")

    serialized = json.dumps(payload, ensure_ascii=False)
    for pattern in SECRET_PATTERNS:
        if pattern.search(serialized):
            raise KnowledgeValidationError("knowledge payload contains secret-like content")


def write_validated_payload(payload: dict[str, Any], output_path: Path) -> None:
    validate_payload(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def run_pi(prompt: str, *, pi_bin: str = DEFAULT_PI_BIN, model: str = DEFAULT_MODEL, timeout_seconds: int = 600) -> str:
    cmd = [pi_bin, "-p", prompt, "--mode", "json", "--model", model]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8", timeout=timeout_seconds)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or f"pi exited {completed.returncode}").strip())
    return completed.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh shared/support-ai-knowledge.json with a Pi-reviewed support KB.")
    sub = parser.add_subparsers(dest="command", required=True)

    inventory = sub.add_parser("inventory", help="print allowlisted source docs")
    inventory.add_argument("--repo-root", default=str(REPO_ROOT))

    prompt_cmd = sub.add_parser("prompt", help="print the Pi prompt packet")
    prompt_cmd.add_argument("--repo-root", default=str(REPO_ROOT))
    prompt_cmd.add_argument("--output", default="")

    apply_cmd = sub.add_parser("apply-response", help="validate a saved Pi response and write support-ai-knowledge.json")
    apply_cmd.add_argument("response_file")
    apply_cmd.add_argument("--output", default=str(DEFAULT_OUTPUT))

    run_cmd = sub.add_parser("run-pi", help="run Pi, validate JSON, and optionally write output")
    run_cmd.add_argument("--repo-root", default=str(REPO_ROOT))
    run_cmd.add_argument("--pi-bin", default=DEFAULT_PI_BIN)
    run_cmd.add_argument("--model", default=DEFAULT_MODEL)
    run_cmd.add_argument("--output", default=str(DEFAULT_OUTPUT))
    run_cmd.add_argument("--apply", action="store_true")

    args = parser.parse_args(argv)
    if args.command == "inventory":
        root = Path(args.repo_root)
        for path in collect_source_docs(root):
            print(path.as_posix())
        return 0
    if args.command == "prompt":
        root = Path(args.repo_root)
        prompt = build_pi_prompt(read_source_docs(collect_source_docs(root), repo_root=root))
        if args.output:
            Path(args.output).write_text(prompt, encoding="utf-8")
        else:
            print(prompt)
        return 0
    if args.command == "apply-response":
        payload = extract_json_payload(Path(args.response_file).read_text(encoding="utf-8", errors="replace"))
        write_validated_payload(payload, Path(args.output))
        print(f"wrote {Path(args.output).as_posix()}")
        return 0
    if args.command == "run-pi":
        root = Path(args.repo_root)
        prompt = build_pi_prompt(read_source_docs(collect_source_docs(root), repo_root=root))
        raw = run_pi(prompt, pi_bin=args.pi_bin, model=args.model)
        payload = extract_json_payload(raw)
        if args.apply:
            write_validated_payload(payload, Path(args.output))
            print(f"wrote {Path(args.output).as_posix()}")
        else:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
