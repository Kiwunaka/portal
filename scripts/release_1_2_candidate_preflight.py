"""Build a read-only POKROV 1.2.0 exact-candidate preflight report."""

from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "1.2.0"
CORE_TARGET_VERSION = "1.1.0"
VALID_INDEXES = {f"I{number}" for number in range(6)}
VALID_STAGES = {"pre_freeze", "candidate", "external", "deferred"}
VALID_EXTERNAL_GATES = {"pre_candidate", "post_candidate"}
STAGE_POLICY_RELATIVE_PATH = Path("shared/release-1.2.0-candidate-stage-policy.json")
RELEASE_INDEX_CONTRACT_PATH = Path("release-index.contract.json")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
BOUND_CORE_ARTIFACT_STATE = "exact_local_replacement_bound"
BOUND_STRUCTURED_EVENT_STATE = "bound_pre_candidate_local"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _git_identity(repo_root: Path) -> dict[str, Any]:
    revision = (
        subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        .stdout.strip()
        .lower()
    )
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()
    return {
        "revision": revision,
        "branch": branch,
        "working_tree_state": "dirty" if porcelain else "clean",
    }


def _git_optional(repo_root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def _release_index_contract(
    release_index_root: Path,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Validate the pre-candidate public-index policy without inventing a key."""

    blockers: list[dict[str, str]] = []

    def add(identifier: str, status: str, detail: str) -> None:
        blockers.append({"id": identifier, "status": status, "detail": detail})

    contract_path = release_index_root / RELEASE_INDEX_CONTRACT_PATH
    summary: dict[str, Any] = {
        "path": RELEASE_INDEX_CONTRACT_PATH.as_posix(),
        "status": "MISSING",
        "contract_sha256": None,
        "manifest_schema_sha256": None,
        "active_signing_keys": 0,
        "candidate_created": False,
        "promotion_authorized": False,
    }
    if not contract_path.is_file():
        add(
            "release_index_contract_missing",
            "BLOCKED_LOCAL_RELEASE_INDEX",
            "public release-index checkout has no fail-closed source contract",
        )
        return summary, blockers

    contract = _read_json(contract_path)
    summary["contract_sha256"] = _sha256_file(contract_path)
    errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            errors.append(field)

    require(contract.get("schema") == "pokrov.release-index.contract/v1", "schema")
    require(contract.get("repository") == "Kiwunaka/pokrov", "repository")
    require(contract.get("promotion_branch") == "main", "promotion_branch")
    require(
        contract.get("candidate_manifest_path") == "releases/1.2.0/release-index.json",
        "candidate_manifest_path",
    )
    target = contract.get("development_target", {})
    if not isinstance(target, dict):
        target = {}
    require(target.get("product_version") == TARGET_VERSION, "target.product_version")
    require(target.get("state") == "PRE_CANDIDATE_LOCAL", "target.state")
    require(target.get("candidate_created") is False, "target.candidate_created")
    require(
        target.get("promotion_authorized") is False,
        "target.promotion_authorized",
    )

    signature = contract.get("signature_policy", {})
    if not isinstance(signature, dict):
        signature = {}
    require(signature.get("algorithm") == "ed25519", "signature.algorithm")
    require(signature.get("threshold") == 1, "signature.threshold")
    require(
        signature.get("detached_signature_suffix") == ".sig",
        "signature.detached_signature_suffix",
    )
    require(
        signature.get("signed_payload") == "exact_manifest_bytes",
        "signature.signed_payload",
    )

    same_byte = contract.get("same_byte_policy", {})
    if not isinstance(same_byte, dict):
        same_byte = {}
    for field in (
        "require_artifact_sha256",
        "require_github_asset_digest_match",
        "require_manifest_signature",
        "stable_pointer_atomic",
    ):
        require(same_byte.get(field) is True, f"same_byte_policy.{field}")
    require(
        same_byte.get("rebuild_on_promotion") is False,
        "same_byte_policy.rebuild_on_promotion",
    )

    manifest_schema = contract.get("manifest_schema", {})
    if not isinstance(manifest_schema, dict):
        manifest_schema = {}
    schema_relative = manifest_schema.get("path")
    schema_declared_hash = str(manifest_schema.get("sha256") or "").lower()
    require(
        schema_relative == "schemas/release-index-manifest-v2.schema.json",
        "manifest_schema.path",
    )
    require(
        SHA256_PATTERN.fullmatch(schema_declared_hash) is not None,
        "manifest_schema.sha256",
    )
    schema_path = release_index_root / str(schema_relative or "")
    if schema_path.is_file():
        schema_actual_hash = _sha256_file(schema_path)
        summary["manifest_schema_sha256"] = schema_actual_hash
        require(schema_actual_hash == schema_declared_hash, "manifest_schema.bytes")
    else:
        require(False, "manifest_schema.file")

    keyring_relative = contract.get("trusted_keyring_path")
    require(
        keyring_relative == "trusted/release-signing-keys.json",
        "trusted_keyring_path",
    )
    keyring_path = release_index_root / str(keyring_relative or "")
    active_keys: list[dict[str, Any]] = []
    if keyring_path.is_file():
        keyring = _read_json(keyring_path)
        require(
            keyring.get("schema") == "pokrov.release-index.keyring/v1",
            "keyring.schema",
        )
        keys = keyring.get("keys", [])
        require(isinstance(keys, list), "keyring.keys")
        if isinstance(keys, list):
            for key in keys:
                if not isinstance(key, dict) or key.get("state") != "active":
                    continue
                encoded = key.get("public_key_base64")
                try:
                    decoded = base64.b64decode(encoded, validate=True)
                except (TypeError, ValueError):
                    decoded = b""
                if (
                    isinstance(key.get("id"), str)
                    and re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", key["id"])
                    and len(decoded) == 32
                ):
                    active_keys.append(key)
                else:
                    errors.append("keyring.active_key")
    else:
        require(False, "keyring.file")
    summary["active_signing_keys"] = len(active_keys)

    retained = contract.get("retained_public_release", {})
    if not isinstance(retained, dict):
        retained = {}
    require(retained.get("version") == "1.1.6", "retained.version")
    require(retained.get("tag") == "v1.1.6", "retained.tag")
    require(
        retained.get("trust_state") == "LEGACY_CHECKSUM_ONLY_NOT_CANDIDATE_ELIGIBLE",
        "retained.trust_state",
    )
    require(retained.get("manifest_signature") is False, "retained.signature")

    if errors:
        summary["status"] = "INVALID"
        add(
            "release_index_contract_invalid",
            "BLOCKED_LOCAL_RELEASE_INDEX",
            "invalid release-index source contract: " + ", ".join(errors),
        )
    elif not active_keys:
        summary["status"] = "BLOCKED_OWNER_SIGNING_KEY"
        add(
            "release_index_signing_key_missing",
            "BLOCKED_BY_OWNER_DECISION",
            "release-index contract has no active trusted Ed25519 public key",
        )
    else:
        summary["status"] = "CONTRACT_READY_PRE_CANDIDATE"
    return summary, blockers


def _pubspec_version(path: Path) -> str:
    match = re.search(
        r"^version:\s*([^\s]+)\s*$", path.read_text(encoding="utf-8"), re.MULTILINE
    )
    if match is None:
        raise ValueError(f"missing version in {path}")
    return match.group(1)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _core_artifact_binding(
    *,
    client_root: Path,
    runtime_seed: dict[str, Any],
    core_revision: str,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Validate exact local Core bytes and their fail-closed evidence contract."""

    blockers: list[dict[str, str]] = []

    def add(identifier: str, detail: str) -> None:
        blockers.append(
            {
                "id": identifier,
                "status": "BLOCKED_LOCAL_ARTIFACT",
                "detail": detail,
            }
        )

    core_target = runtime_seed.get("development_target", {})
    if not isinstance(core_target, dict):
        core_target = {}
    desktop_abi_seed = runtime_seed.get("desktop_abi", {})
    if not isinstance(desktop_abi_seed, dict):
        desktop_abi_seed = {}
    structured_events = desktop_abi_seed.get("structured_events", {})
    if not isinstance(structured_events, dict):
        structured_events = {}
    artifact_state = str(core_target.get("artifact_state") or "")
    structured_event_state = str(
        structured_events.get("exact_replacement_artifact") or ""
    )
    summary: dict[str, Any] = {
        "artifact_state": artifact_state,
        "structured_event_artifact_state": structured_event_state,
        "activation_state": str(runtime_seed.get("activation_state") or ""),
        "verified_exact_local_bytes": False,
        "files": {},
    }
    if (
        artifact_state != BOUND_CORE_ARTIFACT_STATE
        or structured_event_state != BOUND_STRUCTURED_EVENT_STATE
    ):
        add(
            "core_replacement_artifact_pending",
            "exact structured-event Core replacement artifact is not bound",
        )
        return summary, blockers

    provenance = runtime_seed.get("artifact_provenance", {})
    assets = runtime_seed.get("assets", {})
    desktop_abi = runtime_seed.get("desktop_abi", {})
    if not isinstance(provenance, dict):
        provenance = {}
    if not isinstance(assets, dict):
        assets = {}
    if not isinstance(desktop_abi, dict):
        desktop_abi = {}
    android = assets.get("android", {})
    windows = assets.get("windows", {})
    if not isinstance(android, dict):
        android = {}
    if not isinstance(windows, dict):
        windows = {}

    metadata_errors: list[str] = []

    def require(condition: bool, field: str) -> None:
        if not condition:
            metadata_errors.append(field)

    require(str(runtime_seed.get("version") or "") == CORE_TARGET_VERSION, "version")
    require(
        str(runtime_seed.get("source_commit") or "").lower() == core_revision,
        "source_commit",
    )
    require(runtime_seed.get("release_tag_created") is False, "release_tag_created")
    require(
        str(runtime_seed.get("activation_state") or "") == "active_pre_candidate_local",
        "activation_state",
    )
    require(
        str(provenance.get("status") or "") == "clean_reproducible_pre_candidate_local",
        "artifact_provenance.status",
    )
    require(
        str(provenance.get("evidence_ceiling") or "") == "PRE_CANDIDATE_LOCAL",
        "artifact_provenance.evidence_ceiling",
    )
    require(provenance.get("candidate_created") is False, "candidate_created")
    require(provenance.get("promotion_authorized") is False, "promotion_authorized")
    require(
        "release_url" in provenance and provenance.get("release_url") is None,
        "release_url",
    )
    require(
        str(provenance.get("vcs_stamp") or "")
        == "disabled_for_reproducible_release_artifacts",
        "artifact_provenance.vcs_stamp",
    )
    require(
        android.get("entry") == "pokrov-core.aar"
        and android.get("sync_destination") == "apps/android_shell/android/app/libs"
        and android.get("sync_policy") == "exact_pre_candidate_build",
        "assets.android",
    )
    require(
        str(android.get("source_commit") or "").lower() == core_revision,
        "assets.android.source_commit",
    )
    require(
        windows.get("entry") == "pokrov-core.dll"
        and windows.get("sync_destination")
        == "apps/windows_shell/windows/runner/resources/runtime"
        and windows.get("sync_policy") == "exact_pre_candidate_build",
        "assets.windows",
    )
    require(
        str(windows.get("source_commit") or "").lower() == core_revision,
        "assets.windows.source_commit",
    )
    require(
        windows.get("runtime_dependencies") == ["libcronet.dll"],
        "assets.windows.runtime_dependencies",
    )
    require(
        structured_events.get("callback_symbol") == "pokrovCoreSetEventCallback"
        and structured_events.get("context_symbol") == "pokrovCoreSetEventContext",
        "desktop_abi.structured_events.symbols",
    )
    required_capabilities = desktop_abi.get("required_capabilities", [])
    require(
        isinstance(required_capabilities, list)
        and "structured_operational_events" in required_capabilities,
        "desktop_abi.required_capabilities",
    )

    build = provenance.get("reproducible_build", {})
    evidence = provenance.get("artifact_evidence", {})
    if not isinstance(build, dict):
        build = {}
    if not isinstance(evidence, dict):
        evidence = {}
    android_build = build.get("android", {})
    windows_build = build.get("windows", {})
    android_evidence = evidence.get("android", {})
    windows_evidence = evidence.get("windows", {})
    sbom = evidence.get("sbom", [])
    for value, name in (
        (android_build, "reproducible_build.android"),
        (windows_build, "reproducible_build.windows"),
        (android_evidence, "artifact_evidence.android"),
        (windows_evidence, "artifact_evidence.windows"),
    ):
        require(isinstance(value, dict), name)
    if not isinstance(android_build, dict):
        android_build = {}
    if not isinstance(windows_build, dict):
        windows_build = {}
    if not isinstance(android_evidence, dict):
        android_evidence = {}
    if not isinstance(windows_evidence, dict):
        windows_evidence = {}

    for value, field in (
        (android_build.get("source_commit"), "reproducible_build.android.source_commit"),
        (windows_build.get("source_commit"), "reproducible_build.windows.source_commit"),
        (android_evidence.get("source_commit"), "artifact_evidence.android.source_commit"),
        (windows_evidence.get("source_commit"), "artifact_evidence.windows.source_commit"),
    ):
        require(str(value or "").lower() == core_revision, field)

    require(
        android_evidence.get("result") == "PASS_BYTE_IDENTICAL_TWO_BUILDS",
        "artifact_evidence.android.result",
    )
    android_abis = android_evidence.get("abis", [])
    require(
        isinstance(android_abis, list)
        and all(isinstance(value, str) for value in android_abis)
        and set(android_abis) == {"armeabi-v7a", "arm64-v8a", "x86", "x86_64"},
        "artifact_evidence.android.abis",
    )
    require(
        windows_evidence.get("result") == "PASS_BYTE_IDENTICAL_TWO_BUILDS",
        "artifact_evidence.windows.result",
    )
    require(
        windows_evidence.get("required_exports") == 15,
        "artifact_evidence.windows.required_exports",
    )
    require(
        windows_evidence.get("proxy_only_start_stop_cycles") == 100
        and windows_evidence.get("proxy_only_result") == "PASS_LOCAL",
        "artifact_evidence.windows.proxy_only",
    )
    for value, field in (
        (android_evidence.get("tree_sha256"), "artifact_evidence.android.tree_sha256"),
        (
            android_evidence.get("evidence_sha256"),
            "artifact_evidence.android.evidence_sha256",
        ),
        (windows_evidence.get("tree_sha256"), "artifact_evidence.windows.tree_sha256"),
        (
            windows_evidence.get("evidence_sha256"),
            "artifact_evidence.windows.evidence_sha256",
        ),
    ):
        require(
            isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None,
            field,
        )
    sbom_map = (
        {
            str(item.get("name") or ""): str(item.get("sha256") or "")
            for item in sbom
            if isinstance(item, dict)
        }
        if isinstance(sbom, list)
        else {}
    )
    require(
        isinstance(sbom, list)
        and len(sbom) == 2
        and set(sbom_map) == {"pokrov-core.cdx.json", "sing-box.cdx.json"}
        and all(SHA256_PATTERN.fullmatch(value) for value in sbom_map.values()),
        "artifact_evidence.sbom",
    )

    file_contracts = (
        (
            "android",
            client_root / "apps/android_shell/android/app/libs/pokrov-core.aar",
            android.get("size"),
            android.get("sha256"),
            android_build.get("size"),
            android_build.get("sha256"),
        ),
        (
            "windows",
            client_root
            / "apps/windows_shell/windows/runner/resources/runtime/pokrov-core.dll",
            windows.get("size"),
            windows.get("sha256"),
            windows_build.get("size"),
            windows_build.get("sha256"),
        ),
        (
            "libcronet",
            client_root
            / "apps/windows_shell/windows/runner/resources/runtime/libcronet.dll",
            (windows.get("runtime_dependency_size") or {}).get("libcronet.dll")
            if isinstance(windows.get("runtime_dependency_size"), dict)
            else None,
            (windows.get("runtime_dependency_sha256") or {}).get("libcronet.dll")
            if isinstance(windows.get("runtime_dependency_sha256"), dict)
            else None,
            None,
            build.get("libcronet_sha256"),
        ),
    )
    byte_errors: list[str] = []
    for (
        label,
        path,
        declared_size,
        declared_hash,
        build_size,
        build_hash,
    ) in file_contracts:
        declared_hash = str(declared_hash or "").lower()
        build_hash = str(build_hash or "").lower()
        contract_valid = (
            isinstance(declared_size, int)
            and declared_size > 0
            and SHA256_PATTERN.fullmatch(declared_hash) is not None
            and (build_size is None or build_size == declared_size)
            and build_hash == declared_hash
        )
        if not path.is_file():
            actual_size = None
            actual_hash = None
            byte_errors.append(f"{label}:missing")
        else:
            actual_size = path.stat().st_size
            actual_hash = _sha256_file(path)
            if (
                not contract_valid
                or actual_size != declared_size
                or actual_hash != declared_hash
            ):
                byte_errors.append(f"{label}:identity")
        summary["files"][label] = {
            "path": path.relative_to(client_root).as_posix(),
            "declared_size": declared_size,
            "declared_sha256": declared_hash,
            "actual_size": actual_size,
            "actual_sha256": actual_hash,
            "match": contract_valid
            and actual_size == declared_size
            and actual_hash == declared_hash,
        }

    if metadata_errors:
        add(
            "core_artifact_binding_metadata_invalid",
            "invalid exact Core artifact metadata: " + ", ".join(metadata_errors),
        )
    if byte_errors:
        add(
            "core_artifact_binding_bytes_invalid",
            "exact Core artifact byte identity failed: " + ", ".join(byte_errors),
        )
    summary["verified_exact_local_bytes"] = not blockers
    return summary, blockers


def _load_ledger(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    keys: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["plan"], row["id"])
        if key in keys:
            raise ValueError(f"duplicate ledger key {key}")
        keys.add(key)
        if row["index"] not in VALID_INDEXES:
            raise ValueError(f"invalid index for {key}: {row['index']}")
    if not rows:
        raise ValueError("execution ledger must contain at least one row")
    return rows


def _load_stage_policy(
    path: Path, rows: list[dict[str, str]]
) -> tuple[dict[str, Any], dict[tuple[str, str], dict[str, str]]]:
    policy = _read_json(path)
    if policy.get("schema") != "pokrov.release-1.2.0.row-stage-policy/v1":
        raise ValueError("candidate stage policy schema is unsupported")
    if policy.get("default_stage") != "pre_freeze":
        raise ValueError("candidate stage policy must fail safe to pre_freeze")
    stages = policy.get("stages")
    if not isinstance(stages, dict) or set(stages) != VALID_STAGES:
        raise ValueError("candidate stage policy must define the four exact stages")
    if any(
        not isinstance(value, str) or not value.strip() for value in stages.values()
    ):
        raise ValueError("candidate stage descriptions must be non-empty strings")

    ledger_keys = {(row["plan"], row["id"]) for row in rows}
    assignments = {
        key: {
            "stage": "pre_freeze",
            "reason": "Fail-safe default: local I3 is required before candidate creation.",
        }
        for key in ledger_keys
    }
    overrides = policy.get("overrides")
    if not isinstance(overrides, list):
        raise ValueError("candidate stage policy overrides must be a list")
    seen: set[tuple[str, str]] = set()
    for position, raw_override in enumerate(overrides):
        if not isinstance(raw_override, dict):
            raise ValueError(f"candidate stage override {position} must be an object")
        allowed_fields = {"plan", "id", "stage", "reason", "external_gate"}
        extra_fields = set(raw_override) - allowed_fields
        if extra_fields:
            raise ValueError(
                f"candidate stage override {position} has unsupported fields: "
                f"{sorted(extra_fields)}"
            )
        plan = raw_override.get("plan")
        identifier = raw_override.get("id")
        stage = raw_override.get("stage")
        reason = raw_override.get("reason")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (plan, identifier, stage, reason)
        ):
            raise ValueError(
                f"candidate stage override {position} has an empty required field"
            )
        key = (plan, identifier)
        if key not in ledger_keys:
            raise ValueError(
                f"candidate stage override references unknown ledger key {key}"
            )
        if key in seen:
            raise ValueError(f"duplicate candidate stage override for {key}")
        seen.add(key)
        if stage not in VALID_STAGES:
            raise ValueError(f"invalid candidate stage for {key}: {stage}")
        external_gate = raw_override.get("external_gate")
        if stage == "external":
            if external_gate not in VALID_EXTERNAL_GATES:
                raise ValueError(
                    f"external candidate stage for {key} needs an exact external_gate"
                )
        elif external_gate is not None:
            raise ValueError(
                f"non-external candidate stage for {key} cannot set external_gate"
            )
        assignment = {"stage": stage, "reason": reason.strip()}
        if stage == "external":
            assignment["external_gate"] = external_gate
        assignments[key] = assignment

    return (
        {
            "schema": policy["schema"],
            "path": STAGE_POLICY_RELATIVE_PATH.as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "default_stage": policy["default_stage"],
            "override_count": len(overrides),
            "ledger_row_count": len(assignments),
        },
        assignments,
    )


def _pending_lane(row: dict[str, str]) -> str:
    status = row["status"].upper()
    if "NOT_AUTHORIZED" in status:
        return "not_authorized"
    if "BLOCKED_BY_ACCESS" in status:
        return "blocked_by_access"
    if "BLOCKED_BY_OWNER" in status:
        return "blocked_by_owner_decision"
    if "MANUAL_OWNER_TEST" in status:
        return "manual_owner_test"
    if "NOT_REQUESTED" in status:
        return "not_requested"
    if "DEFERRED" in status:
        return "deferred"
    if "MONITOR_ONLY" in status:
        return "monitor_only"
    if row["phase"] == "P11":
        return "phase_11_local_or_candidate"
    return "local_closure_or_candidate_dependency"


def _stage_blockers(pending_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    pre_freeze = [row for row in pending_rows if row["stage"] == "pre_freeze"]
    external_pre_candidate = [
        row
        for row in pending_rows
        if row["stage"] == "external" and row.get("external_gate") == "pre_candidate"
    ]
    if pre_freeze:
        blockers.append(
            {
                "id": "ledger_pre_freeze_incomplete",
                "status": "BLOCKED_LOCAL_FREEZE",
                "detail": (
                    f"{len(pre_freeze)} explicitly staged rows remain below local I3"
                ),
            }
        )
    if external_pre_candidate:
        blockers.append(
            {
                "id": "ledger_external_pre_candidate_incomplete",
                "status": "BLOCKED_EXTERNAL_PRECONDITION",
                "detail": (
                    f"{len(external_pre_candidate)} external pre-candidate rows remain unresolved"
                ),
            }
        )
    return blockers


def _target_contract_blockers(
    *,
    versions: dict[str, str],
    handoff_target: dict[str, Any],
    core_release: dict[str, Any],
    core_target: dict[str, Any],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []

    def add(identifier: str, detail: str) -> None:
        blockers.append(
            {
                "id": identifier,
                "status": "BLOCKED_LOCAL_CONTRACT",
                "detail": detail,
            }
        )

    android_product = versions["android"].split("+", 1)[0]
    windows_product = versions["windows"].split("+", 1)[0]
    if android_product != windows_product:
        add("client_shell_version_drift", "Android and Windows product versions differ")
    if android_product != TARGET_VERSION or versions["app_shell"] != TARGET_VERSION:
        add(
            "client_target_version_stale",
            f"active client packages must target {TARGET_VERSION}",
        )
    handoff_product = str(handoff_target.get("product_version") or "")
    handoff_build = handoff_target.get("platform_build")
    handoff_package = str(handoff_target.get("package_version") or "")
    valid_handoff_build = (
        isinstance(handoff_build, int)
        and not isinstance(handoff_build, bool)
        and handoff_build > 0
    )
    expected_package = (
        f"{TARGET_VERSION}+{handoff_build}" if valid_handoff_build else None
    )
    if (
        versions["android"] != versions["windows"]
        or (
            expected_package is not None
            and (
                versions["android"] != expected_package
                or versions["windows"] != expected_package
            )
        )
    ):
        add(
            "client_build_number_drift",
            "active Android and Windows shells must match the exact package "
            "version owned by release-handoff.seed.json",
        )
    if (
        handoff_product != TARGET_VERSION
        or not valid_handoff_build
        or expected_package is None
        or handoff_package != expected_package
        or str(handoff_target.get("state") or "") != "PRE_CANDIDATE_LOCAL"
        or handoff_target.get("candidate_created") is not False
    ):
        add(
            "client_handoff_target_invalid",
            "release-handoff development target is not the exact pre-candidate contract",
        )
    if (
        str(core_release.get("version") or "") != CORE_TARGET_VERSION
        or str(core_release.get("state") or "") != "PRE_CANDIDATE_LOCAL"
        or core_release.get("candidate_created") is not False
    ):
        add(
            "core_source_target_invalid",
            f"Core source must identify {CORE_TARGET_VERSION} PRE_CANDIDATE_LOCAL",
        )
    if (
        str(core_target.get("required_for_product") or "") != TARGET_VERSION
        or str(core_target.get("version") or "") != CORE_TARGET_VERSION
        or str(core_target.get("release_tag") or "") != f"v{CORE_TARGET_VERSION}"
        or str(core_target.get("state") or "") != "PRE_CANDIDATE_LOCAL"
        or core_target.get("candidate_created") is not False
        or str(core_target.get("artifact_state") or "")
        not in {"pending", BOUND_CORE_ARTIFACT_STATE}
    ):
        add(
            "client_core_target_invalid",
            "client Core development target disagrees with the pre-candidate source contract",
        )
    return blockers


def build_report(
    *,
    platform_root: Path,
    client_root: Path,
    core_root: Path,
    release_index_root: Path | None,
    ledger_root: Path | None = None,
) -> dict[str, Any]:
    ledger_source_root = ledger_root or platform_root
    ledger_path = (
        ledger_source_root
        / "docs/developer/work-orders/2026-08-21--release-1.2.0-megaplan/EXECUTION-LEDGER.csv"
    )
    rows = _load_ledger(ledger_path)
    stage_policy, stage_assignments = _load_stage_policy(
        platform_root / STAGE_POLICY_RELATIVE_PATH, rows
    )
    pending = [row for row in rows if int(row["index"][1:]) < 3]
    sources = {
        "platform": _git_identity(platform_root),
        "client": _git_identity(client_root),
        "core": _git_identity(core_root),
    }
    ledger_source = _git_identity(ledger_source_root)
    preflight_tool = {
        **_git_identity(REPO_ROOT),
        "script_sha256": _sha256_file(Path(__file__).resolve()),
    }
    blockers: list[dict[str, str]] = []
    for name, value in sources.items():
        if value["working_tree_state"] != "clean":
            blockers.append(
                {
                    "id": f"{name}_worktree_dirty",
                    "status": "BLOCKED_LOCAL_FREEZE",
                    "detail": "exact candidate identity requires a clean committed revision",
                }
            )
    if ledger_source["working_tree_state"] != "clean":
        blockers.append(
            {
                "id": "ledger_worktree_dirty",
                "status": "BLOCKED_LOCAL_FREEZE",
                "detail": "execution ledger evidence requires a clean committed revision",
            }
        )
    if preflight_tool["working_tree_state"] != "clean":
        blockers.append(
            {
                "id": "preflight_tool_worktree_dirty",
                "status": "BLOCKED_LOCAL_FREEZE",
                "detail": "candidate preflight tool requires a clean committed revision",
            }
        )

    release_index: dict[str, Any]
    if release_index_root is None or not (release_index_root / ".git").exists():
        release_index = {"status": "BLOCKED_BY_ACCESS"}
        blockers.append(
            {
                "id": "release_index_missing",
                "status": "BLOCKED_BY_ACCESS",
                "detail": "public release-index repository/revision is unavailable",
            }
        )
    else:
        release_index = {"status": "AVAILABLE", **_git_identity(release_index_root)}
        if release_index["working_tree_state"] != "clean":
            blockers.append(
                {
                    "id": "release_index_worktree_dirty",
                    "status": "BLOCKED_LOCAL_FREEZE",
                    "detail": "release-index revision must be clean",
                }
            )
        remote_url = _git_optional(
            release_index_root, "config", "--get", "remote.origin.url"
        )
        published_revision = _git_optional(
            release_index_root, "rev-parse", "refs/remotes/origin/main"
        )
        release_index["remote_url"] = remote_url
        release_index["published_revision"] = published_revision
        release_index["head_is_published_main"] = (
            published_revision == release_index["revision"]
        )
        normalized_remote = (remote_url or "").lower().removesuffix(".git")
        if normalized_remote not in {
            "https://github.com/kiwunaka/pokrov",
            "git@github.com:kiwunaka/pokrov",
        }:
            blockers.append(
                {
                    "id": "release_index_remote_invalid",
                    "status": "BLOCKED_LOCAL_CONTRACT",
                    "detail": "release-index checkout does not bind Kiwunaka/pokrov",
                }
            )
        if published_revision != release_index["revision"]:
            blockers.append(
                {
                    "id": "release_index_revision_unpublished",
                    "status": "BLOCKED_EXTERNAL_PRECONDITION",
                    "detail": "release-index HEAD is not the fetched public origin/main revision",
                }
            )
        release_index_contract, release_index_blockers = _release_index_contract(
            release_index_root
        )
        release_index["contract"] = release_index_contract
        blockers.extend(release_index_blockers)

    versions = {
        "target": TARGET_VERSION,
        "android": _pubspec_version(client_root / "apps/android_shell/pubspec.yaml"),
        "windows": _pubspec_version(client_root / "apps/windows_shell/pubspec.yaml"),
        "app_shell": _pubspec_version(client_root / "packages/app_shell/pubspec.yaml"),
    }
    core_release = _read_json(core_root / "config/release.json")
    runtime_seed = _read_json(client_root / "config/runtime-artifacts.seed.json")[
        "core"
    ]
    handoff_target = _read_json(client_root / "config/release-handoff.seed.json")[
        "release_truth"
    ]["development_target"]
    core_target = runtime_seed.get("development_target", {})
    if not isinstance(core_target, dict):
        core_target = {}
    blockers.extend(
        _target_contract_blockers(
            versions=versions,
            handoff_target=handoff_target,
            core_release=core_release,
            core_target=core_target,
        )
    )
    core_state = {
        "source_version": str(core_release.get("version") or ""),
        "source_state": str(core_release.get("state") or ""),
        "source_revision": sources["core"]["revision"],
        "seed_version": str(runtime_seed.get("version") or ""),
        "target_version": str(core_target.get("version") or ""),
        "target_state": str(core_target.get("state") or ""),
        "seed_source_revision": str(runtime_seed.get("source_commit") or "").lower(),
        "seed_structured_event_artifact": str(
            runtime_seed.get("desktop_abi", {})
            .get("structured_events", {})
            .get("exact_replacement_artifact", "")
        ),
    }
    if core_state["seed_source_revision"] != core_state["source_revision"]:
        blockers.append(
            {
                "id": "client_core_seed_revision_stale",
                "status": "BLOCKED_LOCAL_ARTIFACT",
                "detail": "client runtime seed does not bind the active Core source revision",
            }
        )
    artifact_binding, artifact_blockers = _core_artifact_binding(
        client_root=client_root,
        runtime_seed=runtime_seed,
        core_revision=core_state["source_revision"],
    )
    core_state["artifact_binding"] = artifact_binding
    blockers.extend(artifact_blockers)

    pending_rows: list[dict[str, Any]] = []
    for row in pending:
        assignment = stage_assignments[(row["plan"], row["id"])]
        pending_row: dict[str, Any] = {
            "plan": row["plan"],
            "id": row["id"],
            "phase": row["phase"],
            "index": row["index"],
            "status": row["status"],
            "lane": _pending_lane(row),
            "stage": assignment["stage"],
            "stage_reason": assignment["reason"],
            "summary": row["summary"],
            "next_action": row["next_action"],
        }
        if "external_gate" in assignment:
            pending_row["external_gate"] = assignment["external_gate"]
        pending_rows.append(pending_row)
    blockers.extend(_stage_blockers(pending_rows))
    lane_counts: dict[str, int] = {}
    stage_counts: dict[str, int] = {}
    for row in pending_rows:
        lane_counts[row["lane"]] = lane_counts.get(row["lane"], 0) + 1
        stage_counts[row["stage"]] = stage_counts.get(row["stage"], 0) + 1
    external_pre_candidate_count = sum(
        row.get("external_gate") == "pre_candidate" for row in pending_rows
    )

    return {
        "schema": "pokrov.release-1.2.candidate-preflight/v1",
        "captured_at_utc": datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z"),
        "status": "BLOCKED" if blockers else "READY_LOCAL_FREEZE",
        "candidate_created": False,
        "candidate_proven": False,
        "promotion_authorized": False,
        "preflight_tool": preflight_tool,
        "sources": sources,
        "release_index": release_index,
        "versions": versions,
        "core": core_state,
        "stage_policy": stage_policy,
        "ledger": {
            "source": ledger_source,
            "total": len(rows),
            "below_i3": len(pending_rows),
            "pre_freeze_rows_below_i3": stage_counts.get("pre_freeze", 0),
            "candidate_rows_below_i3": stage_counts.get("candidate", 0),
            "external_rows_below_i3": stage_counts.get("external", 0),
            "external_pre_candidate_rows_below_i3": external_pre_candidate_count,
            "deferred_rows_below_i3": stage_counts.get("deferred", 0),
            "pending_stage_counts": dict(sorted(stage_counts.items())),
            "pending_lane_counts": dict(sorted(lane_counts.items())),
            "pending_rows": pending_rows,
        },
        "blockers": blockers,
        "evidence_ceiling": "LOCAL_READ_ONLY_PREFLIGHT",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--ledger-root",
        type=Path,
        help=(
            "Clean post-freeze evidence checkout that owns EXECUTION-LEDGER.csv; "
            "defaults to --platform-root."
        ),
    )
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--release-index-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--expect-blocked",
        action="store_true",
        help="Return success only when the honest current status is BLOCKED.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report(
            platform_root=args.platform_root.resolve(),
            client_root=args.client_root.resolve(),
            core_root=args.core_root.resolve(),
            ledger_root=args.ledger_root.resolve() if args.ledger_root else None,
            release_index_root=args.release_index_root.resolve()
            if args.release_index_root
            else None,
        )
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"CANDIDATE_PREFLIGHT_ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "blockers": len(report["blockers"]),
                "candidate_created": False,
                "candidate_rows_below_i3": report["ledger"]["candidate_rows_below_i3"],
                "deferred_rows_below_i3": report["ledger"]["deferred_rows_below_i3"],
                "external_pre_candidate_rows_below_i3": report["ledger"][
                    "external_pre_candidate_rows_below_i3"
                ],
                "ledger_below_i3": report["ledger"]["below_i3"],
                "output": str(output),
                "pre_freeze_rows_below_i3": report["ledger"][
                    "pre_freeze_rows_below_i3"
                ],
                "status": report["status"],
            },
            sort_keys=True,
        )
    )
    if args.expect_blocked:
        return 0 if report["status"] == "BLOCKED" else 1
    return 0 if report["status"] == "READY_LOCAL_FREEZE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
