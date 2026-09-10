import base64
import errno
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_BOT_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

worker = importlib.import_module("support_bundle_worker")


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _private_bytes(key: x25519.X25519PrivateKey) -> bytes:
    return key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_mounted_worker_key_decrypts_client_protocol_round_trip(tmp_path: Path) -> None:
    recipient = x25519.X25519PrivateKey.generate()
    ephemeral = x25519.X25519PrivateKey.generate()
    diagnostic_id = "diag-0123456789abcdef01234567"
    manifest_sha256 = "a" * 64
    shared = ephemeral.exchange(recipient.public_key())
    key = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=diagnostic_id.encode("utf-8"),
        info=b"pokrov-support-bundle-v1",
    ).derive(shared)
    nonce = b"n" * 12
    plaintext = b'{"files":[],"manifest":{},"schema_version":1}'
    sealed = AESGCM(key).encrypt(nonce, plaintext, manifest_sha256.encode("utf-8"))

    key_file = (tmp_path / "recipient-keys.json").resolve()
    key_file.write_text(
        json.dumps(
            {
                "keys": [
                    {
                        "key_id": "support-test-1",
                        "private_key_b64": _b64(_private_bytes(recipient)),
                    }
                ],
                "schema_version": 1,
            }
        ),
        encoding="utf-8",
    )
    decryptor = worker.load_mounted_support_decryptor(key_file)
    envelope = {
        "ciphertext_b64": _b64(sealed[:-16]),
        "diagnostic_id": diagnostic_id,
        "ephemeral_public_key_b64": _b64(
            ephemeral.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ),
        "mac_b64": _b64(sealed[-16:]),
        "manifest_sha256": manifest_sha256,
        "nonce_b64": _b64(nonce),
        "recipient_key_id": "support-test-1",
    }

    assert decryptor(envelope) == plaintext
    exported = dict(decryptor._private_keys)
    exported["support-test-1"] = b"x" * 32
    assert decryptor(envelope) == plaintext


def test_worker_key_file_rejects_relative_symlink_and_duplicate_keys(
    tmp_path: Path,
) -> None:
    with pytest.raises(worker.SupportBundleWorkerConfigError):
        worker.load_mounted_support_decryptor(Path("relative.json"))

    private_key = _b64(_private_bytes(x25519.X25519PrivateKey.generate()))
    duplicate = (tmp_path / "duplicate.json").resolve()
    duplicate.write_text(
        '{"keys":[{"key_id":"support-test-1","private_key_b64":"'
        + private_key
        + '"},{"key_id":"support-test-1","private_key_b64":"'
        + private_key
        + '"}],"schema_version":1}',
        encoding="utf-8",
    )
    with pytest.raises(worker.SupportBundleWorkerConfigError):
        worker.load_mounted_support_decryptor(duplicate)

    alias = (tmp_path / "alias.json").resolve()
    try:
        alias.symlink_to(duplicate)
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(worker.SupportBundleWorkerConfigError):
        worker.load_mounted_support_decryptor(alias)


def test_platform_worker_wiring_is_opt_in() -> None:
    source = (PORTAL_BOT_DIR / "worker.py").read_text(encoding="utf-8")
    assert 'os.getenv("POKROV_SUPPORT_BUNDLE_WORKER_ENABLED")' in source
    assert "if SUPPORT_BUNDLE_WORKER_ENABLED:" in source
    assert (
        '_supervise_job("support_bundle_ingest", support_bundle_ingest_job)' in source
    )


def test_support_health_reports_stopped_worker_and_corrupt_signal(monkeypatch, tmp_path) -> None:
    health = importlib.import_module("support_bundle_health")
    accepted = tmp_path / "accepted"
    monkeypatch.setenv("POKROV_SUPPORT_BUNDLE_ACCEPTED_DIR", str(accepted))
    now = datetime.now(timezone.utc)
    observed = int(now.timestamp())
    assert health.write_support_bundle_health(accepted, {"started_at": observed})
    assert health.support_bundle_health_alerts(now=now) == []
    assert health.support_bundle_health_alerts(now=now + timedelta(seconds=61))[0]["fingerprint"] == "support_bundle_health_unavailable"
    assert health.write_support_bundle_health(accepted, {
        "ingest": {"observed_at": observed, "errors": 0},
        "retention": {"observed_at": observed, "errors": 0},
    })
    assert health.support_bundle_health_alerts(now=now) == []
    stale = health.support_bundle_health_alerts(now=now + timedelta(seconds=601))
    assert [item["fingerprint"] for item in stale] == ["support_bundle_health_ingest"]
    assert stale[0]["metadata"]["state"] == "stale"
    (tmp_path / health.HEALTH_FILE_NAME).write_text('{"schema_version":2,"raw":"planted-private-value"}', encoding="utf8")
    invalid = health.support_bundle_health_alerts(now=now)
    assert invalid[0]["fingerprint"] == "support_bundle_health_unavailable"
    assert "planted-private-value" not in json.dumps(invalid)


def test_support_health_disk_full_preserves_previous_signal(monkeypatch, tmp_path) -> None:
    health = importlib.import_module("support_bundle_health")
    accepted = tmp_path / "accepted"
    previous = {"ingest": {"observed_at": 123, "errors": 0}}
    assert health.write_support_bundle_health(accepted, previous)
    stored = tmp_path / health.HEALTH_FILE_NAME
    before = stored.read_bytes()

    def disk_full(*_args):
        raise OSError(errno.ENOSPC, "fixture disk full")

    monkeypatch.setattr(health.os, "replace", disk_full)
    assert not health.write_support_bundle_health(accepted, {"ingest": {"observed_at": 124, "errors": 1}})
    assert stored.read_bytes() == before
    assert list(tmp_path.iterdir()) == [stored]
