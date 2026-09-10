from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "verify_support_signing_custody.py"
SPEC = importlib.util.spec_from_file_location("verify_support_signing_custody", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _fixture(tmp_path: Path, *, private_bytes: bytes = bytes(range(32))) -> dict[str, object]:
    private_key = Ed25519PrivateKey.from_private_bytes(private_bytes)
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    seed = {
        "schema_version": 1,
        "algorithm": "Ed25519",
        "purpose": "support-mode-policy-v2",
        "status": "active",
        "key_id": "pokrov-support-test",
        "public_key_b64url": _b64url(public_bytes),
        "public_key_sha256": hashlib.sha256(public_bytes).hexdigest(),
    }
    seed_path = tmp_path / "support-signing.seed.json"
    seed_path.write_text(json.dumps(seed, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "seed": seed,
        "seed_path": seed_path,
        "private_b64url": _b64url(private_bytes),
        "code_secret": "c" * 32,
    }


def _verify(fixture: dict[str, object], **overrides: object) -> dict[str, object]:
    seed = fixture["seed"]
    assert isinstance(seed, dict)
    values = {
        "client_seed_path": fixture["seed_path"],
        "platform_revision": "a" * 40,
        "client_revision": "b" * 40,
        "key_id": seed["key_id"],
        "private_key_b64url": fixture["private_b64url"],
        "public_key_b64url": seed["public_key_b64url"],
        "code_secret": fixture["code_secret"],
    }
    values.update(overrides)
    return MODULE.verify_custody(**values)


def test_valid_custody_receipt_contains_only_public_proof(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)

    receipt = _verify(fixture)
    serialized = json.dumps(receipt, sort_keys=True)

    assert receipt["status"] == "PASS"
    assert receipt["scope"] == "hosted_source_control_custody"
    assert receipt["candidate_created"] is False
    assert receipt["production_runtime_mutated"] is False
    assert receipt["key_id"] == "pokrov-support-test"
    assert str(fixture["private_b64url"]) not in serialized
    assert str(fixture["code_secret"]) not in serialized


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"key_id": "different-key"}, "key id"),
        ({"private_key_b64url": _b64url(b"z" * 32)}, "private key"),
        ({"public_key_b64url": _b64url(b"p" * 32)}, "public key"),
        ({"code_secret": "short"}, "code secret"),
        ({"client_revision": "not-a-revision"}, "client revision"),
        ({"client_revision": "B" * 40}, "client revision"),
    ],
)
def test_custody_mismatch_fails_closed(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    fixture = _fixture(tmp_path)

    with pytest.raises(MODULE.CustodyVerificationError, match=message):
        _verify(fixture, **overrides)


def test_seed_rejects_unknown_fields_and_noncanonical_public_encoding(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    seed_path = fixture["seed_path"]
    assert isinstance(seed_path, Path)
    seed = fixture["seed"]
    assert isinstance(seed, dict)
    seed["unexpected"] = True
    seed_path.write_text(json.dumps(seed) + "\n", encoding="utf-8")
    with pytest.raises(MODULE.CustodyVerificationError, match="closed schema"):
        _verify(fixture)

    seed.pop("unexpected")
    seed["public_key_b64url"] = str(seed["public_key_b64url"])[:-1] + "F"
    seed_path.write_text(json.dumps(seed) + "\n", encoding="utf-8")
    with pytest.raises(MODULE.CustodyVerificationError, match="canonical"):
        _verify(fixture)


@pytest.mark.parametrize("publish_recipient", [False, True])
def test_cli_writes_public_receipt_without_echoing_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    publish_recipient: bool,
) -> None:
    fixture = _fixture(tmp_path)
    seed = fixture["seed"]
    assert isinstance(seed, dict)
    monkeypatch.setenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", str(seed["key_id"]))
    monkeypatch.setenv(
        "POKROV_SUPPORT_MODE_SIGNING_PUBLIC_KEY_B64",
        str(seed["public_key_b64url"]),
    )
    monkeypatch.setenv(
        "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64",
        str(fixture["private_b64url"]),
    )
    monkeypatch.setenv("POKROV_SUPPORT_MODE_CODE_SECRET", str(fixture["code_secret"]))
    output = tmp_path / "receipt.json"
    key_set_output = tmp_path / "signed-key-set.json"
    recipient = X25519PrivateKey.generate()
    recipient_public = _b64url(recipient.public_key().public_bytes_raw())
    monkeypatch.setenv("POKROV_SUPPORT_RECIPIENT_KEY_ID", "worker-test" if publish_recipient else "")
    monkeypatch.setenv("POKROV_SUPPORT_RECIPIENT_PUBLIC_KEY_B64", recipient_public if publish_recipient else "")

    exit_code = MODULE.main(
        [
            "--client-seed",
            str(fixture["seed_path"]),
            "--platform-revision",
            "a" * 40,
            "--client-revision",
            "b" * 40,
            "--output",
            str(output),
            "--signed-key-set-output",
            str(key_set_output),
        ]
    )

    captured = capsys.readouterr()
    receipt_text = output.read_text(encoding="utf-8")
    assert exit_code == 0
    assert "Support signing custody verified" in captured.out
    assert key_set_output.exists() is publish_recipient
    if publish_recipient:
        envelope = json.loads(key_set_output.read_text(encoding="utf-8"))
        raw = base64.urlsafe_b64decode(envelope["payload_b64"] + "=" * (-len(envelope["payload_b64"]) % 4))
        signature = base64.urlsafe_b64decode(envelope["signature_b64"] + "=" * (-len(envelope["signature_b64"]) % 4))
        Ed25519PrivateKey.from_private_bytes(bytes(range(32))).public_key().verify(signature, raw)
        payload = json.loads(raw)
        assert envelope["key_id"] == seed["key_id"]
        assert set(payload) == {"schema_version", "type", "issued_at", "expires_at", "keys"}
        assert payload["type"] == "pokrov.support.key_set"
        assert datetime.fromisoformat(payload["expires_at"]) - datetime.fromisoformat(payload["issued_at"]) == timedelta(days=30)
        assert payload["keys"] == [{
            "algorithm": "X25519-HKDF-SHA256-AES-256-GCM",
            "key_id": "worker-test", "not_after": payload["expires_at"],
            "public_key_b64": recipient_public,
        }]
        receipt_text += key_set_output.read_text(encoding="utf-8")
    for secret in (str(fixture["private_b64url"]), str(fixture["code_secret"])):
        assert secret not in captured.out
        assert secret not in captured.err
        assert secret not in receipt_text


@pytest.mark.parametrize("key_id,public_key", [
    ("", _b64url(b"p" * 32)),
    ("worker-test", ""),
    ("worker-test", _b64url(bytes(32))),
])
def test_recipient_signing_rejects_incomplete_or_unusable_key(key_id: str, public_key: str) -> None:
    with pytest.raises(MODULE.CustodyVerificationError):
        MODULE._sign_recipient_key_set(
            signing_key_id="pokrov-support-test",
            private_key_b64url=_b64url(bytes(range(32))),
            recipient_key_id=key_id,
            recipient_public_key_b64url=public_key,
            now=datetime(2026, 9, 10, tzinfo=timezone.utc),
        )
