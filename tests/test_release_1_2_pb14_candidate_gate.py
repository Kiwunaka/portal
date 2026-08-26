from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "release_1_2_pb14_candidate_gate.py"
SPEC = importlib.util.spec_from_file_location(
    "release_1_2_pb14_candidate_gate", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_detached_signature_verification_uses_exact_active_key() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    payload = b'{"candidate":"exact"}\n'
    keyring = {
        "schema": "pokrov.release-index.keyring/v1",
        "keys": [
            {
                "id": "test-release-key",
                "state": "active",
                "algorithm": "ed25519",
                "public_key_base64": MODULE.base64.b64encode(public_key).decode(
                    "ascii"
                ),
                "public_key_sha256": MODULE._sha256_bytes(public_key),
            }
        ],
    }

    result = MODULE._verify_detached_signature(
        manifest_bytes=payload,
        signature_bytes=private_key.sign(payload),
        keyring=keyring,
        key_id="test-release-key",
    )

    assert result == {
        "status": "PASS",
        "algorithm": "ed25519",
        "key_id": "test-release-key",
        "public_key_sha256": MODULE._sha256_bytes(public_key),
    }


def test_detached_signature_rejects_manifest_drift() -> None:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    keyring = {
        "schema": "pokrov.release-index.keyring/v1",
        "keys": [
            {
                "id": "test-release-key",
                "state": "active",
                "algorithm": "ed25519",
                "public_key_base64": MODULE.base64.b64encode(public_key).decode(
                    "ascii"
                ),
                "public_key_sha256": MODULE._sha256_bytes(public_key),
            }
        ],
    }

    try:
        MODULE._verify_detached_signature(
            manifest_bytes=b"changed",
            signature_bytes=private_key.sign(b"original"),
            keyring=keyring,
            key_id="test-release-key",
        )
    except MODULE.Pb14GateError as exc:
        assert "verification failed" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("manifest drift must fail signature verification")


def test_isolated_exact_candidate_breach_stops_close_and_fails_closed() -> None:
    descriptor = {
        "component": "client",
        "version": "1.2.0",
        "revision": "a" * 40,
        "artifact_sha256": "b" * 64,
    }
    binding = {
        "candidate_label": "pokrov-1.2.0-candidate.test",
        "candidate_id": MODULE.compute_candidate_id(descriptor),
        "candidate_descriptor": descriptor,
        "manifest_sha256": "b" * 64,
        "client_revision": "a" * 40,
        "core_version": "1.1.0",
        "android_build_number": "4030",
        "version": "1.2.0",
        "rollback_target": "1.1.6",
    }

    result = MODULE._run_isolated_control(binding)

    assert result["database"] == "TEMPORARY_SQLITE_DESTROYED_AFTER_GATE"
    assert result["cohort"] == "ISOLATED_LOCAL_CONTROL_FIXTURE"
    assert result["promotion_stop"] == {
        "status": "PASS",
        "error_code": "release_health_gate_failed",
        "staged_state_preserved": True,
    }
    assert result["rollback_request"]["status"] == "PASS"
    assert result["rollback_request"]["exact_candidate_status"] == "rollback_requested"
    assert result["rollback_request"]["exact_candidate_rollout_percent"] == 0
    assert result["rollback_request"]["rollback_candidate_status"] == "current"
    assert result["rollback_request"]["rollback_candidate_rollout_percent"] == 100
    assert result["rollback_request"]["external_artifact_switch"] == "NOT_PERFORMED"
    assert result["public_policy"] == {
        "exact_candidate_rollout_percent": 0,
        "rollback_candidate_rollout_percent": 100,
    }
