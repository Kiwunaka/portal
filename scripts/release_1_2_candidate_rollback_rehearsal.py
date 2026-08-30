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
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
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


class RollbackRehearsalError(RuntimeError):
    """Raised when an exact-candidate rollback invariant fails."""


candidate_gate: Any = None
portal_handoff: Any = None
handoff_validator: Any = None
ExactGitSnapshotError: Any = None
GIT_REVISION_RE: Any = None
assert_sparse_repository_clean: Any = None
canonical_requested_paths: Any = None
confirm_repository_revision: Any = None
git_command: Any = None
git_environment: Any = None
materialize_sparse_repository: Any = None
read_blob: Any = None


class _VerifiedRepoSourceLoader(importlib.abc.Loader):
    def __init__(self, path: Path, object_id: str, git_executable: Path) -> None:
        self.path = path
        self.object_id = object_id
        self.git_executable = git_executable

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> None:
        return None

    def exec_module(self, module: Any) -> None:
        try:
            observed = self.path.read_bytes()
        except OSError as exc:
            raise ImportError("rollback harness source is unavailable") from exc
        committed = _bootstrap_exact_blob(self.git_executable, self.object_id)
        if not _python_source_bytes_match(observed, committed):
            raise ImportError("rollback harness source differs from HEAD")
        code = compile(committed, str(self.path), "exec", dont_inherit=True)
        exec(code, module.__dict__)


class _VerifiedRepoSourceFinder(importlib.abc.MetaPathFinder):
    def __init__(
        self,
        expected_sources: Mapping[str, str],
        git_executable: Path,
    ) -> None:
        self.expected_sources = dict(expected_sources)
        self.git_executable = git_executable

    def find_spec(
        self,
        fullname: str,
        path: Sequence[str] | None,
        target: Any = None,
    ) -> importlib.machinery.ModuleSpec | None:
        del target
        discovered = importlib.machinery.PathFinder.find_spec(fullname, path)
        if discovered is None or discovered.origin is None:
            return discovered
        try:
            source = Path(discovered.origin).resolve(strict=True)
            relative = source.relative_to(REPO_ROOT).as_posix()
        except (OSError, ValueError):
            return discovered
        if source.suffix.casefold() != ".py":
            raise ImportError("rollback harness local module is not source-backed")
        object_id = self.expected_sources.get(relative)
        if object_id is None:
            raise ImportError("rollback harness local source is not committed")
        package_paths = discovered.submodule_search_locations
        return importlib.util.spec_from_file_location(
            fullname,
            source,
            loader=_VerifiedRepoSourceLoader(
                source,
                object_id,
                self.git_executable,
            ),
            submodule_search_locations=(
                list(package_paths) if package_paths is not None else None
            ),
        )


_CLIENT_SNAPSHOT_PATHS = (
    "scripts/new-release-handoff-v2.ps1",
    "scripts/set-release-stable-pointer.ps1",
    "scripts/validate-observability-contracts.ps1",
    "scripts/check-client-version-parity.ps1",
    "config/runtime-artifacts.seed.json",
    "config/observability-contracts.seed.json",
    "config/release-handoff.seed.json",
    "config/windows-release.seed.json",
    "packages/observability_contracts/lib/observability_contracts.dart",
    "apps/android_shell/pubspec.yaml",
    "apps/windows_shell/pubspec.yaml",
    "packages/app_shell/pubspec.yaml",
)
_PLATFORM_SNAPSHOT_PATHS = (
    "scripts/validate_observability_contracts.py",
    "scripts/validate_release_handoff_metadata.py",
    "shared/contracts/observability/error-catalog.json",
    "shared/contracts/observability/error-catalog.schema.json",
    "shared/contracts/observability/observability-event.schema.json",
)
_CORE_SNAPSHOT_PATHS = (
    "config/release.json",
    "config/observability-contracts.json",
    "scripts/verify-observability-contracts.ps1",
    "v2/hcore/grpc_server.go",
    "platform/desktop/custom.go",
)
_HARNESS_PATHS = (
    "scripts/release_1_2_candidate_rollback_rehearsal.py",
    "scripts/release_1_2_pb14_candidate_gate.py",
    "scripts/remote_brain_apply_release_handoff.py",
    "scripts/validate_release_handoff_metadata.py",
    "scripts/exact_git_snapshot.py",
)


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
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"),
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
        if not repository or GIT_REVISION_RE.fullmatch(revision) is None:
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


def _powershell_executable() -> Path:
    raw_executable = shutil.which("pwsh") or shutil.which("powershell")
    if raw_executable is None:
        raise RollbackRehearsalError("PowerShell is required for the client pointer")
    try:
        executable = Path(raw_executable).resolve(strict=True)
    except OSError as exc:
        raise RollbackRehearsalError(
            "PowerShell is required for the client pointer"
        ) from exc
    if not executable.is_file():
        raise RollbackRehearsalError("PowerShell is required for the client pointer")
    return executable


def _git_executable() -> Path:
    raw_executable = shutil.which("git.exe") or shutil.which("git")
    if raw_executable is None:
        raise RollbackRehearsalError("Git is required for exact source snapshots")
    try:
        executable = Path(raw_executable).resolve(strict=True)
    except OSError as exc:
        raise RollbackRehearsalError(
            "Git is required for exact source snapshots"
        ) from exc
    if not executable.is_file():
        raise RollbackRehearsalError("Git is required for exact source snapshots")
    return executable


def _bootstrap_git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    return environment


def _bootstrap_git_command(git_executable: Path, *arguments: str) -> list[str]:
    return [
        str(git_executable),
        "-c",
        "core.fsmonitor=false",
        "-c",
        f"core.hooksPath={os.devnull}",
        *arguments,
    ]


def _bootstrap_git(
    git_executable: Path,
    *arguments: str,
    timeout: int = 120,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            _bootstrap_git_command(git_executable, *arguments),
            cwd=REPO_ROOT,
            env=_bootstrap_git_environment(),
            check=False,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RollbackRehearsalError(
            "rollback harness bootstrap failed"
        ) from exc


def _bootstrap_exact_blob(git_executable: Path, object_id: str) -> bytes:
    completed = _bootstrap_git(
        git_executable,
        "cat-file",
        "blob",
        object_id,
    )
    digest = hashlib.sha1(usedforsecurity=False)
    digest.update(f"blob {len(completed.stdout)}\0".encode("ascii"))
    digest.update(completed.stdout)
    if completed.returncode != 0 or digest.hexdigest() != object_id:
        raise RollbackRehearsalError(
            "rollback harness source object integrity check failed"
        )
    return completed.stdout


def _python_source_bytes_match(observed: bytes, committed: bytes) -> bool:
    if observed == committed:
        return True
    normalized_observed = observed.replace(b"\r\n", b"\n")
    normalized_committed = committed.replace(b"\r\n", b"\n")
    return (
        b"\r" not in normalized_observed
        and b"\r" not in normalized_committed
        and normalized_observed == normalized_committed
    )


def _bootstrap_verified_imports(git_executable: Path) -> None:
    current_source = Path(__file__).resolve(strict=True)
    for module in tuple(sys.modules.values()):
        raw_origin = getattr(module, "__file__", None)
        if not raw_origin:
            continue
        try:
            origin = Path(raw_origin).resolve(strict=True)
            origin.relative_to(REPO_ROOT)
        except (OSError, ValueError):
            continue
        if origin != current_source:
            raise RollbackRehearsalError(
                "rollback harness local module loaded before source verification"
            )

    top_level = _bootstrap_git(git_executable, "rev-parse", "--show-toplevel")
    head = _bootstrap_git(git_executable, "rev-parse", "HEAD")
    try:
        actual_root = Path(top_level.stdout.decode("utf-8").strip()).resolve(
            strict=True
        )
        revision = head.stdout.decode("ascii").strip().lower()
    except (OSError, UnicodeError) as exc:
        raise RollbackRehearsalError(
            "rollback harness revision is unavailable"
        ) from exc
    if (
        top_level.returncode != 0
        or head.returncode != 0
        or actual_root != REPO_ROOT
        or len(revision) != 40
        or any(character not in "0123456789abcdef" for character in revision)
    ):
        raise RollbackRehearsalError("rollback harness revision is unavailable")

    checked = _bootstrap_git(
        git_executable,
        "fsck",
        "--strict",
        "--no-reflogs",
        "--no-dangling",
        revision,
        timeout=300,
    )
    if checked.returncode != 0:
        raise RollbackRehearsalError(
            "rollback harness Git object integrity check failed"
        )
    inventory = _bootstrap_git(
        git_executable,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        revision,
    )
    if inventory.returncode != 0 or len(inventory.stdout) > 64 * 1024 * 1024:
        raise RollbackRehearsalError(
            "rollback harness source inventory is unavailable"
        )
    expected_sources: dict[str, str] = {}
    for raw_entry in inventory.stdout.split(b"\0"):
        if not raw_entry:
            continue
        header, separator, raw_path = raw_entry.partition(b"\t")
        fields = header.split()
        if not separator or len(fields) != 3:
            raise RollbackRehearsalError(
                "rollback harness source inventory is invalid"
            )
        try:
            mode = fields[0].decode("ascii")
            object_type = fields[1].decode("ascii")
            object_id = fields[2].decode("ascii").lower()
            relative = raw_path.decode("utf-8")
        except UnicodeError as exc:
            raise RollbackRehearsalError(
                "rollback harness source inventory is invalid"
            ) from exc
        if not relative.endswith(".py"):
            continue
        if (
            mode not in {"100644", "100755"}
            or object_type != "blob"
            or len(object_id) != 40
            or any(character not in "0123456789abcdef" for character in object_id)
            or relative in expected_sources
        ):
            raise RollbackRehearsalError(
                "rollback harness source inventory is invalid"
            )
        expected_sources[relative] = object_id

    current_relative = current_source.relative_to(REPO_ROOT).as_posix()
    required_sources = (*_HARNESS_PATHS, current_relative)
    for relative in required_sources:
        object_id = expected_sources.get(relative)
        source = REPO_ROOT.joinpath(*relative.split("/"))
        if object_id is None:
            raise RollbackRehearsalError(
                f"rollback harness source is unavailable: {relative}"
            )
        try:
            observed = source.read_bytes()
        except OSError as exc:
            raise RollbackRehearsalError(
                f"rollback harness source is unavailable: {relative}"
            ) from exc
        committed = _bootstrap_exact_blob(git_executable, object_id)
        if not _python_source_bytes_match(observed, committed):
            raise RollbackRehearsalError(
                f"rollback harness source differs from HEAD: {relative}"
            )

    finder = _VerifiedRepoSourceFinder(expected_sources, git_executable)
    sys.meta_path.insert(0, finder)
    try:
        exact_snapshot = importlib.import_module("exact_git_snapshot")
        loaded_candidate_gate = importlib.import_module(
            "release_1_2_pb14_candidate_gate"
        )
        loaded_portal_handoff = importlib.import_module(
            "remote_brain_apply_release_handoff"
        )
        loaded_handoff_validator = importlib.import_module(
            "validate_release_handoff_metadata"
        )
    except (ImportError, OSError, SyntaxError) as exc:
        raise RollbackRehearsalError(
            "rollback harness verified source import failed"
        ) from exc
    globals().update(
        {
            "candidate_gate": loaded_candidate_gate,
            "portal_handoff": loaded_portal_handoff,
            "handoff_validator": loaded_handoff_validator,
            "ExactGitSnapshotError": exact_snapshot.ExactGitSnapshotError,
            "GIT_REVISION_RE": exact_snapshot.GIT_REVISION_RE,
            "assert_sparse_repository_clean": exact_snapshot.assert_sparse_repository_clean,
            "canonical_requested_paths": exact_snapshot.canonical_requested_paths,
            "confirm_repository_revision": exact_snapshot.confirm_repository_revision,
            "git_command": exact_snapshot.git_command,
            "git_environment": exact_snapshot.git_environment,
            "materialize_sparse_repository": exact_snapshot.materialize_sparse_repository,
            "read_blob": exact_snapshot.read_blob,
            "_verified_source_finder": finder,
        }
    )


def _read_exact_json_blob(
    *,
    git_executable: Path,
    repository: Path,
    revision: str,
    path: str,
) -> dict[str, Any]:
    try:
        raw = read_blob(
            git_executable,
            repository,
            revision,
            path,
        )
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (ExactGitSnapshotError, UnicodeError, json.JSONDecodeError) as exc:
        raise RollbackRehearsalError(
            f"exact source JSON is invalid: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise RollbackRehearsalError(f"exact source JSON is invalid: {path}")
    return value


def _runtime_asset_paths(runtime_artifacts: Mapping[str, Any]) -> tuple[str, ...]:
    core = runtime_artifacts.get("core")
    assets = core.get("assets") if isinstance(core, Mapping) else None
    if not isinstance(assets, Mapping):
        raise RollbackRehearsalError("exact client runtime assets are invalid")
    paths: list[str] = []
    for platform in ("android", "windows"):
        asset = assets.get(platform)
        if not isinstance(asset, Mapping):
            raise RollbackRehearsalError("exact client runtime assets are invalid")
        destination = str(asset.get("sync_destination") or "")
        entry = str(asset.get("entry") or "")
        paths.append(f"{destination}/{entry}")
    try:
        return canonical_requested_paths(paths)
    except ExactGitSnapshotError as exc:
        raise RollbackRehearsalError("exact client runtime assets are invalid") from exc


def _core_abi_path(core_release: Mapping[str, Any]) -> str:
    raw_path = str(core_release.get("abi_contract") or "")
    try:
        return canonical_requested_paths((raw_path,))[0]
    except ExactGitSnapshotError as exc:
        raise RollbackRehearsalError("exact Core ABI contract is invalid") from exc


def _materialize_release_source_snapshots(
    *,
    git_executable: Path,
    client_root: Path,
    platform_root: Path,
    core_root: Path,
    source_revisions: Mapping[str, Mapping[str, str]],
    destination: Path,
) -> tuple[
    dict[str, Path],
    dict[str, tuple[str, ...]],
    dict[str, tuple[str, ...]],
]:
    client_revision = source_revisions["client"]["revision"]
    platform_revision = source_revisions["platform"]["revision"]
    core_revision = source_revisions["core"]["revision"]
    runtime_artifacts = _read_exact_json_blob(
        git_executable=git_executable,
        repository=client_root,
        revision=client_revision,
        path="config/runtime-artifacts.seed.json",
    )
    core_release = _read_exact_json_blob(
        git_executable=git_executable,
        repository=core_root,
        revision=core_revision,
        path="config/release.json",
    )
    client_lfs_paths = _runtime_asset_paths(runtime_artifacts)
    client_paths = canonical_requested_paths(
        (*_CLIENT_SNAPSHOT_PATHS, *client_lfs_paths)
    )
    platform_paths = canonical_requested_paths(_PLATFORM_SNAPSHOT_PATHS)
    core_paths = canonical_requested_paths(
        (*_CORE_SNAPSHOT_PATHS, _core_abi_path(core_release))
    )
    snapshots = {
        "client": destination / "client",
        "platform": destination / "platform",
        "core": destination / "core",
    }
    snapshot_paths = {
        "client": client_paths,
        "platform": platform_paths,
        "core": core_paths,
    }
    snapshot_lfs_paths = {
        "client": client_lfs_paths,
        "platform": (),
        "core": (),
    }
    try:
        materialize_sparse_repository(
            git_executable,
            client_root,
            client_revision,
            snapshots["client"],
            client_paths,
            client_lfs_paths,
        )
        materialize_sparse_repository(
            git_executable,
            platform_root,
            platform_revision,
            snapshots["platform"],
            platform_paths,
        )
        materialize_sparse_repository(
            git_executable,
            core_root,
            core_revision,
            snapshots["core"],
            core_paths,
        )
    except ExactGitSnapshotError as exc:
        raise RollbackRehearsalError(
            "exact release source snapshot could not be created"
        ) from exc
    return snapshots, snapshot_paths, snapshot_lfs_paths


def _snapshot_process_environment(
    git_executable: Path,
    powershell_executable: Path,
) -> dict[str, str]:
    environment = git_environment()
    for key in tuple(environment):
        if key in {"PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"}:
            environment.pop(key, None)
    executable_directories = {
        str(git_executable.parent),
        str(powershell_executable.parent),
        str(Path(sys.executable).resolve().parent),
    }
    environment.update(
        {
            "PATH": os.pathsep.join(sorted(executable_directories)),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
        }
    )
    return environment


def _harness_identity(
    git_executable: Path,
    powershell_executable: Path,
) -> dict[str, Any]:
    completed = subprocess.run(
        git_command(git_executable, "rev-parse", "HEAD"),
        cwd=REPO_ROOT,
        env=git_environment(),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    revision = completed.stdout.strip().lower()
    if (
        completed.returncode != 0
        or GIT_REVISION_RE.fullmatch(revision) is None
    ):
        raise RollbackRehearsalError("rollback harness revision is unavailable")
    try:
        confirm_repository_revision(git_executable, REPO_ROOT, revision)
    except ExactGitSnapshotError as exc:
        raise RollbackRehearsalError("rollback harness revision is unavailable") from exc

    file_hashes: dict[str, str] = {}
    for path in _HARNESS_PATHS:
        try:
            committed = read_blob(
                git_executable,
                REPO_ROOT,
                revision,
                path,
            )
        except ExactGitSnapshotError as exc:
            raise RollbackRehearsalError(
                f"rollback harness source is unavailable: {path}"
            ) from exc
        local_path = REPO_ROOT.joinpath(*path.split("/"))
        try:
            observed = local_path.read_bytes()
        except OSError as exc:
            raise RollbackRehearsalError(
                f"rollback harness source is unavailable: {path}"
            ) from exc
        if not _python_source_bytes_match(observed, committed):
            raise RollbackRehearsalError(
                f"rollback harness source differs from HEAD: {path}"
            )
        file_hashes[path] = _sha256_bytes(committed)
    return {
        "revision": revision,
        "files": file_hashes,
        "git_executable_sha256": _sha256_file(git_executable),
        "powershell_executable_sha256": _sha256_file(powershell_executable),
        "python_executable_sha256": _sha256_file(Path(sys.executable).resolve()),
    }


def _generate_candidate_handoff(
    *,
    powershell_executable: Path,
    client_root: Path,
    platform_root: Path,
    core_root: Path,
    generator_input: Mapping[str, Any],
    temporary_root: Path,
    process_environment: Mapping[str, str],
) -> Path:
    generator = client_root / "scripts" / "new-release-handoff-v2.ps1"
    if not generator.is_file():
        raise RollbackRehearsalError(f"client handoff generator is missing: {generator}")
    input_path = temporary_root / "candidate-generator-input.json"
    output_path = temporary_root / "candidate-release-handoff.json"
    input_path.write_bytes(_json_bytes(generator_input))
    command = [
        str(powershell_executable),
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
        env=dict(process_environment),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 or not output_path.is_file():
        detail = (completed.stderr or completed.stdout).strip()
        raise RollbackRehearsalError(f"client handoff generation failed: {detail}")
    return output_path


def _run_pointer(
    script: Path,
    arguments: Sequence[str],
    *,
    powershell_executable: Path,
    process_environment: Mapping[str, str],
) -> dict[str, Any]:
    command = [
        str(powershell_executable),
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
        env=dict(process_environment),
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
    powershell_executable: Path,
    process_environment: Mapping[str, str],
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
        client_script,
        ["-CatalogPath", str(catalog_path), "-ValidateOnly"],
        powershell_executable=powershell_executable,
        process_environment=process_environment,
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
        powershell_executable=powershell_executable,
        process_environment=process_environment,
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
        powershell_executable=powershell_executable,
        process_environment=process_environment,
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
        powershell_executable=powershell_executable,
        process_environment=process_environment,
    )
    if _sha256_file(pointer_path) != stable_sha or _sha256_file(
        reverse_backup
    ) != candidate_sha:
        raise RollbackRehearsalError("client rollback exact-byte check failed")
    final_validation = _run_pointer(
        client_script,
        ["-CatalogPath", str(catalog_path), "-ValidateOnly"],
        powershell_executable=powershell_executable,
        process_environment=process_environment,
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
    git_executable = _git_executable()
    _bootstrap_verified_imports(git_executable)
    powershell_executable = _powershell_executable()
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
    harness_identity = _harness_identity(git_executable, powershell_executable)
    process_environment = _snapshot_process_environment(
        git_executable,
        powershell_executable,
    )
    binding = candidate_gate._validate_retained_candidate(
        manifest_path=args.manifest,
        signature_path=args.signature,
        receipt_path=args.receipt,
        signed_evidence_path=args.signed_evidence,
        release_index_root=args.release_index_root,
        require_physical_phone_install_binding=False,
    )
    try:
        manifest_bytes = args.manifest.read_bytes()
        candidate_input_bytes = args.candidate_input.read_bytes()
        stable_handoff_bytes = args.stable_handoff.read_bytes()
        signed_manifest = json.loads(
            manifest_bytes.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
        candidate_input = json.loads(
            candidate_input_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
        stable_payload = json.loads(
            stable_handoff_bytes.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RollbackRehearsalError("candidate rehearsal input changed") from exc
    if not all(
        isinstance(value, dict)
        for value in (signed_manifest, candidate_input, stable_payload)
    ) or _sha256_bytes(manifest_bytes) != binding["manifest_sha256"]:
        raise RollbackRehearsalError("candidate rehearsal input changed")
    signed_sources = _source_tuple(signed_manifest)
    generator_input = prepare_generator_input(candidate_input, signed_manifest)
    stable_identity = _handoff_identity(stable_payload)

    temporary_parent = args.temporary_root
    if temporary_parent is not None:
        try:
            temporary_parent = temporary_parent.resolve(strict=True)
        except OSError as exc:
            raise RollbackRehearsalError(
                "rollback temporary root is unavailable"
            ) from exc
        if not temporary_parent.is_dir():
            raise RollbackRehearsalError("rollback temporary root is unavailable")
    with tempfile.TemporaryDirectory(
        prefix="pokrov-candidate-rollback-",
        dir=temporary_parent,
    ) as raw_root:
        root = Path(raw_root)
        snapshots, snapshot_paths, snapshot_lfs_paths = (
            _materialize_release_source_snapshots(
                git_executable=git_executable,
                client_root=args.client_root,
                platform_root=args.platform_root,
                core_root=args.core_root,
                source_revisions=signed_sources,
                destination=root / "source-snapshots",
            )
        )
        client_script = (
            snapshots["client"] / "scripts" / "set-release-stable-pointer.ps1"
        )
        generated_handoff = _generate_candidate_handoff(
            powershell_executable=powershell_executable,
            client_root=snapshots["client"],
            platform_root=snapshots["platform"],
            core_root=snapshots["core"],
            generator_input=generator_input,
            temporary_root=root,
            process_environment=process_environment,
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
        stable_target.write_bytes(stable_handoff_bytes)
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
            powershell_executable=powershell_executable,
            process_environment=process_environment,
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
        for name, snapshot in snapshots.items():
            try:
                assert_sparse_repository_clean(
                    git_executable,
                    snapshot,
                    signed_sources[name]["revision"],
                    snapshot_paths[name],
                    snapshot_lfs_paths[name],
                )
            except ExactGitSnapshotError as exc:
                raise RollbackRehearsalError(
                    f"exact {name} source snapshot changed during rehearsal"
                ) from exc

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
        "harness": harness_identity,
        "retained_stable": {
            "release_id": stable_identity[0],
            "release_version": stable_identity[1],
            "handoff_sha256": _sha256_bytes(stable_handoff_bytes),
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
    parser.add_argument(
        "--temporary-root",
        type=Path,
        help="Existing private parent for disposable exact-source snapshots.",
    )
    parser.add_argument("--handoff-output", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        result = run_rehearsal(build_parser().parse_args(argv))
    except RollbackRehearsalError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        gate_module = globals().get("candidate_gate")
        if gate_module is None or not isinstance(exc, gate_module.Pb14GateError):
            raise
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
