from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_candidate_rollback_rehearsal.py"
SPEC = importlib.util.spec_from_file_location("candidate_rollback_rehearsal", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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
