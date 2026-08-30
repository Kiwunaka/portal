from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_module():
    path = SCRIPTS_DIR / "remote_prepare_ru_origin_auth.py"
    spec = importlib.util.spec_from_file_location("remote_prepare_ru_origin_auth_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MODULE = _load_module()


def test_preflight_is_read_only_and_reports_exact_target_state() -> None:
    command = MODULE._preflight_command()

    assert "systemctl is-active --quiet portal-api" in command
    assert MODULE.REGISTRY_PATH in command
    assert MODULE.DROPIN_PATH in command
    assert "systemctl restart" not in command
    assert "install -D" not in command
    assert "rm -f" not in command


def test_registry_has_one_exact_scoped_key_without_extra_truth() -> None:
    secret = b"A" * 32
    payload = json.loads(MODULE._registry(secret))

    assert payload == {
        "keys": [
            {
                "enabled": True,
                "key_id": "ru-mini-v1",
                "origins": ["ru"],
                "scopes": [
                    "ru_probe:heartbeat",
                    "ru_probe:ingest",
                    "ru_probe:manifest",
                ],
                "secret": "A" * 32,
                "subject": "mini",
            }
        ]
    }


def test_secret_rejects_whitespace_and_accepts_visible_ascii(tmp_path: Path) -> None:
    good = tmp_path / "good.key"
    good.write_bytes(b"B" * 32)
    assert MODULE._secret(good) == b"B" * 32

    bad = tmp_path / "bad.key"
    bad.write_bytes(b"B" * 31 + b"\n")
    with pytest.raises(MODULE.RuOriginAuthError, match="visible_ascii"):
        MODULE._secret(bad)


def test_apply_orders_owned_files_before_restart_and_keeps_secret_out_of_command() -> None:
    command = MODULE._apply_command(stage_dir="/root/stage/one", receipt_dir="/root/receipt/one")

    assert command.index("registry.json") < command.index("systemctl restart portal-api")
    assert command.index("dropin.conf") < command.index("systemctl restart portal-api")
    assert "secret" not in command.lower()
    assert "stat -c %a" in command
    assert "systemctl is-active --quiet portal-api" in command


def test_rollback_requires_owned_receipt_and_managed_markers() -> None:
    command = MODULE._rollback_command(receipt_dir="/root/receipt/20260830T000000Z-1")

    assert MODULE.RECEIPT_SCHEMA in command or "base64 -d" in command
    assert "Managed by scripts/remote_prepare_ru_origin_auth.py" not in command
    assert command.index("receipt.json") < command.index("rm -f")
    assert command.index("rm -f") < command.index("systemctl restart portal-api")


def test_failure_cleanup_removes_secret_stage_before_restart() -> None:
    command = MODULE._cleanup_command(
        stage_dir="/root/stage/one", receipt_dir="/root/receipt/one"
    )

    assert command.startswith("set -e")
    assert command.index("rm -rf") < command.index("systemctl restart portal-api")


def test_install_preflight_fails_closed_on_existing_targets() -> None:
    values = {
        "effective_uid_root": True,
        "python3_present": True,
        "install_present": True,
        "systemctl_present": True,
        "portal_api_active": True,
        "registry_present": True,
        "dropin_present": False,
        "registry_env_configured": False,
    }

    with pytest.raises(MODULE.RuOriginAuthError, match="target_already_present"):
        MODULE._assert_install_preflight(values)


def test_signed_manifest_reports_bounded_http_failure(monkeypatch, tmp_path: Path) -> None:
    secret = tmp_path / "secret.key"
    secret.write_bytes(b"C" * 32)
    response = MODULE.internal_hmac_client.InternalResponse(
        status=403,
        body=b'{"code":"key_scope_forbidden","correlation_id":"redacted"}',
        headers={},
    )
    monkeypatch.setattr(
        MODULE.internal_hmac_client, "signed_request", lambda **_kwargs: response
    )

    with pytest.raises(
        MODULE.RuOriginAuthError,
        match="signed_manifest_http_403_key_scope_forbidden",
    ):
        MODULE._signed_manifest(secret, attempts=1, retry_seconds=0)


def test_signed_manifest_retries_transient_non_json_502(monkeypatch, tmp_path: Path) -> None:
    secret = tmp_path / "secret.key"
    secret.write_bytes(b"D" * 32)
    responses = iter(
        [
            MODULE.internal_hmac_client.InternalResponse(
                status=502, body=b"temporary upstream gap", headers={}
            ),
            MODULE.internal_hmac_client.InternalResponse(
                status=200,
                body=(
                    b'{"targets":[{"scope":"release_required","endpoint":'
                    b'{"local_probe_profile_id":null}}]}'
                ),
                headers={},
            ),
        ]
    )
    sleeps: list[float] = []
    monkeypatch.setattr(
        MODULE.internal_hmac_client,
        "signed_request",
        lambda **_kwargs: next(responses),
    )

    report = MODULE._signed_manifest(
        secret,
        attempts=2,
        retry_seconds=0.25,
        sleep_fn=sleeps.append,
    )

    assert report["http_status"] == 200
    assert report["readiness_attempts"] == 2
    assert report["target_count"] == 1
    assert sleeps == [0.25]
