#!/usr/bin/env python3
"""Make one fail-closed Gate F decision for an exact POKROV 1.2.0 candidate.

The verifier does not execute external gates and never authorizes Gate G. It
validates the retained signed manifest, binds every required Gate F check to an
exact candidate-scoped evidence file, and emits exactly one GO, NO_GO, or
BLOCKED decision.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import release_1_2_pb14_candidate_gate as candidate_gate  # noqa: E402


INPUT_SCHEMA = "pokrov.release-1.2.0.gate-f-input/v1"
REPORT_SCHEMA = "pokrov.release-1.2.0.gate-f-decision/v1"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_REVISION_RE = re.compile(r"[0-9a-f]{40}\Z")

REQUIRED_CHECK_IDS = (
    "gates_a_e_exact_candidate",
    "mandatory_stop_ship_and_dod",
    "no_open_p0_false_green_or_secret_leak",
    "supply_chain_signature_sbom_provenance",
    "target_channel_signing_and_manual_gates",
    "release_docs_manifest_binding",
    "rollback_and_kill_controls",
    "current_origin",
    "brain_origin",
    "ru_origin",
    "windows_live_network",
    "android_ldplayer_rehearsal",
    "android_physical_device",
    "authenticated_client_egress",
    "payment_provider_e2e",
    "operator_auth_rbac_action_intent",
    "legal_commercial_approval",
    "performance_and_release_health",
    "hosted_required_checks",
)

ALLOWED_STATUSES = {
    "PASS",
    "FAIL",
    "MANUAL_OWNER_TEST",
    "OPERATOR_ATTESTED",
    "SKIPPED_BY_OWNER",
    "SKIPPED_BY_OPERATOR",
    "BLOCKED_BY_ACCESS",
    "BLOCKED_BY_ACCESS_GITHUB_BILLING",
    "BLOCKED_BY_OWNER_DECISION",
    "NOT_AUTHORIZED",
    "NOT_REQUESTED",
    "NOT_RUN",
    "MISSING",
}


class GateFError(RuntimeError):
    """Raised for malformed or unbound Gate F inputs."""


def _utcnow() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise GateFError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateFError(f"invalid JSON input: {path}") from exc
    if not isinstance(value, dict):
        raise GateFError(f"JSON input must be an object: {path}")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise GateFError(f"invalid JSON pointer: {pointer}")
    current = value
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, Mapping):
            if part not in current:
                raise GateFError(f"JSON pointer is missing: {pointer}")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit():
                raise GateFError(f"JSON pointer is missing: {pointer}")
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise GateFError(f"JSON pointer is missing: {pointer}") from exc
        else:
            raise GateFError(f"JSON pointer is missing: {pointer}")
    return current


def _relative_evidence_path(repo_root: Path, raw_path: Any) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise GateFError("evidence path must be a non-empty relative path")
    relative = Path(raw_path)
    if relative.is_absolute():
        raise GateFError("evidence path must be relative to the repository")
    resolved_root = repo_root.resolve()
    resolved = (resolved_root / relative).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise GateFError("evidence path escapes the repository") from exc
    return resolved


def _validate_upstream_evidence(
    *, repo_root: Path, evidence_payload: Mapping[str, Any]
) -> None:
    if evidence_payload.get("schema") != "pokrov.release-1.2.0.gate-f-evidence/v1":
        return
    upstream = evidence_payload.get("upstream_evidence")
    if not isinstance(upstream, list) or not upstream:
        raise GateFError("Gate F evidence lacks upstream evidence digests")
    seen: set[str] = set()
    for item in upstream:
        if not isinstance(item, Mapping):
            raise GateFError("Gate F upstream evidence entry must be an object")
        path = _relative_evidence_path(repo_root, item.get("path"))
        relative = path.relative_to(repo_root.resolve()).as_posix()
        if relative in seen:
            raise GateFError(f"duplicate Gate F upstream evidence: {relative}")
        seen.add(relative)
        expected_hash = str(item.get("sha256") or "").lower()
        if SHA256_RE.fullmatch(expected_hash) is None:
            raise GateFError(f"Gate F upstream evidence SHA-256 is invalid: {relative}")
        if not path.is_file():
            raise GateFError(f"Gate F upstream evidence is missing: {relative}")
        if _sha256_file(path) != expected_hash:
            raise GateFError(f"Gate F upstream evidence SHA-256 mismatch: {relative}")


def _expected_candidate(input_payload: Mapping[str, Any]) -> dict[str, Any]:
    candidate = input_payload.get("candidate")
    if not isinstance(candidate, Mapping):
        raise GateFError("Gate F input lacks candidate binding")
    expected = {
        "id": str(candidate.get("id") or ""),
        "operational_id": str(candidate.get("operational_id") or "").lower(),
        "manifest_sha256": str(candidate.get("manifest_sha256") or "").lower(),
        "signature_sha256": str(candidate.get("signature_sha256") or "").lower(),
        "receipt_sha256": str(candidate.get("receipt_sha256") or "").lower(),
        "sources": dict(candidate.get("sources") or {}),
    }
    if not expected["id"]:
        raise GateFError("candidate id is missing")
    for field in (
        "operational_id",
        "manifest_sha256",
        "signature_sha256",
        "receipt_sha256",
    ):
        if SHA256_RE.fullmatch(str(expected[field])) is None:
            raise GateFError(f"candidate {field} is invalid")
    if set(expected["sources"]) != {"platform", "client", "core", "release_index"}:
        raise GateFError("candidate source tuple is incomplete")
    for name, revision in expected["sources"].items():
        normalized = str(revision or "").lower()
        if GIT_REVISION_RE.fullmatch(normalized) is None:
            raise GateFError(f"candidate {name} source revision is invalid")
        expected["sources"][name] = normalized
    return expected


def _validate_signed_candidate(
    *,
    args: argparse.Namespace,
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    binding = candidate_gate._validate_retained_candidate(
        manifest_path=args.manifest,
        signature_path=args.signature,
        receipt_path=args.receipt,
        signed_evidence_path=args.signed_evidence,
        release_index_root=args.release_index_root,
    )
    manifest = _read_json(args.manifest)
    receipt_hash = _sha256_file(args.receipt)
    sources = manifest.get("sources")
    if not isinstance(sources, Mapping):
        raise GateFError("signed candidate source tuple is invalid")
    actual_sources: dict[str, str] = {}
    for name in ("platform", "client", "core", "release_index"):
        source = sources.get(name)
        if not isinstance(source, Mapping):
            raise GateFError(f"signed candidate {name} source is invalid")
        actual_sources[name] = str(source.get("commit") or "").lower()
    mismatches: list[str] = []
    comparisons = {
        "id": binding.get("candidate_label"),
        "operational_id": binding.get("candidate_id"),
        "manifest_sha256": binding.get("manifest_sha256"),
        "signature_sha256": binding.get("signature_sha256"),
        "receipt_sha256": receipt_hash,
    }
    for field, actual in comparisons.items():
        if str(actual or "").lower() != str(expected[field]).lower():
            mismatches.append(field)
    if actual_sources != expected["sources"]:
        mismatches.append("sources")
    if mismatches:
        raise GateFError(
            "signed candidate does not match Gate F input: " + ", ".join(mismatches)
        )
    return {
        "status": "PASS",
        "candidate_label": binding["candidate_label"],
        "operational_id": binding["candidate_id"],
        "manifest_sha256": binding["manifest_sha256"],
        "signature_sha256": binding["signature_sha256"],
        "receipt_sha256": receipt_hash,
        "signing": binding["signing"],
        "sources": actual_sources,
    }


def _validate_checks(
    *,
    repo_root: Path,
    input_payload: Mapping[str, Any],
    candidate_id: str,
) -> list[dict[str, Any]]:
    checks = input_payload.get("checks")
    if not isinstance(checks, list):
        raise GateFError("Gate F checks must be a list")
    by_id: dict[str, Mapping[str, Any]] = {}
    for raw_check in checks:
        if not isinstance(raw_check, Mapping):
            raise GateFError("Gate F check must be an object")
        identifier = str(raw_check.get("id") or "")
        if identifier in by_id:
            raise GateFError(f"duplicate Gate F check: {identifier}")
        by_id[identifier] = raw_check
    required = set(REQUIRED_CHECK_IDS)
    present = set(by_id)
    if present != required:
        missing = sorted(required - present)
        extra = sorted(present - required)
        raise GateFError(f"Gate F check set mismatch; missing={missing}; extra={extra}")

    outcomes: list[dict[str, Any]] = []
    validated_payloads: set[Path] = set()
    for identifier in REQUIRED_CHECK_IDS:
        raw_check = by_id[identifier]
        evidence = raw_check.get("evidence")
        if not isinstance(evidence, Mapping):
            raise GateFError(f"{identifier} lacks evidence binding")
        evidence_path = _relative_evidence_path(repo_root, evidence.get("path"))
        if not evidence_path.is_file():
            raise GateFError(f"{identifier} evidence file is missing")
        expected_hash = str(evidence.get("sha256") or "").lower()
        if SHA256_RE.fullmatch(expected_hash) is None:
            raise GateFError(f"{identifier} evidence SHA-256 is invalid")
        actual_hash = _sha256_file(evidence_path)
        if actual_hash != expected_hash:
            raise GateFError(f"{identifier} evidence SHA-256 mismatch")
        payload = _read_json(evidence_path)
        if evidence_path not in validated_payloads:
            _validate_upstream_evidence(
                repo_root=repo_root,
                evidence_payload=payload,
            )
            validated_payloads.add(evidence_path)
        status_pointer = str(evidence.get("status_pointer") or "")
        candidate_pointer = str(evidence.get("candidate_pointer") or "")
        status = _json_pointer(payload, status_pointer)
        bound_candidate = _json_pointer(payload, candidate_pointer)
        if not isinstance(status, str) or status not in ALLOWED_STATUSES:
            raise GateFError(f"{identifier} evidence status is not allowed: {status}")
        if bound_candidate != candidate_id:
            raise GateFError(f"{identifier} evidence candidate binding mismatch")
        outcomes.append(
            {
                "id": identifier,
                "status": status,
                "evidence": {
                    "path": evidence_path.relative_to(repo_root.resolve()).as_posix(),
                    "sha256": actual_hash,
                    "status_pointer": status_pointer,
                    "candidate_pointer": candidate_pointer,
                },
            }
        )
    return outcomes


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    validation_errors: list[str] = []
    candidate_summary: dict[str, Any] = {"status": "NOT_VALIDATED"}
    outcomes: list[dict[str, Any]] = []
    expected_id: str | None = None
    input_sha256: str | None = None
    try:
        if not args.input.is_file():
            raise GateFError(f"Gate F input is missing: {args.input}")
        input_sha256 = _sha256_file(args.input)
        input_payload = _read_json(args.input)
        if input_payload.get("schema") != INPUT_SCHEMA:
            raise GateFError("Gate F input schema is invalid")
        expected = _expected_candidate(input_payload)
        expected_id = expected["id"]
        candidate_summary = _validate_signed_candidate(args=args, expected=expected)
        outcomes = _validate_checks(
            repo_root=args.repo_root.resolve(),
            input_payload=input_payload,
            candidate_id=expected["id"],
        )
    except (GateFError, candidate_gate.Pb14GateError, OSError, ValueError) as exc:
        validation_errors.append(str(exc))

    if validation_errors:
        decision = "NO_GO"
    elif any(item["status"] == "FAIL" for item in outcomes):
        decision = "NO_GO"
    elif any(item["status"] != "PASS" for item in outcomes):
        decision = "BLOCKED"
    else:
        decision = "GO"

    return {
        "schema": REPORT_SCHEMA,
        "generated_at_utc": _utcnow(),
        "decision": decision,
        "candidate_id": expected_id,
        "candidate": candidate_summary,
        "gate_f_input_sha256": input_sha256,
        "checks": outcomes,
        "summary": {
            "required": len(REQUIRED_CHECK_IDS),
            "pass": sum(item["status"] == "PASS" for item in outcomes),
            "fail": sum(item["status"] == "FAIL" for item in outcomes),
            "non_pass": sum(item["status"] != "PASS" for item in outcomes),
            "validation_errors": validation_errors,
        },
        "promotion": {
            "gate_g_authorized": False,
            "stable_pointer_mutation": "NOT_AUTHORIZED",
            "public_release_mutation": "NOT_AUTHORIZED",
            "same_byte_promotion_requires_separate_owner_authorization": True,
        },
        "evidence_ceiling": (
            "GATE_F_DECISION_ONLY; GO DOES_NOT_AUTHORIZE_GATE_G_OR_PUBLIC_PROMOTION"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--signed-evidence", type=Path, required=True)
    parser.add_argument("--release-index-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--expect-blocked",
        action="store_true",
        help="Return success for an honestly retained BLOCKED report; NO_GO stays nonzero.",
    )
    return parser


def _exit_code(decision: str, *, expect_blocked: bool) -> int:
    if decision == "GO" or (decision == "BLOCKED" and expect_blocked):
        return 0
    return 2


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(args)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is None:
        sys.stdout.write(rendered)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    return _exit_code(report["decision"], expect_blocked=args.expect_blocked)


if __name__ == "__main__":
    raise SystemExit(main())
