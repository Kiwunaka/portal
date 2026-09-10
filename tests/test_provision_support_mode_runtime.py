from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import provision_support_mode_runtime as provision


def fixture(tmp_path):
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    encode = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    seed = {
        "schema_version": 1, "algorithm": "Ed25519", "purpose": "support-mode-policy-v2",
        "status": "active", "key_id": "owned-fixture", "public_key_b64url": encode(public),
        "public_key_sha256": hashlib.sha256(public).hexdigest(),
    }
    path = tmp_path / "seed.json"
    path.write_text(json.dumps(seed), encoding="utf-8")
    payload = {
        "platform_revision": "a" * 40, "client_revision": "b" * 40,
        "key_id": seed["key_id"], "public_key_b64url": seed["public_key_b64url"],
        "private_key_b64url": encode(key.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())),
        "code_secret": 'owned-fixture-32-byte-secret-"quoted"-\\-value',
    }
    return path, payload


def test_exact_pin_and_atomic_install_preserve_existing_configuration(tmp_path):
    seed, payload = fixture(tmp_path)
    raw, public = provision.environment_bytes(payload, seed)
    assert public["public_key_sha256"] == json.loads(seed.read_text())["public_key_sha256"]
    assert raw.count(b"\n") == 3
    assert b'\\"quoted\\"' in raw and b"\\\\-value" in raw
    target = tmp_path / "support-mode.env"
    assert provision.install_environment(target, raw)
    assert not provision.install_environment(target, raw)
    with pytest.raises(provision.ProvisionError, match="differs"):
        provision.install_environment(target, raw + b"different")
    assert target.read_bytes() == raw
    assert not list(tmp_path.glob(".support-mode-*"))


def test_wrong_private_key_and_multiline_secret_fail_before_install(tmp_path):
    seed, payload = fixture(tmp_path)
    wrong = {**payload, "private_key_b64url": base64.urlsafe_b64encode(bytes(32)).decode().rstrip("=")}
    with pytest.raises(ValueError, match="private key does not match"):
        provision.environment_bytes(wrong, seed)
    with pytest.raises(provision.ProvisionError, match="single environment line"):
        provision.environment_bytes({**payload, "code_secret": payload["code_secret"] + "\nINJECTED=1"}, seed)


def test_sender_rejects_unpinned_server_and_never_writes_secret_output(tmp_path, monkeypatch, capsys):
    seed, payload = fixture(tmp_path)
    for field, env in [("key_id", "POKROV_SUPPORT_MODE_SIGNING_KEY_ID"), ("private_key_b64url", "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64"), ("public_key_b64url", "POKROV_SUPPORT_MODE_SIGNING_PUBLIC_KEY_B64"), ("code_secret", "POKROV_SUPPORT_MODE_CODE_SECRET")]:
        monkeypatch.setenv(env, payload[field])
    # A library exception carrying raw request text must not reach logs/artifacts.
    monkeypatch.setenv("POKROV_SUPPORT_PROVISION_SSH_KEY", payload["private_key_b64url"])
    monkeypatch.setattr(provision.paramiko.Ed25519Key, "from_private_key", lambda *a: object())
    class PinnedConnection:
        def __init__(self):
            self.keys = provision.paramiko.HostKeys()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def get_host_keys(self):
            return self.keys
        def set_missing_host_key_policy(self, policy):
            assert isinstance(policy, provision.paramiko.RejectPolicy)
        def connect(self, host, **kwargs):
            assert host == "82.21.114.104" and kwargs["port"] == 29374
            assert not kwargs["allow_agent"] and not kwargs["look_for_keys"]
            assert self.keys[f"[{host}]:29374"]["ssh-ed25519"].get_base64() == provision.BRAIN_HOST_KEY
            raise provision.paramiko.SSHException(payload["private_key_b64url"] + payload["code_secret"])
    monkeypatch.setattr(provision.paramiko, "SSHClient", PinnedConnection)
    output = tmp_path / "receipt.json"
    assert provision.main(["--client-seed", str(seed), "--platform-revision", "a" * 40, "--client-revision", "b" * 40, "--output", str(output)]) == 1
    log = capsys.readouterr()
    assert payload["private_key_b64url"] not in log.out + log.err
    assert payload["code_secret"] not in log.out + log.err
    assert not output.exists()
