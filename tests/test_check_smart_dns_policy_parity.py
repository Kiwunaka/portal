from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_smart_dns_policy_parity.py"
SPEC = importlib.util.spec_from_file_location("check_smart_dns_policy_parity", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_matching_bytes_pass(tmp_path: Path) -> None:
    platform = tmp_path / "platform.json"
    client = tmp_path / "client.json"
    platform.write_bytes(MODULE.PLATFORM_POLICY.read_bytes())
    client.write_bytes(platform.read_bytes())
    digest = MODULE.check_policy_parity(platform, client)
    assert len(digest) == 64


def test_lf_and_windows_crlf_share_canonical_digest(tmp_path: Path) -> None:
    platform = tmp_path / "platform.json"
    client = tmp_path / "client.json"
    lf = MODULE.PLATFORM_POLICY.read_bytes().replace(b"\r\n", b"\n")
    platform.write_bytes(lf)
    client.write_bytes(lf.replace(b"\n", b"\r\n"))

    digest = MODULE.check_policy_parity(platform, client)

    assert digest == MODULE.hashlib.sha256(lf).hexdigest()


def test_semantic_or_byte_drift_fails_closed(tmp_path: Path) -> None:
    platform = tmp_path / "platform.json"
    client = tmp_path / "client.json"
    document = {
        "schema_version": "pokrov-smart-dns-policy-v1",
        "state": "owner_lab_default_off",
        "groups": {"ai": ["openai.com"], "gaming_services": ["xbox.com"]},
        "recursive_dns": False,
    }
    platform.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    client.write_text(json.dumps(document, sort_keys=True, indent=2), encoding="utf-8")
    with pytest.raises(MODULE.PolicyParityError, match="bytes differ"):
        MODULE.check_policy_parity(platform, client)

    client.write_text(
        json.dumps({**document, "recursive_dns": True}, sort_keys=True),
        encoding="utf-8",
    )
    with pytest.raises(MODULE.PolicyParityError, match="documents differ"):
        MODULE.check_policy_parity(platform, client)


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        (b"{\r}\n", "lone carriage return"),
        (b"\xef\xbb\xbf{}\n", "BOM forbidden"),
        (b"\xff\xfe", "must be UTF-8"),
    ],
)
def test_noncanonical_policy_bytes_fail_closed(
    tmp_path: Path,
    payload: bytes,
    error: str,
) -> None:
    policy = tmp_path / "policy.json"
    policy.write_bytes(payload)

    with pytest.raises(MODULE.PolicyParityError, match=error):
        MODULE._load_policy(policy)
