#!/usr/bin/env python3
"""Fail-closed controller for the isolated emergency-network firewall lab.

The controller never changes the host firewall.  A separately reviewed,
hash-pinned executor owns the disposable network namespace or sandbox.  This
process only binds inputs to hashes, invokes that executor without a shell and
derives PASS/FAIL from a strict, redacted result contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping


SCHEMA = "pokrov-emergency-synthetic-firewall-proof-v1"
EXECUTOR_SCHEMA = "pokrov-emergency-isolated-executor-result-v1"
PINNED_CORE_SHA256 = "7cc83854fc4022b759e9de3d0942b90a24c859cfd51e3231d04e7c7a6b7d5054"
MAX_EXECUTOR_OUTPUT_BYTES = 64 * 1024
_HEX64_RE = re.compile(r"^[a-f0-9]{64}$")
_ISOLATION_KINDS = frozenset({"linux-network-namespace", "windows-sandbox", "dedicated-lab-vm"})
_CHECK_KEYS = frozenset(
    {
        "ru_reserve_reachable",
        "direct_foreign_blocked",
        "reserve_to_owned_foreign",
        "reserve_to_owned_ru_to_owned_foreign",
        "owned_foreign_exit_verified",
        "dns_chain_resolved",
    }
)


class ProofFailure(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_hex64(value: object) -> bool:
    return isinstance(value, str) and _HEX64_RE.fullmatch(value) is not None


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _blocked(*, core_sha256: str, reasons: list[str]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "classification": "BLOCKED_BY_ACCESS",
        "core_sha256": core_sha256,
        "reasons": sorted(set(reasons)),
    }


def preflight(
    *,
    core_path: Path,
    executor_path: Path | None,
    executor_sha256: str | None,
    manifest_path: Path | None,
    manifest_sha256: str | None,
) -> dict[str, Any]:
    if not core_path.is_file():
        return _blocked(core_sha256="", reasons=["exact_core_unavailable"])
    core_digest = _sha256_file(core_path)
    if core_digest != PINNED_CORE_SHA256:
        raise ProofFailure("exact_core_hash_mismatch")

    blockers: list[str] = []
    if executor_path is None or not executor_path.is_absolute() or not executor_path.is_file():
        blockers.append("isolated_executor_unavailable")
    elif not _is_hex64(executor_sha256) or _sha256_file(executor_path) != executor_sha256:
        raise ProofFailure("isolated_executor_hash_mismatch")
    if manifest_path is None or not manifest_path.is_absolute() or not manifest_path.is_file():
        blockers.append("controlled_fixture_manifest_unavailable")
    elif not _is_hex64(manifest_sha256) or _sha256_file(manifest_path) != manifest_sha256:
        raise ProofFailure("controlled_fixture_manifest_hash_mismatch")
    if blockers:
        return _blocked(core_sha256=core_digest, reasons=blockers)
    return {
        "schema_version": SCHEMA,
        "classification": "READY_NOT_EXECUTED",
        "core_sha256": core_digest,
        "executor_sha256": executor_sha256,
        "fixture_manifest_sha256": manifest_sha256,
    }


def _validate_executor_result(
    result: Mapping[str, Any],
    *,
    core_sha256: str,
    executor_sha256: str,
    manifest_sha256: str,
    expected_payload_sha256: str,
) -> dict[str, Any]:
    expected_top_keys = {
        "schema_version",
        "core_sha256",
        "executor_sha256",
        "fixture_manifest_sha256",
        "firewall_policy_sha256",
        "payload_sha256",
        "isolation",
        "checks",
    }
    if set(result) != expected_top_keys or result.get("schema_version") != EXECUTOR_SCHEMA:
        raise ProofFailure("executor_result_shape_invalid")
    expected_hashes = {
        "core_sha256": core_sha256,
        "executor_sha256": executor_sha256,
        "fixture_manifest_sha256": manifest_sha256,
        "payload_sha256": expected_payload_sha256,
    }
    for key, expected in expected_hashes.items():
        if result.get(key) != expected:
            raise ProofFailure(f"executor_{key}_mismatch")
    if not _is_hex64(result.get("firewall_policy_sha256")):
        raise ProofFailure("firewall_policy_hash_invalid")

    isolation = result.get("isolation")
    if not isinstance(isolation, dict) or set(isolation) != {
        "kind",
        "ephemeral",
        "host_firewall_untouched",
        "teardown_completed",
    }:
        raise ProofFailure("isolation_result_invalid")
    if isolation.get("kind") not in _ISOLATION_KINDS:
        raise ProofFailure("isolation_kind_invalid")

    checks = result.get("checks")
    if not isinstance(checks, dict) or set(checks) != _CHECK_KEYS:
        raise ProofFailure("executor_checks_invalid")
    if any(not isinstance(value, bool) for value in checks.values()):
        raise ProofFailure("executor_checks_invalid")

    failed_checks = sorted(key for key, value in checks.items() if not value)
    if isolation.get("ephemeral") is not True:
        failed_checks.append("isolation_not_ephemeral")
    if isolation.get("host_firewall_untouched") is not True:
        failed_checks.append("host_firewall_touched")
    if isolation.get("teardown_completed") is not True:
        failed_checks.append("teardown_incomplete")
    failed_checks.sort()

    return {
        "schema_version": SCHEMA,
        "classification": "PASS" if not failed_checks else "FAIL",
        "core_sha256": core_sha256,
        "executor_sha256": executor_sha256,
        "fixture_manifest_sha256": manifest_sha256,
        "firewall_policy_sha256": result["firewall_policy_sha256"],
        "payload_sha256": expected_payload_sha256,
        "isolation_kind": isolation["kind"],
        "failed_checks": failed_checks,
        "evidence_sha256": _canonical_sha256(result),
    }


def execute(
    *,
    core_path: Path,
    executor_path: Path,
    executor_sha256: str,
    manifest_path: Path,
    manifest_sha256: str,
    expected_payload_sha256: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    ready = preflight(
        core_path=core_path,
        executor_path=executor_path,
        executor_sha256=executor_sha256,
        manifest_path=manifest_path,
        manifest_sha256=manifest_sha256,
    )
    if ready["classification"] != "READY_NOT_EXECUTED":
        return ready
    if not _is_hex64(expected_payload_sha256):
        raise ProofFailure("expected_payload_hash_invalid")

    request = {
        "schema_version": "pokrov-emergency-isolated-executor-request-v1",
        "core_path": str(core_path.resolve()),
        "fixture_manifest_path": str(manifest_path.resolve()),
        "expected_payload_sha256": expected_payload_sha256,
    }
    environment = os.environ.copy()
    environment["POKROV_EMERGENCY_LAB_NO_HOST_FIREWALL"] = "1"
    try:
        completed = subprocess.run(
            [str(executor_path.resolve())],
            input=json.dumps(request, separators=(",", ":")),
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            shell=False,
            env=environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProofFailure("isolated_executor_timeout") from exc
    if completed.returncode != 0:
        raise ProofFailure("isolated_executor_failed")
    if len(completed.stdout.encode("utf-8")) > MAX_EXECUTOR_OUTPUT_BYTES:
        raise ProofFailure("executor_output_too_large")
    try:
        result = json.loads(completed.stdout)
    except ValueError as exc:
        raise ProofFailure("executor_result_invalid") from exc
    if not isinstance(result, dict):
        raise ProofFailure("executor_result_invalid")
    return _validate_executor_result(
        result,
        core_sha256=PINNED_CORE_SHA256,
        executor_sha256=executor_sha256,
        manifest_sha256=manifest_sha256,
        expected_payload_sha256=expected_payload_sha256,
    )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="POKROV isolated emergency firewall proof controller")
    parser.add_argument("--core-dll", required=True, type=Path)
    parser.add_argument("--executor", type=Path)
    parser.add_argument("--executor-sha256")
    parser.add_argument("--fixture-manifest", type=Path)
    parser.add_argument("--fixture-manifest-sha256")
    parser.add_argument("--expected-payload-sha256")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args(argv)
    if not 1 <= args.timeout_seconds <= 600:
        parser.error("--timeout-seconds must be between 1 and 600")
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parse_args(list(argv or sys.argv[1:]))
        if args.execute:
            if not all(
                (
                    args.executor,
                    args.executor_sha256,
                    args.fixture_manifest,
                    args.fixture_manifest_sha256,
                    args.expected_payload_sha256,
                )
            ):
                result = _blocked(core_sha256="", reasons=["controlled_lab_material_incomplete"])
            else:
                result = execute(
                    core_path=args.core_dll,
                    executor_path=args.executor,
                    executor_sha256=args.executor_sha256,
                    manifest_path=args.fixture_manifest,
                    manifest_sha256=args.fixture_manifest_sha256,
                    expected_payload_sha256=args.expected_payload_sha256,
                    timeout_seconds=args.timeout_seconds,
                )
        else:
            result = preflight(
                core_path=args.core_dll,
                executor_path=args.executor,
                executor_sha256=args.executor_sha256,
                manifest_path=args.fixture_manifest,
                manifest_sha256=args.fixture_manifest_sha256,
            )
        print(json.dumps(result, ensure_ascii=True, separators=(",", ":")))
        return 0 if result["classification"] in {"PASS", "READY_NOT_EXECUTED", "BLOCKED_BY_ACCESS"} else 1
    except ProofFailure as exc:
        print(
            json.dumps(
                {"schema_version": SCHEMA, "classification": "FAIL", "error_code": exc.code},
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )
        return 1
    except Exception:
        print(
            json.dumps(
                {"schema_version": SCHEMA, "classification": "FAIL", "error_code": "unexpected_failure"},
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
