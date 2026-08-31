from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_candidate_rollback_rehearsal.py"
SPEC = importlib.util.spec_from_file_location("candidate_rollback_rehearsal", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
EXACT_SNAPSHOT = importlib.import_module("exact_git_snapshot")
MODULE.candidate_gate = importlib.import_module("release_1_2_pb14_candidate_gate")
MODULE.portal_handoff = importlib.import_module("remote_brain_apply_release_handoff")
MODULE.handoff_validator = importlib.import_module(
    "validate_release_handoff_metadata"
)
for _name in (
    "ExactGitSnapshotError",
    "GIT_REVISION_RE",
    "assert_sparse_repository_clean",
    "canonical_requested_paths",
    "confirm_repository_revision",
    "git_command",
    "git_environment",
    "materialize_sparse_repository",
    "read_blob",
):
    setattr(MODULE, _name, getattr(EXACT_SNAPSHOT, _name))


def _git() -> Path:
    raw = shutil.which("git.exe") or shutil.which("git")
    assert raw is not None
    return Path(raw).resolve()


def test_cli_does_not_import_sibling_module_before_source_bootstrap(
    tmp_path: Path,
) -> None:
    script = tmp_path / MODULE_PATH.name
    script.write_bytes(MODULE_PATH.read_bytes())
    marker = tmp_path / "sibling-module-loaded.txt"
    (tmp_path / "argparse.py").write_text(
        "with open(" + repr(str(marker)) + ", 'w', encoding='utf-8') as handle:\n"
        "    handle.write('loaded')\n"
        "raise RuntimeError('sibling module must not load')\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert not marker.exists()


def test_verified_source_loader_compiles_only_hash_bound_source(tmp_path: Path) -> None:
    git = _git()
    relative = "scripts/validate_release_handoff_metadata.py"
    object_id = subprocess.run(
        [str(git), "-C", str(REPO_ROOT), "rev-parse", f"HEAD:{relative}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    committed = subprocess.run(
        [str(git), "-C", str(REPO_ROOT), "cat-file", "blob", object_id],
        check=True,
        capture_output=True,
    ).stdout
    source = tmp_path / "verified_module.py"
    source.write_bytes(committed.replace(b"\n", b"\r\n"))
    loader = MODULE._VerifiedRepoSourceLoader(source, object_id, git)
    spec = importlib.util.spec_from_file_location("verified_module", source, loader=loader)
    assert spec is not None
    loaded = importlib.util.module_from_spec(spec)
    MODULE.sys.modules[spec.name] = loaded
    try:
        loader.exec_module(loaded)
        assert loaded.EXIT_INVALID == 2

        source.write_bytes(committed + b"\nCHANGED = True\n")
        with pytest.raises(ImportError, match="differs from HEAD"):
            loader.exec_module(loaded)
    finally:
        MODULE.sys.modules.pop(spec.name, None)


def _commit_tree(root: Path, files: dict[str, bytes]) -> str:
    git = _git()
    for relative, value in files.items():
        path = root.joinpath(*relative.split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    subprocess.run(
        [str(git), "init", "-q", str(root)], check=True, capture_output=True
    )
    subprocess.run(
        [str(git), "-C", str(root), "add", "."], check=True, capture_output=True
    )
    subprocess.run(
        [
            str(git),
            "-C",
            str(root),
            "-c",
            "user.name=POKROV Test",
            "-c",
            "user.email=test@pokrov.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
        capture_output=True,
    )
    return subprocess.run(
        [str(git), "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _lfs_pointer(value: bytes) -> tuple[bytes, str]:
    object_id = MODULE.hashlib.sha256(value).hexdigest()
    pointer = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{object_id}\n"
        f"size {len(value)}\n"
    ).encode("ascii")
    return pointer, object_id


def _install_lfs_object(root: Path, object_id: str, value: bytes) -> None:
    path = root / ".git" / "lfs" / "objects" / object_id[:2] / object_id[2:4] / object_id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def _candidate_inputs() -> tuple[dict, dict, dict]:
    handoff = json.loads(
        (REPO_ROOT / "tests/fixtures/release-handoff/valid-v2.json").read_text(
            encoding="utf-8"
        )
    )
    manifest = {
        "candidate_id": "pokrov-1.2.0-candidate.3",
        "product": {"version": "1.2.0-rc.1"},
        "compatibility": {"core_version": "1.1.0"},
        "sources": {
            name: {
                "repository": value["repository"],
                "commit": value["revision"],
            }
            for name, value in handoff["sources"].items()
        },
        "artifacts": [
            {
                "name": artifact["file_name"],
                "platform": artifact["platform"],
                "kind": artifact["kind"],
                "sha256": artifact["sha256"],
                "size": artifact["size_bytes"],
            }
            for artifact in handoff["artifacts"]
        ],
    }
    binding = {"candidate_label": "pokrov-1.2.0-candidate.3"}
    return handoff, manifest, binding


def test_bind_candidate_handoff_binds_signed_identity() -> None:
    handoff, manifest, binding = _candidate_inputs()

    result = MODULE.bind_candidate_handoff(handoff, manifest, binding)

    assert result["schema_version"] == 2
    assert result["release_id"] == "pokrov-1.2.0-rc.1"
    assert result["artifact_count"] == 2


def test_bind_candidate_handoff_rejects_signed_artifact_drift() -> None:
    handoff, manifest, binding = _candidate_inputs()
    manifest["artifacts"][0]["sha256"] = "0" * 64

    with pytest.raises(MODULE.RollbackRehearsalError, match="signed artifact drift"):
        MODULE.bind_candidate_handoff(handoff, manifest, binding)


def test_prepare_generator_input_updates_only_signed_index_revision() -> None:
    handoff, manifest, _binding = _candidate_inputs()
    candidate_input = {
        "sources": {
            "platform": copy.deepcopy(handoff["sources"]["platform"]),
            "core": copy.deepcopy(handoff["sources"]["core"]),
            "release_index": {
                "repository": "Kiwunaka/pokrov",
                "revision": "0" * 40,
            },
        }
    }

    result = MODULE.prepare_generator_input(candidate_input, manifest)

    assert result["sources"]["release_index"]["revision"] == "d" * 40
    assert candidate_input["sources"]["release_index"]["revision"] == "0" * 40


def test_portal_round_trip_restores_exact_env_bytes(tmp_path: Path) -> None:
    stable = tmp_path / "stable.json"
    candidate = REPO_ROOT / "tests/fixtures/release-handoff/valid-v2.json"
    stable.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "release_id": "stable-a",
                "release_version": "1.1.6",
                "runtime_env": {
                    "APP_ANDROID_APK_URL": "https://downloads.example/stable.apk",
                    "APP_ANDROID_RELEASE_NOTES": "Stable",
                    "APP_ANDROID_RELEASE_NOTES_URL": "https://downloads.example/stable",
                    "APP_ANDROID_PUBLISHED_AT": "2026-08-20T00:00:00Z",
                    "APP_WINDOWS_EXE_URL": "https://downloads.example/stable.exe",
                    "APP_WINDOWS_RELEASE_NOTES": "Stable",
                    "APP_WINDOWS_RELEASE_NOTES_URL": "https://downloads.example/stable",
                    "APP_WINDOWS_PUBLISHED_AT": "2026-08-20T00:00:00Z",
                    "APP_DOCS_URL": "https://pokrov.space/install/",
                },
            }
        ),
        encoding="utf-8",
    )

    result = MODULE.portal_round_trip(stable, candidate)

    assert result["status"] == "PASS_LOCAL"
    assert result["rollback_byte_identical"] is True
    assert result["before_sha256"] == result["rollback_sha256"]
    assert result["candidate_label"] == "pokrov-1.2.0-rc.1"


def test_isolated_catalog_hash_binds_both_targets(tmp_path: Path) -> None:
    stable = tmp_path / "stable.json"
    candidate = tmp_path / "candidate.json"
    stable.write_bytes(b'{"schema_version":1}\n')
    candidate.write_bytes(b'{"schema_version":2}\n')

    result = MODULE.build_isolated_catalog(
        artifact_root=tmp_path,
        stable_path=stable,
        candidate_path=candidate,
        stable_identity=("stable-a", "1.1.6", 1),
        candidate_identity=("candidate-b", "1.2.0", 2),
    )

    # The function receives catalog-relative paths in production, so patch the
    # digest sources for this narrow construction test.
    assert [item["release_id"] for item in result["rollback_targets"]] == [
        "stable-a",
        "candidate-b",
    ]
    assert result["mutation_policy"]["exact_candidate_gate_required"] is True


def test_release_source_snapshots_use_commit_objects_not_mutable_worktrees(
    tmp_path: Path,
) -> None:
    client_root = tmp_path / "client"
    platform_root = tmp_path / "platform"
    core_root = tmp_path / "core"
    client_root.mkdir()
    platform_root.mkdir()
    core_root.mkdir()
    runtime_artifacts = {
        "core": {
            "assets": {
                "android": {
                    "sync_destination": "runtime/android",
                    "entry": "core.aar",
                },
                "windows": {
                    "sync_destination": "runtime/windows",
                    "entry": "core.dll",
                },
            }
        }
    }
    client_files = {path: b"fixture\n" for path in MODULE._CLIENT_SNAPSHOT_PATHS}
    client_files["config/runtime-artifacts.seed.json"] = json.dumps(
        runtime_artifacts
    ).encode()
    android_value = b"exact-android"
    windows_value = b"exact-windows"
    android_pointer, android_object_id = _lfs_pointer(android_value)
    windows_pointer, windows_object_id = _lfs_pointer(windows_value)
    client_files["runtime/android/core.aar"] = android_pointer
    client_files["runtime/windows/core.dll"] = windows_pointer
    client_files["not-selected.txt"] = b"must stay absent"
    core_files = {path: b"fixture\n" for path in MODULE._CORE_SNAPSHOT_PATHS}
    core_files["config/release.json"] = json.dumps(
        {"abi_contract": "config/abi.json"}
    ).encode()
    core_files["config/abi.json"] = b"{}\n"
    platform_files = {
        path: b"fixture\n" for path in MODULE._PLATFORM_SNAPSHOT_PATHS
    }
    client_revision = _commit_tree(client_root, client_files)
    _install_lfs_object(client_root, android_object_id, android_value)
    _install_lfs_object(client_root, windows_object_id, windows_value)
    platform_revision = _commit_tree(platform_root, platform_files)
    core_revision = _commit_tree(core_root, core_files)
    generator = client_root / "scripts/new-release-handoff-v2.ps1"
    generator.write_bytes(b"mutable worktree bytes\n")

    snapshots, snapshot_paths, snapshot_lfs_paths = (
        MODULE._materialize_release_source_snapshots(
            git_executable=_git(),
            client_root=client_root,
            platform_root=platform_root,
            core_root=core_root,
            source_revisions={
                "client": {"revision": client_revision},
                "platform": {"revision": platform_revision},
                "core": {"revision": core_revision},
            },
            destination=tmp_path / "snapshots",
        )
    )

    assert (
        snapshots["client"] / "scripts/new-release-handoff-v2.ps1"
    ).read_bytes() == b"fixture\n"
    assert not (snapshots["client"] / "not-selected.txt").exists()
    assert (snapshots["client"] / "runtime/android/core.aar").read_bytes() == (
        b"exact-android"
    )
    for name, revision in (
        ("client", client_revision),
        ("platform", platform_revision),
        ("core", core_revision),
    ):
        MODULE.assert_sparse_repository_clean(
            _git(),
            snapshots[name],
            revision,
            snapshot_paths[name],
            snapshot_lfs_paths[name],
        )
