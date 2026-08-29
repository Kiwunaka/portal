from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "remote_migrate_owned_smart_dns_frontend.py"
SPEC = importlib.util.spec_from_file_location("remote_migrate_owned_smart_dns_frontend", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _base_config() -> bytes:
    return MODULE._canonical_text(MODULE.DEFAULT_BASE_CONFIG)


def _ready_preflight(
    *,
    base_sha256: str,
    base_service_sha256: str,
    release_sha256: str,
) -> dict[str, object]:
    return {
        "haproxy_present": True,
        "systemd_present": True,
        "effective_uid_root": True,
        "python3_present": True,
        "base64_present": True,
        "curl_present": True,
        "config_present": True,
        "config_sha256": base_sha256,
        "service_unit_present": True,
        "service_unit_sha256": base_service_sha256,
        "service_reload_signal_present": False,
        "frontend_config_valid": True,
        "frontend_state": "active",
        "frontend_enabled": "enabled",
        "public_443_listening": True,
        "smart_dns_state": "active",
        "smart_dns_enabled": "disabled",
        "smart_dns_fronted_config_valid": True,
        "smart_dns_loopback_listener": True,
        "smart_dns_nonloopback_listener": False,
        "smart_dns_release_sha256": release_sha256,
        "smart_dns_route_present": False,
    }


def test_candidate_config_uses_canonical_exact_child_routes_and_proxy_v2() -> None:
    base = _base_config()
    candidate, metadata = MODULE.build_candidate_config(
        base_config=base,
        doh_hostname="DNS.Pokrov.Space.",
    )
    text = candidate.decode("utf-8")

    assert metadata["application_suffix_count"] == 19
    assert metadata["exact_sni_route_count"] == 20
    assert metadata["child_sni_route_count"] == 19
    assert metadata["policy_sha256"] == "b6977f6f6a5ee48898116820d1db252b5b670cb7b86959c78f7bdbc7de90e0fa"
    assert "use_backend be_smart_dns if { req.ssl_sni -i dns.pokrov.space }" in text
    assert "use_backend be_smart_dns if { req.ssl_sni -i openai.com }" in text
    assert "use_backend be_smart_dns if { req.ssl_sni -m end -i .openai.com }" in text
    assert text.index("use_backend be_smart_dns") < text.index(
        "default_backend be_legacy_reality_fallback"
    )
    assert "server smart_dns 127.0.0.1:18443 check send-proxy-v2" in text
    assert b"be_smart_dns" not in base


def test_candidate_config_rejects_hostname_injection() -> None:
    with pytest.raises(MODULE.SmartDNSFrontendMigrationError, match="doh_hostname_invalid"):
        MODULE.build_candidate_config(
            base_config=_base_config(),
            doh_hostname="dns.pokrov.space\nbackend injected",
        )


def test_candidate_config_rejects_doh_hostname_owned_by_base_route() -> None:
    with pytest.raises(
        MODULE.SmartDNSFrontendMigrationError,
        match="doh_hostname_conflicts_with_base_route",
    ):
        MODULE.build_candidate_config(
            base_config=_base_config(),
            doh_hostname="connect.pokrov.space",
        )


def test_candidate_config_rejects_nonloopback_or_existing_backend() -> None:
    nonloopback = _base_config().replace(b"127.0.0.1:10443", b"10.0.0.4:10443")
    with pytest.raises(MODULE.SmartDNSFrontendMigrationError, match="base_backend_not_loopback"):
        MODULE.build_candidate_config(
            base_config=nonloopback,
            doh_hostname="dns.pokrov.space",
        )

    existing = _base_config() + b"\nbackend be_smart_dns\n"
    with pytest.raises(
        MODULE.SmartDNSFrontendMigrationError,
        match="base_smart_dns_route_already_present",
    ):
        MODULE.build_candidate_config(
            base_config=existing,
            doh_hostname="dns.pokrov.space",
        )


def test_policy_loader_rejects_noncanonical_duplicate_suffix(tmp_path: Path) -> None:
    policy = json.loads(MODULE.POLICY_PATH.read_text(encoding="utf-8"))
    policy["groups"]["ai"].append(policy["groups"]["ai"][0])
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(policy) + "\n", encoding="utf-8")

    with pytest.raises(
        MODULE.SmartDNSFrontendMigrationError,
        match="policy_suffix_not_unique_canonical",
    ):
        MODULE._load_policy_suffixes(path)


def test_preflight_command_is_read_only_and_sanitized() -> None:
    command = MODULE._preflight_command()

    for prohibited in (
        "systemctl reload",
        "systemctl restart",
        "systemctl enable",
        "systemctl disable",
        "rm -",
        "mv -",
        "install -",
        "ufw ",
        "cat ",
    ):
        assert prohibited not in command
    assert "sha256sum" in command
    assert "haproxy -c" in command
    assert "smart_dns_release_sha256" in command
    assert "smart_dns_nonloopback_listener" in command
    assert "smart_dns_fronted_config_valid" in command
    assert "curl_present" in command
    assert "effective_uid_root" in command
    assert "service_unit_sha256" in command
    assert "ExecReload=/bin/kill -USR2 \\$MAINPID" in command


def test_parse_probe_rejects_duplicate_or_unbounded_values() -> None:
    with pytest.raises(MODULE.SmartDNSFrontendMigrationError):
        MODULE._parse_probe("state=yes\nstate=no")
    with pytest.raises(MODULE.SmartDNSFrontendMigrationError):
        MODULE._parse_probe("state=contains whitespace")


def test_install_preflight_requires_exact_baseline_backend_and_candidate() -> None:
    base_sha256 = "a" * 64
    base_service_sha256 = "e" * 64
    release_sha256 = "b" * 64
    ready = _ready_preflight(
        base_sha256=base_sha256,
        base_service_sha256=base_service_sha256,
        release_sha256=release_sha256,
    )
    MODULE._assert_install_preflight(
        ready,
        base_sha256=base_sha256,
        base_service_sha256=base_service_sha256,
        smart_dns_release_sha256=release_sha256,
        candidate_valid=True,
    )

    cases = (
        {"effective_uid_root": False},
        {"config_sha256": "c" * 64},
        {"service_unit_sha256": "f" * 64},
        {"smart_dns_state": "inactive"},
        {"smart_dns_fronted_config_valid": False},
        {"smart_dns_loopback_listener": False},
        {"smart_dns_nonloopback_listener": True},
        {"smart_dns_route_present": True},
        {"smart_dns_release_sha256": "d" * 64},
    )
    for override in cases:
        blocked = dict(ready)
        blocked.update(override)
        with pytest.raises(MODULE.SmartDNSFrontendMigrationError):
            MODULE._assert_install_preflight(
                blocked,
                base_sha256=base_sha256,
                base_service_sha256=base_service_sha256,
                smart_dns_release_sha256=release_sha256,
                candidate_valid=True,
            )


def test_receipt_preflight_requires_root_only_exact_digest_bound_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base_sha256 = "a" * 64
    candidate_sha256 = "b" * 64
    base_service_sha256 = "c" * 64
    candidate_service_sha256 = "d" * 64
    release_sha256 = "e" * 64
    output = "\n".join(
        (
            "backup_dir_mode=700",
            f"base_config_sha256={base_sha256}",
            f"candidate_config_sha256={candidate_sha256}",
            f"base_service_sha256={base_service_sha256}",
            f"candidate_service_sha256={candidate_service_sha256}",
            f"smart_dns_release_sha256={release_sha256}",
            "receipt_node_code=ru",
            "receipt_state=applied",
            f"backup_config_sha256={base_sha256}",
            f"backup_service_sha256={base_service_sha256}",
            "backup_config_valid=yes",
        )
    )
    monkeypatch.setattr(MODULE, "_run", lambda *_args, **_kwargs: output)

    receipt = MODULE._remote_receipt_preflight(object(), "/root/receipt")

    assert receipt == {
        "base_config_sha256": base_sha256,
        "candidate_config_sha256": candidate_sha256,
        "base_service_sha256": base_service_sha256,
        "candidate_service_sha256": candidate_service_sha256,
        "smart_dns_release_sha256": release_sha256,
        "node_code": "ru",
        "state": "applied",
        "backup_config_valid": True,
    }

    mismatched = output.replace(
        f"backup_config_sha256={base_sha256}",
        f"backup_config_sha256={'f' * 64}",
    )
    monkeypatch.setattr(MODULE, "_run", lambda *_args, **_kwargs: mismatched)
    with pytest.raises(
        MODULE.SmartDNSFrontendMigrationError,
        match="receipt_backup_digest_mismatch",
    ):
        MODULE._remote_receipt_preflight(object(), "/root/receipt")


def test_rollback_preflight_requires_exact_applied_candidate_and_node() -> None:
    receipt = {
        "candidate_config_sha256": "a" * 64,
        "candidate_service_sha256": "b" * 64,
        "node_code": "ru",
        "state": "applied",
        "backup_config_valid": True,
        "smart_dns_release_sha256": "c" * 64,
    }
    preflight = _ready_preflight(
        base_sha256=str(receipt["candidate_config_sha256"]),
        base_service_sha256=str(receipt["candidate_service_sha256"]),
        release_sha256="c" * 64,
    )
    MODULE._assert_rollback_preflight(preflight, receipt, node_code="ru")

    for override in (
        {"config_sha256": "d" * 64},
        {"service_unit_sha256": "e" * 64},
        {"effective_uid_root": False},
        {"smart_dns_release_sha256": "f" * 64},
    ):
        blocked = dict(preflight)
        blocked.update(override)
        with pytest.raises(MODULE.SmartDNSFrontendMigrationError):
            MODULE._assert_rollback_preflight(blocked, receipt, node_code="ru")

    with pytest.raises(MODULE.SmartDNSFrontendMigrationError, match="receipt_node_mismatch"):
        MODULE._assert_rollback_preflight(preflight, receipt, node_code="de")


def test_apply_and_rollback_commands_are_receipt_and_digest_bound() -> None:
    base_sha256 = "a" * 64
    candidate_sha256 = "b" * 64
    base_service_sha256 = "d" * 64
    candidate_service_sha256 = "e" * 64
    release_sha256 = "c" * 64
    receipt = "20260829T120000Z-42-bbbbbbbbbbbb"
    backup = f"{MODULE.BACKUP_ROOT}/{receipt}"
    stage_config = f"{MODULE.STAGE_ROOT}/{receipt}/candidate.cfg"
    stage_service = f"{MODULE.STAGE_ROOT}/{receipt}/candidate.service"

    backup_command = MODULE._backup_command(
        backup_dir=backup,
        base_sha256=base_sha256,
        candidate_sha256=candidate_sha256,
        base_service_sha256=base_service_sha256,
        candidate_service_sha256=candidate_service_sha256,
        smart_dns_release_sha256=release_sha256,
        node_code="de",
    )
    apply_command = MODULE._apply_command(
        stage_config_path=stage_config,
        stage_service_path=stage_service,
        backup_dir=backup,
        base_sha256=base_sha256,
        candidate_sha256=candidate_sha256,
        base_service_sha256=base_service_sha256,
        candidate_service_sha256=candidate_service_sha256,
        smart_dns_release_sha256=release_sha256,
        node_code="de",
        doh_hostname="dns.pokrov.space",
    )
    rollback_command = MODULE._rollback_command(
        backup_dir=backup,
        base_sha256=base_sha256,
        candidate_sha256=candidate_sha256,
        base_service_sha256=base_service_sha256,
        candidate_service_sha256=candidate_service_sha256,
        smart_dns_release_sha256=release_sha256,
        node_code="de",
        require_candidate_current=True,
    )

    for expected in (
        base_sha256,
        candidate_sha256,
        base_service_sha256,
        candidate_service_sha256,
        release_sha256,
        "node-code",
    ):
        assert expected in backup_command + apply_command + rollback_command
    assert "haproxy -c" in apply_command
    assert "/bin/kill -USR2 \"$main_pid\"" in apply_command
    assert "systemctl daemon-reload" in apply_command
    assert "--resolve dns.pokrov.space:443:127.0.0.1" in apply_command
    assert "https://dns.pokrov.space/dns-query" in apply_command
    assert "= 400" in apply_command
    assert "receipt-state" in backup_command
    assert "grep -qx prepared" in apply_command
    assert "grep -qx applied" in rollback_command
    assert MODULE.SMART_DNS_CURRENT in rollback_command
    assert "rolled_back" in rollback_command
    assert "rm -rf" not in backup_command + apply_command + rollback_command

    automatic_rollback = MODULE._rollback_command(
        backup_dir=backup,
        base_sha256=base_sha256,
        candidate_sha256=candidate_sha256,
        base_service_sha256=base_service_sha256,
        candidate_service_sha256=candidate_service_sha256,
        smart_dns_release_sha256=release_sha256,
        node_code="de",
        require_candidate_current=False,
    )
    assert "current_config_sha=" in automatic_rollback
    assert "current_service_sha=" in automatic_rollback
    assert "case \"$current_config_sha\"" in automatic_rollback
    assert "case \"$current_service_sha\"" in automatic_rollback


def test_online_apply_passes_doh_hostname_only_to_apply_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    class FakeSSH:
        def close(self) -> None:
            return None

    base = MODULE._canonical_text(MODULE.DEFAULT_BASE_CONFIG)
    candidate, _ = MODULE.build_candidate_config(
        base_config=base,
        doh_hostname="dns.pokrov.space",
    )
    base_sha256 = MODULE._sha256_bytes(base)
    candidate_sha256 = MODULE._sha256_bytes(candidate)
    base_service_sha256 = MODULE._sha256_bytes(
        MODULE._canonical_text(MODULE.DEFAULT_BASE_SERVICE)
    )
    candidate_service_sha256 = MODULE._sha256_bytes(
        MODULE._canonical_text(MODULE.CANDIDATE_SERVICE)
    )
    release_sha256 = "f" * 64
    preflight = _ready_preflight(
        base_sha256=base_sha256,
        base_service_sha256=base_service_sha256,
        release_sha256=release_sha256,
    )
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text("safe fixture\n", encoding="utf-8")
    commands: dict[str, str] = {}

    monkeypatch.setattr(MODULE, "_connect_owned", lambda **_kwargs: (FakeSSH(), "key"))
    monkeypatch.setattr(MODULE, "_resolve_node_host", lambda *_args: "node.invalid")
    monkeypatch.setattr(MODULE, "_remote_preflight", lambda *_args: preflight)
    monkeypatch.setattr(MODULE, "_remote_write", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        MODULE,
        "_runtime_transform",
        lambda *_args, **_kwargs: {
            "base_config_sha256": base_sha256,
            "candidate_config_sha256": candidate_sha256,
            "candidate_config_valid": True,
            "base_config_valid": True,
        },
    )

    def fake_run(_ssh: object, command: str, *, label: str, **_kwargs: object) -> str:
        commands[label] = command
        return ""

    monkeypatch.setattr(MODULE, "_run", fake_run)
    monkeypatch.setattr(MODULE, "_run_allow_failure", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--brain-host",
            "brain.invalid",
            "--node-code",
            "ru",
            "--known-hosts",
            str(known_hosts),
            "--doh-hostname",
            "dns.pokrov.space",
            "--apply",
            "--confirm-base-config-sha256",
            base_sha256,
            "--confirm-candidate-config-sha256",
            candidate_sha256,
            "--confirm-base-service-sha256",
            base_service_sha256,
            "--confirm-candidate-service-sha256",
            candidate_service_sha256,
            "--confirm-smart-dns-release-sha256",
            release_sha256,
            "--confirm-node-code",
            "ru",
            "--confirm-client-selection-disabled",
            "CLIENT_SELECTION_DISABLED",
            "--confirm-external-mutation",
            "FRONTEND_MUTATION_AUTHORIZED",
        ],
    )

    assert MODULE.main() == 0
    assert "dns.pokrov.space" not in commands["receipt_backup"]
    assert "--resolve dns.pokrov.space:443:127.0.0.1" in commands["frontend_apply"]

    receipt_id = "20260829T120000Z-42-bbbbbbbbbbbb"
    failure_report = tmp_path / "apply-failure.json"
    monkeypatch.setattr(MODULE, "_release_id", lambda *_args: receipt_id)

    def failing_run(_ssh: object, command: str, *, label: str, **_kwargs: object) -> str:
        commands[label] = command
        if label in {"frontend_apply", "automatic_rollback"}:
            raise MODULE.SmartDNSFrontendMigrationError(label + "_failed")
        return ""

    monkeypatch.setattr(MODULE, "_run", failing_run)
    monkeypatch.setattr(sys, "argv", [*sys.argv, "--json-out", str(failure_report)])

    assert MODULE.main() == 1
    failed = json.loads(failure_report.read_text(encoding="utf-8"))
    assert failed["receipt_id"] == receipt_id
    assert failed["receipt_created"] is True
    assert failed["mutation_attempted"] is True
    assert failed["automatic_rollback_status"] == "FAIL"
    assert failed["raw_runtime_material_returned"] is False
    stderr = capsys.readouterr().err
    assert "receipt_id=" + receipt_id in stderr
    assert "automatic_rollback_status=FAIL" in stderr


def test_rollback_plan_uses_receipt_without_rebuilding_runtime_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSSH:
        def close(self) -> None:
            return None

    receipt_id = "20260829T120000Z-42-bbbbbbbbbbbb"
    receipt = {
        "base_config_sha256": "a" * 64,
        "candidate_config_sha256": "b" * 64,
        "base_service_sha256": "c" * 64,
        "candidate_service_sha256": "d" * 64,
        "smart_dns_release_sha256": "e" * 64,
        "node_code": "ru",
        "state": "applied",
        "backup_config_valid": True,
    }
    preflight = _ready_preflight(
        base_sha256=str(receipt["candidate_config_sha256"]),
        base_service_sha256=str(receipt["candidate_service_sha256"]),
        release_sha256=str(receipt["smart_dns_release_sha256"]),
    )
    preflight["smart_dns_route_present"] = True
    known_hosts = tmp_path / "known_hosts"
    known_hosts.write_text("safe fixture\n", encoding="utf-8")
    report_path = tmp_path / "rollback-plan.json"

    monkeypatch.setattr(MODULE, "_connect_owned", lambda **_kwargs: (FakeSSH(), "key"))
    monkeypatch.setattr(MODULE, "_resolve_node_host", lambda *_args: "node.invalid")
    monkeypatch.setattr(MODULE, "_remote_preflight", lambda *_args: preflight)
    monkeypatch.setattr(MODULE, "_remote_receipt_preflight", lambda *_args: receipt)
    monkeypatch.setattr(MODULE, "POLICY_PATH", tmp_path / "missing-policy.json")
    monkeypatch.setattr(
        MODULE,
        "_runtime_transform",
        lambda *_args, **_kwargs: pytest.fail("rollback must not rebuild a candidate"),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--brain-host",
            "brain.invalid",
            "--node-code",
            "ru",
            "--known-hosts",
            str(known_hosts),
            "--base-config",
            str(tmp_path / "missing-base.cfg"),
            "--base-service",
            str(tmp_path / "missing-base.service"),
            "--operation",
            "rollback",
            "--receipt-id",
            receipt_id,
            "--json-out",
            str(report_path),
        ],
    )

    assert MODULE.main() == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["repository_fixtures_loaded"] is False


def test_candidate_service_has_validate_then_signal_reload_contract() -> None:
    candidate = MODULE._canonical_text(MODULE.CANDIDATE_SERVICE)
    MODULE._validate_candidate_service(candidate)
    text = candidate.decode("utf-8")

    assert text.index("ExecReload=/usr/sbin/haproxy -c") < text.index(
        "ExecReload=/bin/kill -USR2 $MAINPID"
    )
    assert "KillMode=mixed" in text


def test_offline_plan_writes_candidate_outside_repo_without_returning_hostname(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate = tmp_path / "candidate.cfg"
    report_path = tmp_path / "plan.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--offline",
            "--doh-hostname",
            "dns.pokrov.space",
            "--candidate-config-out",
            str(candidate),
            "--json-out",
            str(report_path),
        ],
    )

    assert MODULE.main() == 0
    printed = capsys.readouterr().out
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert candidate.is_file()
    assert report["mode"] == "OFFLINE_PLAN"
    assert report["target_selected"] is False
    assert report["mutation_performed"] is False
    assert report["candidate_config_valid"] == "NOT_RUN_REMOTE_HAPROXY"
    assert "dns.pokrov.space" not in printed
    assert "dns.pokrov.space" not in json.dumps(report)


def test_candidate_output_inside_repository_is_forbidden() -> None:
    with pytest.raises(
        MODULE.SmartDNSFrontendMigrationError,
        match="candidate_config_output_must_be_outside_repository",
    ):
        MODULE._write_candidate_config(b"safe\n", REPO_ROOT / "forbidden.cfg")


def test_plan_actions_keep_validation_apply_and_rollback_order_explicit() -> None:
    install = MODULE._plan_actions("install")
    rollback = MODULE._plan_actions("rollback")

    assert install.index("retain_root_only_pre_mutation_frontend_receipt") < install.index(
        "atomically_replace_and_reload_frontend_config"
    )
    assert install[-1] == "automatically_restore_receipt_on_failed_apply"
    assert rollback[0] == "verify_exact_receipt_base_candidate_backend_release_and_node"
    assert rollback[-1] == "retain_smart_dns_release_and_receipt_evidence"
