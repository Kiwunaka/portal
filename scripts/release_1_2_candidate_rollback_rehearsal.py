#!/usr/bin/env python3
"""Run an isolated portal + client-channel rollback rehearsal.

The rehearsal binds a signed 1.2.0 release-index candidate to a strict-v2
release handoff, drives the client-owned stable-pointer switch in a temporary
fixture, and projects the same handoffs through the portal runtime consumer.
It never writes the tracked client catalog/pointer or a remote runtime.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import release_1_2_pb14_candidate_gate as candidate_gate  # noqa: E402
import remote_brain_apply_release_handoff as portal_handoff  # noqa: E402
import validate_release_handoff_metadata as handoff_validator  # noqa: E402


class RollbackRehearsalError(RuntimeError):
    """Raised when an exact-candidate rollback invariant fails."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RollbackRehearsalError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RollbackRehearsalError(f"invalid JSON input: {path}") from exc
    if not isinstance(value, dict):
        raise RollbackRehearsalError(f"JSON input must be an object: {path}")
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False).rstrip()
        + "\n"
    ).encode("utf-8")


def _write_new(path: Path, value: Mapping[str, Any]) -> None:
    if path.exists():
        raise RollbackRehearsalError(f"refusing to overwrite output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))


def _write_new_bytes(path: Path, value: bytes) -> None:
    if path.exists():
        raise RollbackRehearsalError(f"refusing to overwrite output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _source_tuple(manifest: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    raw_sources = manifest.get("sources")
    if not isinstance(raw_sources, Mapping):
        raise RollbackRehearsalError("signed manifest source tuple is missing")
    result: dict[str, dict[str, str]] = {}
    for name in ("platform", "client", "core", "release_index"):
        raw = raw_sources.get(name)
        if not isinstance(raw, Mapping):
            raise RollbackRehearsalError(f"signed manifest source is missing: {name}")
        repository = str(raw.get("repository") or "")
        revision = str(raw.get("commit") or "").lower()
        if not repository or candidate_gate.GIT_REVISION_RE.fullmatch(revision) is None:
            raise RollbackRehearsalError(f"signed manifest source is invalid: {name}")
        result[name] = {"repository": repository, "revision": revision}
    return result


def _bind_candidate_artifacts(
    handoff_artifacts: Sequence[Mapping[str, Any]],
    manifest_artifacts: Any,
    client_revision: str,
) -> None:
    if not isinstance(manifest_artifacts, list):
        raise RollbackRehearsalError("signed manifest artifacts are missing")
    by_name: dict[str, Mapping[str, Any]] = {}
    for raw in manifest_artifacts:
        if not isinstance(raw, Mapping):
            raise RollbackRehearsalError("signed manifest artifact is invalid")
        name = str(raw.get("name") or "")
        if not name or name in by_name:
            raise RollbackRehearsalError("signed manifest artifact name is invalid")
        by_name[name] = raw

    observed: set[str] = set()
    for artifact in handoff_artifacts:
        name = str(artifact.get("file_name") or "")
        signed = by_name.get(name)
        if signed is None:
            raise RollbackRehearsalError(f"handoff artifact is unsigned: {name}")
        expected = {
            "platform": str(signed.get("platform") or ""),
            "kind": str(signed.get("kind") or ""),
            "sha256": str(signed.get("sha256") or "").lower(),
            "size_bytes": int(signed.get("size") or -1),
        }
        actual = {
            "platform": str(artifact.get("platform") or ""),
            "kind": str(artifact.get("kind") or ""),
            "sha256": str(artifact.get("sha256") or "").lower(),
            "size_bytes": int(artifact.get("size_bytes") or -1),
        }
        if actual != expected:
            raise RollbackRehearsalError(f"signed artifact drift: {name}")
        if str(artifact.get("source_revision") or "").lower() != client_revision:
            raise RollbackRehearsalError(f"artifact source drift: {name}")
        observed.add(name)
    if observed != set(by_name):
        raise RollbackRehearsalError("handoff and signed manifest artifact sets differ")


def bind_candidate_handoff(
    candidate_input: Mapping[str, Any],
    signed_manifest: Mapping[str, Any],
    binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate a generated strict-v2 handoff against the signed candidate."""

    candidate_label = str(binding.get("candidate_label") or "")
    if candidate_label != str(signed_manifest.get("candidate_id") or ""):
        raise RollbackRehearsalError("candidate binding label mismatch")
    product = signed_manifest.get("product")
    release = candidate_input.get("release")
    sources = candidate_input.get("sources")
    compatibility = candidate_input.get("compatibility")
    artifacts = candidate_input.get("artifacts")
    if not all(
        isinstance(value, Mapping)
        for value in (product, release, sources, compatibility)
    ) or not isinstance(artifacts, list):
        raise RollbackRehearsalError("generated candidate handoff is incomplete")
    if str(product.get("version") or "") != str(release.get("version") or ""):
        raise RollbackRehearsalError("candidate version drift")
    expected_sources = _source_tuple(signed_manifest)
    if dict(sources) != expected_sources:
        raise RollbackRehearsalError("candidate handoff source tuple drift")
    handoff_artifacts = copy.deepcopy(artifacts)
    _bind_candidate_artifacts(
        handoff_artifacts,
        signed_manifest.get("artifacts"),
        expected_sources["client"]["revision"],
    )
    handoff_label = str(release.get("candidate_label") or "")
    if handoff_label != f"pokrov-{release.get('version', '')}":
        raise RollbackRehearsalError("candidate handoff label is invalid")
    manifest_compatibility = signed_manifest.get("compatibility")
    if not isinstance(manifest_compatibility, Mapping) or str(
        compatibility.get("core_version") or ""
    ) != str(manifest_compatibility.get("core_version") or ""):
        raise RollbackRehearsalError("candidate Core version drift")
    try:
        summary = handoff_validator.validate_metadata(dict(candidate_input))
    except handoff_validator.ValidationIssue as exc:
        raise RollbackRehearsalError(
            f"generated candidate handoff is invalid: {exc.code}"
        ) from exc
    return {
        "classification": summary.classification,
        "schema_version": summary.schema_version,
        "release_id": handoff_label,
        "release_version": str(release.get("version") or ""),
        "artifact_count": summary.artifact_count,
        "blocking_gate_count": summary.blocking_gate_count,
    }


def prepare_generator_input(
    candidate_input: Mapping[str, Any], signed_manifest: Mapping[str, Any]
) -> dict[str, Any]:
    """Bind the release-index source after signing without changing artifact input."""

    result = copy.deepcopy(dict(candidate_input))
    sources = result.get("sources")
    if not isinstance(sources, dict):
        raise RollbackRehearsalError("candidate generator sources are missing")
    expected = _source_tuple(signed_manifest)
    for name in ("platform", "core"):
        raw = sources.get(name)
        if not isinstance(raw, Mapping) or dict(raw) != expected[name]:
            raise RollbackRehearsalError(f"candidate generator source drift: {name}")
    release_index = sources.get("release_index")
    if not isinstance(release_index, dict) or str(
        release_index.get("repository") or ""
    ) != expected["release_index"]["repository"]:
        raise RollbackRehearsalError("candidate generator release-index source drift")
    release_index["revision"] = expected["release_index"]["revision"]
    return result


def _handoff_identity(payload: Mapping[str, Any]) -> tuple[str, str, int]:
    schema = int(payload.get("schema_version") or 0)
    if schema == 1:
        release_id = str(payload.get("release_id") or "")
        version = str(payload.get("release_version") or "")
    elif schema == 2:
        release = payload.get("release")
        if not isinstance(release, Mapping):
            raise RollbackRehearsalError("handoff-v2 release identity is missing")
        release_id = str(release.get("candidate_label") or "")
        version = str(release.get("version") or "")
    else:
        raise RollbackRehearsalError(f"unsupported handoff schema: {schema}")
    if not release_id or not version:
        raise RollbackRehearsalError("handoff release identity is incomplete")
    return release_id, version, schema


def build_isolated_catalog(
    *,
    artifact_root: Path,
    stable_path: Path,
    candidate_path: Path,
    stable_identity: tuple[str, str, int],
    candidate_identity: tuple[str, str, int],
) -> dict[str, Any]:
    stable_id, stable_version, stable_schema = stable_identity
    candidate_id, candidate_version, candidate_schema = candidate_identity
    try:
        stable_relative = stable_path.resolve().relative_to(artifact_root.resolve())
        candidate_relative = candidate_path.resolve().relative_to(
            artifact_root.resolve()
        )
    except ValueError as exc:
        raise RollbackRehearsalError(
            "rollback target must stay under the isolated artifact root"
        ) from exc
    return {
        "schema_version": 1,
        "channel": "stable",
        "artifact_root": "../artifacts/releases",
        "stable_pointer": {"path": "release-handoff.json"},
        "rollback_targets": [
            {
                "release_id": stable_id,
                "release_version": stable_version,
                "handoff_schema_version": stable_schema,
                "handoff_path": stable_relative.as_posix(),
                "handoff_sha256": _sha256_file(stable_path),
                "eligibility": "ROLLBACK_ELIGIBLE",
                "platforms": ["android", "windows"],
            },
            {
                "release_id": candidate_id,
                "release_version": candidate_version,
                "handoff_schema_version": candidate_schema,
                "handoff_path": candidate_relative.as_posix(),
                "handoff_sha256": _sha256_file(candidate_path),
                "eligibility": "ROLLBACK_ELIGIBLE",
                "platforms": ["android", "windows"],
            },
        ],
        "mutation_policy": {
            "atomic_replace_required": True,
            "optimistic_lock_required": True,
            "backup_required": True,
            "same_byte_target_required": True,
            "exact_candidate_gate_required": True,
        },
    }


def portal_round_trip(
    stable_handoff: Path, candidate_handoff: Path
) -> dict[str, Any]:
    stable_values = portal_handoff._read_release_metadata(stable_handoff)
    candidate_values = portal_handoff._read_release_metadata(candidate_handoff)
    for label, values in (("stable", stable_values), ("candidate", candidate_values)):
        failures = portal_handoff._validate_release_env(values)
        if failures:
            raise RollbackRehearsalError(
                f"portal {label} projection failed: {'; '.join(failures)}"
            )
    original = "UNRELATED_SETTING=preserved\n"
    before = portal_handoff._rewrite_env(original, stable_values)
    forward = portal_handoff._rewrite_env(before, candidate_values)
    rollback = portal_handoff._rewrite_env(forward, stable_values)
    if rollback != before:
        raise RollbackRehearsalError("portal env rollback was not byte-identical")
    if "UNRELATED_SETTING=preserved" not in rollback:
        raise RollbackRehearsalError("portal env rollback lost an unrelated setting")
    return {
        "status": "PASS_LOCAL",
        "before_sha256": _sha256_bytes(before.encode("utf-8")),
        "forward_sha256": _sha256_bytes(forward.encode("utf-8")),
        "rollback_sha256": _sha256_bytes(rollback.encode("utf-8")),
        "rollback_byte_identical": rollback == before,
        "unrelated_setting_preserved": True,
        "candidate_label": candidate_values.get("APP_RELEASE_CANDIDATE_LABEL", ""),
        "candidate_handoff_sha256": candidate_values.get(
            "APP_RELEASE_HANDOFF_SHA256", ""
        ),
        "candidate_artifact_set_sha256": candidate_values.get(
            "APP_RELEASE_ARTIFACT_SET_SHA256", ""
        ),
        "candidate_android_sha256": candidate_values.get("APP_ANDROID_SHA256", ""),
        "candidate_windows_sha256": candidate_values.get("APP_WINDOWS_SHA256", ""),
    }


def _powershell_executable() -> str:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if executable is None:
        raise RollbackRehearsalError("PowerShell is required for the client pointer")
    return executable


def _git_revision(root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    revision = completed.stdout.strip().lower()
    if completed.returncode != 0 or candidate_gate.GIT_REVISION_RE.fullmatch(
        revision
    ) is None:
        raise RollbackRehearsalError(f"could not resolve Git revision: {root}")
    return revision


def _generate_candidate_handoff(
    *,
    client_root: Path,
    platform_root: Path,
    core_root: Path,
    generator_input: Mapping[str, Any],
    temporary_root: Path,
) -> Path:
    generator = client_root / "scripts" / "new-release-handoff-v2.ps1"
    if not generator.is_file():
        raise RollbackRehearsalError(f"client handoff generator is missing: {generator}")
    input_path = temporary_root / "candidate-generator-input.json"
    output_path = temporary_root / "candidate-release-handoff.json"
    input_path.write_bytes(_json_bytes(generator_input))
    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(generator),
        "-CandidateInputPath",
        str(input_path),
        "-OutputPath",
        str(output_path),
        "-PlatformRoot",
        str(platform_root),
        "-CoreRoot",
        str(core_root),
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 or not output_path.is_file():
        detail = (completed.stderr or completed.stdout).strip()
        raise RollbackRehearsalError(f"client handoff generation failed: {detail}")
    return output_path


def _run_pointer(script: Path, arguments: Sequence[str]) -> dict[str, Any]:
    command = [
        _powershell_executable(),
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
        *arguments,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RollbackRehearsalError(f"client pointer failed: {detail}")
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise RollbackRehearsalError("client pointer returned no JSON result")


def _client_pointer_round_trip(
    *,
    client_script: Path,
    catalog_path: Path,
    pointer_path: Path,
    stable_path: Path,
    candidate_path: Path,
    stable_id: str,
    candidate_id: str,
    evidence_root: Path,
) -> dict[str, Any]:
    def retained(record: Mapping[str, Any]) -> dict[str, Any]:
        value = copy.deepcopy(dict(record))
        if "pointer_path" in value:
            value["pointer_path"] = "<isolated>/artifacts/releases/release-handoff.json"
        return value

    stable_sha = _sha256_file(stable_path)
    candidate_sha = _sha256_file(candidate_path)
    validation = _run_pointer(
        client_script, ["-CatalogPath", str(catalog_path), "-ValidateOnly"]
    )
    dry_run = _run_pointer(
        client_script,
        [
            "-CatalogPath",
            str(catalog_path),
            "-ExpectedCurrentReleaseId",
            stable_id,
            "-TargetReleaseId",
            candidate_id,
        ],
    )
    if _sha256_file(pointer_path) != stable_sha or dry_run.get("applied") is not False:
        raise RollbackRehearsalError("client pointer dry-run changed the pointer")

    forward_backup = evidence_root / "forward-backup.json"
    forward_receipt = evidence_root / "forward-receipt.json"
    forward = _run_pointer(
        client_script,
        [
            "-CatalogPath",
            str(catalog_path),
            "-ExpectedCurrentReleaseId",
            stable_id,
            "-TargetReleaseId",
            candidate_id,
            "-BackupPath",
            str(forward_backup),
            "-ReceiptPath",
            str(forward_receipt),
            "-Apply",
        ],
    )
    if _sha256_file(pointer_path) != candidate_sha or _sha256_file(
        forward_backup
    ) != stable_sha:
        raise RollbackRehearsalError("client forward switch exact-byte check failed")

    reverse_backup = evidence_root / "reverse-backup.json"
    reverse_receipt = evidence_root / "reverse-receipt.json"
    reverse = _run_pointer(
        client_script,
        [
            "-CatalogPath",
            str(catalog_path),
            "-ExpectedCurrentReleaseId",
            candidate_id,
            "-TargetReleaseId",
            stable_id,
            "-BackupPath",
            str(reverse_backup),
            "-ReceiptPath",
            str(reverse_receipt),
            "-Apply",
        ],
    )
    if _sha256_file(pointer_path) != stable_sha or _sha256_file(
        reverse_backup
    ) != candidate_sha:
        raise RollbackRehearsalError("client rollback exact-byte check failed")
    final_validation = _run_pointer(
        client_script, ["-CatalogPath", str(catalog_path), "-ValidateOnly"]
    )
    retained_forward_receipt = retained(_read_json(forward_receipt))
    retained_rollback_receipt = retained(_read_json(reverse_receipt))
    return {
        "status": "PASS_LOCAL",
        "initial_validation": retained(validation),
        "dry_run": retained(dry_run),
        "forward": retained(forward),
        "rollback": retained(reverse),
        "final_validation": retained(final_validation),
        "restored_stable_sha256": _sha256_file(pointer_path),
        "rollback_byte_identical": _sha256_file(pointer_path) == stable_sha,
        "forward_backup_sha256": _sha256_file(forward_backup),
        "forward_receipt": retained_forward_receipt,
        "forward_receipt_sha256": _sha256_bytes(
            _json_bytes(retained_forward_receipt)
        ),
        "rollback_backup_sha256": _sha256_file(reverse_backup),
        "rollback_receipt": retained_rollback_receipt,
        "rollback_receipt_sha256": _sha256_bytes(
            _json_bytes(retained_rollback_receipt)
        ),
    }


def run_rehearsal(args: argparse.Namespace) -> dict[str, Any]:
    inputs = [
        args.candidate_input,
        args.manifest,
        args.signature,
        args.receipt,
        args.signed_evidence,
        args.stable_handoff,
    ]
    for path in inputs:
        if not path.is_file():
            raise RollbackRehearsalError(f"required input is missing: {path}")
    binding = candidate_gate._validate_retained_candidate(
        manifest_path=args.manifest,
        signature_path=args.signature,
        receipt_path=args.receipt,
        signed_evidence_path=args.signed_evidence,
        release_index_root=args.release_index_root,
        require_physical_phone_install_binding=False,
    )
    signed_manifest = _read_json(args.manifest)
    candidate_input = _read_json(args.candidate_input)
    signed_sources = _source_tuple(signed_manifest)
    for name, root in (
        ("client", args.client_root),
        ("platform", args.platform_root),
        ("core", args.core_root),
    ):
        if not root.is_dir():
            raise RollbackRehearsalError(f"exact {name} checkout is missing: {root}")
        if _git_revision(root) != signed_sources[name]["revision"]:
            raise RollbackRehearsalError(f"exact {name} checkout revision drift")
    client_script = args.client_root / "scripts" / "set-release-stable-pointer.ps1"
    if not client_script.is_file():
        raise RollbackRehearsalError(f"client pointer script is missing: {client_script}")
    generator_input = prepare_generator_input(candidate_input, signed_manifest)
    stable_payload = _read_json(args.stable_handoff)
    stable_identity = _handoff_identity(stable_payload)

    with tempfile.TemporaryDirectory(prefix="pokrov-candidate-rollback-") as raw_root:
        root = Path(raw_root)
        generated_handoff = _generate_candidate_handoff(
            client_root=args.client_root,
            platform_root=args.platform_root,
            core_root=args.core_root,
            generator_input=generator_input,
            temporary_root=root,
        )
        candidate_handoff = _read_json(generated_handoff)
        handoff_binding = bind_candidate_handoff(
            candidate_handoff, signed_manifest, binding
        )
        candidate_identity = _handoff_identity(candidate_handoff)
        if stable_identity[0] == candidate_identity[0]:
            raise RollbackRehearsalError("stable and candidate identities must differ")
        config_root = root / "config"
        artifact_root = root / "artifacts" / "releases"
        evidence_root = root / "evidence"
        stable_relative = Path("pokrov-app") / stable_identity[0] / "release-handoff.json"
        candidate_relative = (
            Path("pokrov-app") / candidate_identity[0] / "release-handoff.json"
        )
        stable_target = artifact_root / stable_relative
        candidate_target = artifact_root / candidate_relative
        pointer_path = artifact_root / "release-handoff.json"
        config_root.mkdir(parents=True)
        evidence_root.mkdir(parents=True)
        stable_target.parent.mkdir(parents=True)
        candidate_target.parent.mkdir(parents=True)
        shutil.copyfile(args.stable_handoff, stable_target)
        shutil.copyfile(stable_target, pointer_path)
        shutil.copyfile(generated_handoff, candidate_target)
        catalog = build_isolated_catalog(
            artifact_root=artifact_root,
            stable_path=stable_target,
            candidate_path=candidate_target,
            stable_identity=stable_identity,
            candidate_identity=candidate_identity,
        )
        catalog_path = config_root / "release-rollback-catalog.json"
        catalog_path.write_bytes(_json_bytes(catalog))

        portal = portal_round_trip(stable_target, candidate_target)
        client = _client_pointer_round_trip(
            client_script=client_script,
            catalog_path=catalog_path,
            pointer_path=pointer_path,
            stable_path=stable_target,
            candidate_path=candidate_target,
            stable_id=stable_identity[0],
            candidate_id=candidate_identity[0],
            evidence_root=evidence_root,
        )
        handoff_bytes = candidate_target.read_bytes()

    handoff_sha = _sha256_bytes(handoff_bytes)
    if portal["candidate_handoff_sha256"] != handoff_sha:
        raise RollbackRehearsalError("portal candidate handoff hash drift")
    result = {
        "schema": "pokrov.release-1.2.0.rollback-rehearsal/v1",
        "generated_at_utc": _utcnow(),
        "status": "PASS_LOCAL_EXACT_CANDIDATE_PORTAL_CLIENT_ROLLBACK",
        "row_outcomes": {"REL_DOD/DOD-18": "I3"},
        "scope": {
            "environment": "isolated local fixture",
            "portal_consumer": "scripts/remote_brain_apply_release_handoff.py",
            "client_pointer": "scripts/set-release-stable-pointer.ps1",
            "sequence": [
                stable_identity[0],
                candidate_identity[0],
                stable_identity[0],
            ],
        },
        "signed_candidate": {
            "candidate_label": binding["candidate_label"],
            "candidate_id": binding["candidate_id"],
            "manifest_sha256": binding["manifest_sha256"],
            "signature_sha256": binding["signature_sha256"],
            "signature_verification": binding["signing"],
            "source_revisions": _source_tuple(signed_manifest),
            "handoff_binding": handoff_binding,
            "candidate_handoff_sha256": handoff_sha,
            "candidate_artifact_set_sha256": candidate_handoff["promotion"][
                "source_artifact_set_sha256"
            ],
        },
        "retained_stable": {
            "release_id": stable_identity[0],
            "release_version": stable_identity[1],
            "handoff_sha256": _sha256_file(args.stable_handoff),
        },
        "portal": portal,
        "client_channel": client,
        "mutation_boundary": {
            "tracked_client_pointer": "UNCHANGED",
            "tracked_client_catalog": "UNCHANGED",
            "portal_runtime": "NOT_MUTATED",
            "production_deploy": "NOT_AUTHORIZED",
            "public_release": "NOT_AUTHORIZED",
            "stable_promotion": "NOT_AUTHORIZED",
            "physical_device": "NOT_RUN",
            "android_emulator": "NOT_REQUIRED_FOR_ROLLBACK_REHEARSAL",
        },
        "evidence_ceiling": (
            "I3 verified-local exact-candidate rehearsal; I4/I5 still require an "
            "authorized runtime pointer rollback plus current/brain-origin readback"
        ),
    }
    if args.handoff_output is not None:
        _write_new_bytes(args.handoff_output, handoff_bytes)
    if args.output is not None:
        _write_new(args.output, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run an isolated exact-candidate portal/client rollback rehearsal."
    )
    parser.add_argument("--candidate-input", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--signature", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--signed-evidence", type=Path, required=True)
    parser.add_argument("--stable-handoff", type=Path, required=True)
    parser.add_argument("--client-root", type=Path, required=True)
    parser.add_argument("--platform-root", type=Path, required=True)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--release-index-root", type=Path, required=True)
    parser.add_argument("--handoff-output", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        result = run_rehearsal(build_parser().parse_args(argv))
    except (RollbackRehearsalError, candidate_gate.Pb14GateError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
