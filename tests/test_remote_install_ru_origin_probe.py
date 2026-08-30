from __future__ import annotations

import argparse
import importlib.util
import inspect
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "remote_install_ru_origin_probe.py"
SPEC = importlib.util.spec_from_file_location("remote_install_ru_origin_probe", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BUNDLE = MODULE.bundle_contract


def _members() -> dict[str, bytes]:
    values: dict[str, bytes] = {}
    for path in BUNDLE.SOURCE_MEMBERS:
        if path == "scripts/internal_hmac_client.py":
            values[path] = b"from internal_request_auth import sign_internal_request\n"
        elif path.endswith(".py"):
            values[path] = b"VALUE = 1\n"
        elif path.endswith("pokrov-ru-probe.service") or path.endswith(
            "pokrov-ru-probe-uploader.service"
        ):
            values[path] = b"\n".join(
                [
                    b"[Service]",
                    b"User=pokrov-ru-probe",
                    b"Group=pokrov-ru-probe",
                    b"UMask=0077",
                    b"NoNewPrivileges=true",
                    b"ProtectSystem=strict",
                    b"ReadWritePaths=/var/lib/pokrov-ru-probe",
                    b"",
                ]
            )
        elif path.endswith("pokrov-ru-probe-uploader.timer"):
            values[path] = b"[Timer]\nOnUnitActiveSec=15m\nPersistent=true\n"
        else:
            values[path] = b"[Timer]\nOnCalendar=*-*-* 00,06,12,18:00:00\nPersistent=true\n"
    return values


def _bundle(tmp_path: Path) -> Path:
    members = _members()
    manifest = BUNDLE._manifest(
        source_revision=BUNDLE.EXPECTED_SOURCE_REVISION,
        source_epoch=1_788_000_000,
        members=members,
    )
    output = tmp_path / "ru-origin.zip"
    BUNDLE._write_bundle(output, manifest=manifest, members=members)
    return output


def _runtime_material(tmp_path: Path) -> Path:
    root = tmp_path / "runtime"
    root.mkdir(parents=True)
    for name in ("probe.env", "uploader.env"):
        (root / name).write_text(
            "POKROV_API_BASE_URL=https://api.pokrov.space\n"
            "POKROV_KEY_ID=ru-mini-v1\n"
            "POKROV_PROBE_HOST_ID=mini\n",
            encoding="utf-8",
        )
    (root / "hmac.key").write_bytes(b"x" * 32)
    (root / "profiles.json").write_text(
        json.dumps(
            {
                "profiles": {
                    "awg-owned": {
                        "executable": "/opt/pokrov/bin/probe-adapter",
                        "argv": ["--mode", "awg"],
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def test_bundle_and_runtime_validate_without_returning_secrets(tmp_path: Path) -> None:
    path, manifest, contents, digest = MODULE._validated_local_bundle(
        _bundle(tmp_path / "bundle")
    )
    _root, runtime, summary = MODULE._validated_runtime_material(
        _runtime_material(tmp_path)
    )

    assert path.is_file()
    assert manifest["source"]["revision"] == BUNDLE.EXPECTED_SOURCE_REVISION
    assert set(contents) == set(BUNDLE.SOURCE_MEMBERS)
    assert len(digest) == 64
    assert set(runtime) == set(MODULE.RUNTIME_FILES)
    assert summary == {
        "supplied": True,
        "file_count": 4,
        "environment_key_count": 6,
        "hmac_length_valid": True,
        "profile_count": 1,
        "raw_runtime_material_returned": False,
        "runtime_material_hashes_returned": False,
    }
    assert "x" * 32 not in json.dumps(summary)


def test_runtime_rejects_extra_secret_env_and_subscription_url(tmp_path: Path) -> None:
    extra = _runtime_material(tmp_path / "extra")
    (extra / "extra.txt").write_text("no", encoding="utf-8")
    with pytest.raises(MODULE.RuProbeRemoteOperationError, match="file_set"):
        MODULE._validated_runtime_material(extra)

    secret = _runtime_material(tmp_path / "secret")
    (secret / "probe.env").write_text("HMAC_SECRET=raw\n", encoding="utf-8")
    with pytest.raises(MODULE.RuProbeRemoteOperationError, match="contract"):
        MODULE._validated_runtime_material(secret)

    subscription = _runtime_material(tmp_path / "subscription")
    payload = json.loads((subscription / "profiles.json").read_text(encoding="utf-8"))
    payload["profiles"]["awg-owned"]["argv"].append("https://example.invalid/sub")
    (subscription / "profiles.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(MODULE.RuProbeRemoteOperationError, match="profiles"):
        MODULE._validated_runtime_material(subscription)


def test_preflight_is_read_only_and_sanitized() -> None:
    command = MODULE._preflight_command()

    for prohibited in (
        "mkdir",
        "install -d",
        "systemctl start",
        "systemctl enable",
        "rm -",
        "cat ",
    ):
        assert prohibited not in command
    assert "installed_target_count=" in command
    assert "spool_pending_count=" in command
    assert "sudo -n true" in command
    assert "test -x /usr/sbin/runuser" in command


def test_runtime_material_accepts_empty_profile_registry(tmp_path: Path) -> None:
    subscription = _runtime_material(tmp_path)
    (subscription / "profiles.json").write_text(
        '{"profiles":{}}\n', encoding="utf-8"
    )

    _root, _values, summary = MODULE._validated_runtime_material(subscription)

    assert summary["profile_count"] == 0


def test_remote_profile_validator_accepts_empty_registry() -> None:
    command = MODULE._profile_remote_validator("/etc/pokrov-ru-probe/profiles.json")
    source = inspect.getsource(MODULE._profile_remote_validator)

    assert "len(profiles) <= 128" in source
    assert "1 <= len(profiles)" not in source
    assert "/etc/pokrov-ru-probe/profiles.json" in command


def test_failure_report_retains_rollback_truth_without_runtime_material() -> None:
    report = MODULE._failure_report(
        operation="install",
        error=MODULE.RuProbeRemoteOperationError("install_apply_failed_exit_1"),
        context={
            "receipt_id": "20260830T000000Z-1-7bc2ec16971a",
            "receipt_created": True,
            "mutation_attempted": True,
            "automatic_rollback_status": "PASS",
        },
    )

    assert report["mode"] == "ERROR"
    assert report["error_code"] == "install_apply_failed_exit_1"
    assert report["automatic_rollback_status"] == "PASS"
    assert report["spool_preserved"] is True
    assert "secret" not in json.dumps(report).lower()


def test_install_verifies_before_timer_activation_and_preserves_spool(
    tmp_path: Path,
) -> None:
    _path, manifest, _contents, _digest = MODULE._validated_local_bundle(
        _bundle(tmp_path)
    )
    command = MODULE._install_command(
        stage_dir=f"{MODULE.STAGE_ROOT}/receipt",
        backup_dir=f"{MODULE.BACKUP_ROOT}/receipt",
        manifest=manifest,
    )

    assert "/usr/sbin/runuser -u pokrov-ru-probe" in command
    assert "ru_probe_runner.py --help" in command
    assert "ru_probe_uploader.py --help" in command
    assert command.index("systemd-analyze verify") < command.index("systemctl enable")
    assert command.index("ru_probe_uploader.py --help") < command.index("systemctl enable")
    assert "systemctl start pokrov-ru-probe.timer" in command
    assert "systemctl start pokrov-ru-probe-uploader.timer" in command
    assert "rm -rf" not in command
    assert (
        f"install -d -o pokrov-ru-probe -g pokrov-ru-probe -m 0700 {MODULE.SPOOL_ROOT}"
        in command
    )


def test_rollback_is_receipt_bound_and_never_deletes_spool() -> None:
    digest = "a" * 64
    receipt = "20260829T120000Z-7-" + digest[:12]
    command = MODULE._rollback_command(
        backup_dir=f"{MODULE.BACKUP_ROOT}/{receipt}",
        bundle_sha256=digest,
        source_revision=BUNDLE.EXPECTED_SOURCE_REVISION,
        node_code="mini",
    )

    assert "disable --now pokrov-ru-probe.timer" in command
    assert "disable --now pokrov-ru-probe-uploader.timer" in command
    assert f"if test -e {MODULE.SPOOL_ROOT}" in command
    assert "userdel" not in command
    assert "groupdel" not in command
    assert "rm -rf" not in command
    assert f"rm -f -- {MODULE.SPOOL_ROOT}" not in command
    for state in ("pending", "blocked", "quarantine", "archive"):
        assert f"rm -f -- {MODULE.SPOOL_ROOT}/{state}" not in command


def test_cleanup_is_restricted_to_receipt_stage() -> None:
    command = MODULE._cleanup_stage_command(f"{MODULE.STAGE_ROOT}/safe-receipt")
    assert "rm -rf" in command
    assert MODULE.STAGE_ROOT in command
    with pytest.raises(MODULE.RuProbeRemoteOperationError, match="stage_path"):
        MODULE._cleanup_stage_command(MODULE.STAGE_ROOT)
    with pytest.raises(MODULE.RuProbeRemoteOperationError, match="stage_path"):
        MODULE._cleanup_stage_command(MODULE.SPOOL_ROOT)


def test_privileged_commands_use_passwordless_sudo_without_secret_input() -> None:
    command = MODULE._as_root("systemctl daemon-reload", use_sudo=True)
    assert command.startswith("sudo -n sh -c ")
    assert "password" not in command.lower()
    assert MODULE._as_root("true", use_sudo=False) == "true"


def test_apply_requires_all_external_mutation_confirmations() -> None:
    args = argparse.Namespace(
        operation="install",
        confirm_external_mutation="",
        confirm_bundle_sha256="a" * 64,
        confirm_source_revision=BUNDLE.EXPECTED_SOURCE_REVISION,
        confirm_node_code="mini",
        confirm_runtime_material_ready="RUNTIME_MATERIAL_READY",
        confirm_spool_preservation="PRESERVE_RU_PROBE_SPOOL",
        confirm_timer_activation="ACTIVATE_RU_PROBE_TIMERS",
    )
    with pytest.raises(MODULE.RuProbeRemoteOperationError, match="external_mutation"):
        MODULE._assert_apply_confirmations(
            args,
            bundle_sha256="a" * 64,
            source_revision=BUNDLE.EXPECTED_SOURCE_REVISION,
            node_code="mini",
        )

    args.confirm_external_mutation = "AUTHORIZED_RU_HOST_MUTATION"
    MODULE._assert_apply_confirmations(
        args,
        bundle_sha256="a" * 64,
        source_revision=BUNDLE.EXPECTED_SOURCE_REVISION,
        node_code="mini",
    )


def test_plan_report_shape_contains_no_host_or_runtime_material(tmp_path: Path) -> None:
    path, manifest, _contents, digest = MODULE._validated_local_bundle(
        _bundle(tmp_path)
    )
    report = {
        "schema_version": MODULE.REPORT_SCHEMA,
        "mode": "PLAN",
        "operation": "install",
        "node_code": "mini",
        "bundle_sha256": digest,
        "source_revision": manifest["source"]["revision"],
        "runtime_material": {
            "supplied": False,
            "raw_runtime_material_returned": False,
            "runtime_material_hashes_returned": False,
        },
        "plan": BUNDLE.plan_bundle(path=path, operation="install"),
        "raw_host_returned": False,
        "mutation_performed": False,
    }
    serialized = json.dumps(report, sort_keys=True)

    assert "private_key" not in serialized
    assert "password" not in serialized
    assert "hmac.key" not in serialized
    assert "node_host" not in serialized
    assert report["mutation_performed"] is False
