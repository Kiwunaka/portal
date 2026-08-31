from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT_PATH = SCRIPTS / "remote_install_owned_smart_dns_lab.py"
SPEC = importlib.util.spec_from_file_location(
    "remote_install_owned_smart_dns_lab", SCRIPT_PATH
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BUNDLE = MODULE.bundle_contract


def _synthetic_bundle(tmp_path: Path) -> Path:
    provenance = {
        "repository": "Kiwunaka/portal",
        "revision": "a" * 40,
        "source_epoch": 1,
        "source_time_utc": "1970-01-01T00:00:01Z",
        "go_toolchain": BUNDLE.EXPECTED_GO_VERSION,
        "module_dependencies": ["synthetic fixture"],
    }
    manifest, members = BUNDLE._manifest(
        binary=b"\x7fELF" + b"0" * 1_100_000,
        provenance=provenance,
    )
    destination = tmp_path / "smart-dns.zip"
    BUNDLE._write_bundle(destination, manifest, members)
    return destination


def test_local_bundle_is_exact_and_derives_receipt_bound_paths(tmp_path: Path) -> None:
    path, manifest, contents, digest = MODULE._validated_local_bundle(
        _synthetic_bundle(tmp_path)
    )

    assert path.is_file()
    assert len(digest) == 64
    assert manifest["created_from"]["revision"] == "a" * 40
    assert BUNDLE.BINARY_MEMBER in contents
    assert f"{MODULE.RELEASE_ROOT}/{digest}".endswith(digest)
    assert f"{MODULE.RUNTIME_STAGE_ROOT}/{digest}".endswith(digest)

    for listener_mode in MODULE.LISTENER_MODES:
        _path, _manifest, _contents, mode_digest = MODULE._validated_local_bundle(
            path, listener_mode
        )
        assert mode_digest == digest


def test_canonical_node_codes_are_safe_components() -> None:
    assert MODULE._safe_component("RU_SPB", label="node_code") == "ru_spb"
    assert MODULE._safe_component("dns-lab", label="node_code") == "dns-lab"

    for value in ("../ru", "ru spb", "ru'spb", "-ru", "ru/spb"):
        with pytest.raises(MODULE.SmartDNSRemoteOperationError, match="node_code_invalid"):
            MODULE._safe_component(value, label="node_code")


def test_plan_probe_is_read_only_and_never_returns_runtime_material() -> None:
    command = MODULE._preflight_command(
        release_dir=f"{MODULE.RELEASE_ROOT}/{'a' * 64}",
        runtime_material_dir=f"{MODULE.RUNTIME_STAGE_ROOT}/{'a' * 64}",
        expected_proxy_ipv4="1.1.1.1",
    )

    prohibited = (
        "mkdir",
        "install -",
        "systemctl start",
        "systemctl enable",
        "ufw allow",
        "rm -",
    )
    assert not any(token in command for token in prohibited)
    assert "ss -H -ltn" in command
    assert "python3 -c" in command
    assert "1.1.1.1" in command
    assert "runtime_placeholders_absent" in command
    assert "runtime_contract_valid" in command
    assert "python3" in command
    assert "cat " not in command

    fronted = MODULE._preflight_command(
        release_dir=f"{MODULE.RELEASE_ROOT}/{'a' * 64}",
        runtime_material_dir=f"{MODULE.RUNTIME_STAGE_ROOT}/{'a' * 64}",
        expected_proxy_ipv4="1.1.1.1",
        listener_mode=MODULE.FRONTED_LISTENER_MODE,
    )
    assert "sport = :18443" in fronted
    assert "ufw allow" not in fronted
    assert "systemctl start" not in fronted


def _runtime_config(listener_mode: str) -> dict[str, object]:
    template_name = (
        "config.fronted.template.json"
        if listener_mode == MODULE.FRONTED_LISTENER_MODE
        else "config.template.json"
    )
    config = json.loads(
        (ROOT / "infra" / "owned-smart-dns" / template_name).read_text(
            encoding="utf-8"
        )
    )
    rendered = json.dumps(config)
    rendered = rendered.replace("${POKROV_SMART_DNS_DOH_HOSTNAME}", "dns.example.com")
    rendered = rendered.replace("${POKROV_SMART_DNS_PROXY_IPV4}", "1.1.1.1")
    rendered = rendered.replace("${POKROV_SMART_DNS_UPSTREAM_DOT_IP}", "8.8.8.8")
    rendered = rendered.replace(
        "${POKROV_SMART_DNS_UPSTREAM_DOT_SERVER_NAME}", "dns.google"
    )
    return json.loads(rendered)


def _run_runtime_contract(command: str) -> subprocess.CompletedProcess[str]:
    parts = shlex.split(command)
    assert parts[0] == "python3"
    return subprocess.run(
        [sys.executable, *parts[1:]],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_fronted_runtime_contract_requires_exact_loopback_proxy_v2(
    tmp_path: Path,
) -> None:
    config = _runtime_config(MODULE.FRONTED_LISTENER_MODE)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    command = MODULE._runtime_contract_check(
        str(path), "1.1.1.1", MODULE.FRONTED_LISTENER_MODE
    )
    assert _run_runtime_contract(command).returncode == 0

    config["listen"] = "0.0.0.0:443"
    path.write_text(json.dumps(config), encoding="utf-8")
    assert _run_runtime_contract(command).returncode != 0


def test_dedicated_runtime_contract_accepts_public_443_without_proxy_v2(
    tmp_path: Path,
) -> None:
    config = _runtime_config(MODULE.DEDICATED_LISTENER_MODE)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    command = MODULE._runtime_contract_check(
        str(path), "1.1.1.1", MODULE.DEDICATED_LISTENER_MODE
    )

    assert _run_runtime_contract(command).returncode == 0

    config["listen"] = "127.0.0.1:18443"
    config["accept_proxy_protocol_v2"] = True
    path.write_text(json.dumps(config), encoding="utf-8")
    assert _run_runtime_contract(command).returncode != 0

    config["listen"] = "127.0.0.1:18443"
    config["accept_proxy_protocol_v2"] = False
    path.write_text(json.dumps(config), encoding="utf-8")
    assert _run_runtime_contract(command).returncode != 0


def test_address_availability_helper_returns_only_sanitized_facts() -> None:
    helper = MODULE._ADDRESS_AVAILABILITY_HELPER

    assert 'run("ip", "-j", "-4", "addr", "show", "scope", "global")' in helper
    assert 'run("ss", "-H", "-ltn", "sport = :443")' in helper
    assert 'run("ss", "-H", "-ltn4", "sport = :443")' in helper
    assert "unclaimed_global_ipv4=" in helper
    assert "print(expected" not in helper
    assert "print(candidate" not in helper
    assert "print(address" not in helper

    with pytest.raises(
        MODULE.SmartDNSRemoteOperationError,
        match="expected_proxy_ipv4_not_public",
    ):
        MODULE._address_availability_command("192.0.2.1")


def test_apply_commands_are_digest_bound_secret_safe_and_rollback_armed(
    tmp_path: Path,
) -> None:
    _path, manifest, _contents, digest = MODULE._validated_local_bundle(
        _synthetic_bundle(tmp_path)
    )
    receipt_id = "20260828T120000Z-7-" + digest[:12]
    backup = f"{MODULE.BACKUP_ROOT}/{receipt_id}"
    stage = f"{MODULE.STAGE_ROOT}/{receipt_id}"
    release = f"{MODULE.RELEASE_ROOT}/{digest}"
    runtime = f"{MODULE.RUNTIME_STAGE_ROOT}/{digest}"

    install = MODULE._install_command(
        stage_dir=stage,
        release_dir=release,
        runtime_material_dir=runtime,
        backup_dir=backup,
        manifest=manifest,
    )
    rollback = MODULE._rollback_command(
        backup_dir=backup,
        bundle_sha256=digest,
        node_code="dns-lab",
        release_dir=release,
        require_current_release=True,
    )

    assert "systemctl start pokrov-smart-dns-lab.service" in install
    assert install.index("systemctl start") < install.index("ufw allow 443/tcp")
    assert install.index("ufw allow 443/tcp") < install.index("systemctl enable")
    assert "runuser -u pokrov-smart-dns" in install
    assert "https://$doh_host/dns-query" in install
    assert "${POKROV_" not in install
    assert "privkey.pem" in install
    assert "printf 'applied\\n'" in install
    assert "installed" not in install
    assert "disable --now pokrov-smart-dns-lab.service" in rollback
    assert "ufw --force delete allow 443/tcp" in rollback
    assert rollback.index("listener_after_stop=free") < rollback.index("rm -f")
    assert rollback.rindex("listener_after_stop") > rollback.index("rm -f")
    assert digest in rollback
    assert "readlink -f /opt/pokrov/smart-dns/current" in rollback
    assert "grep -qx applied" in rollback
    assert "rm -rf" not in rollback
    assert f"test -d {release}" in rollback

    automatic = MODULE._rollback_command(
        backup_dir=backup,
        bundle_sha256=digest,
        node_code="dns-lab",
        release_dir=release,
        require_current_release=False,
    )
    assert "prepared|applied" in automatic
    assert "grep -qx applied" not in automatic


def test_fronted_apply_and_rollback_are_loopback_only_and_firewall_neutral(
    tmp_path: Path,
) -> None:
    _path, manifest, _contents, digest = MODULE._validated_local_bundle(
        _synthetic_bundle(tmp_path), MODULE.FRONTED_LISTENER_MODE
    )
    receipt_id = "20260828T120000Z-7-" + digest[:12]
    backup = f"{MODULE.BACKUP_ROOT}/{receipt_id}"
    stage = f"{MODULE.STAGE_ROOT}/{receipt_id}"
    release = f"{MODULE.RELEASE_ROOT}/{digest}"
    runtime = f"{MODULE.RUNTIME_STAGE_ROOT}/{digest}"

    receipt = MODULE._backup_command(
        backup_dir=backup,
        bundle_sha256=digest,
        node_code="dns-lab",
        listener_mode=MODULE.FRONTED_LISTENER_MODE,
    )
    install = MODULE._install_command(
        stage_dir=stage,
        release_dir=release,
        runtime_material_dir=runtime,
        backup_dir=backup,
        manifest=manifest,
        listener_mode=MODULE.FRONTED_LISTENER_MODE,
    )
    rollback = MODULE._rollback_command(
        backup_dir=backup,
        bundle_sha256=digest,
        node_code="dns-lab",
        release_dir=release,
        require_current_release=True,
        listener_mode=MODULE.FRONTED_LISTENER_MODE,
    )

    assert "not_managed" in receipt
    assert "ufw status" not in receipt
    assert "listener-mode" in receipt
    assert "sport = :18443" in install
    assert "127.0.0.1:18443" in install
    assert "ufw allow" not in install
    assert "ufw --force" not in rollback
    assert "sport = :18443" in rollback
    assert "listener-mode" in rollback
    assert "PROXY" not in install
    assert "python3 -c" in install
    assert "192.0.2.10" in MODULE._FRONTED_DOH_PROBE_HELPER
    assert "HTTP/1.1 400" in MODULE._FRONTED_DOH_PROBE_HELPER
    assert "install-step" in install
    assert "listener_check_1_failed" in install
    assert "listener_check_2_failed" in install
    assert "listener_check_3_failed" in install
    assert "listener_attempt" in install
    assert "sleep 0.2" in install
    assert "-lt 50" in install
    assert "local_probe_passed" in install
    assert "final_readback_passed" in install


def test_retained_release_reuse_requires_exact_immutable_member_contract(
    tmp_path: Path,
) -> None:
    _path, manifest, _contents, digest = MODULE._validated_local_bundle(
        _synthetic_bundle(tmp_path), MODULE.FRONTED_LISTENER_MODE
    )
    release = f"{MODULE.RELEASE_ROOT}/{digest}"
    command = MODULE._retained_release_verification_command(
        release_dir=release, manifest=manifest
    )

    assert "sha256sum" in command
    assert "stat -c %s" in command
    assert "stat -c %a" in command
    assert "! -type d ! -type f" in command
    assert not any(line.startswith("rm ") for line in command.splitlines())
    for member, record in manifest["members"].items():
        assert f"{release}/{member}" in command
        assert record["sha256"] in command


def test_fresh_install_rejects_port_path_firewall_or_material_conflicts() -> None:
    ready = {
        "root": True,
        "required_tools": True,
        "ufw_installed": True,
        "ufw_active": True,
        "ufw_rule_present": False,
        "tcp_443": "free",
        "occupied_targets": [],
        "service_state": "inactive",
        "runtime_material_ready": True,
    }
    MODULE._assert_fresh_install_preflight(ready)

    cases = (
        {"tcp_443": "busy"},
        {"occupied_targets": ["unit"]},
        {"ufw_rule_present": True},
        {"runtime_material_ready": False},
        {"ufw_active": False},
    )
    for override in cases:
        with pytest.raises(MODULE.SmartDNSRemoteOperationError):
            MODULE._assert_fresh_install_preflight({**ready, **override})


def test_fronted_fresh_install_ignores_public_443_and_ufw_but_requires_loopback() -> None:
    ready = {
        "root": True,
        "required_tools": True,
        "ufw_installed": False,
        "ufw_active": False,
        "ufw_rule_present": True,
        "tcp_443": "busy",
        "loopback_tcp_18443": "free",
        "occupied_targets": [],
        "service_state": "inactive",
        "runtime_material_ready": True,
    }
    MODULE._assert_fresh_install_preflight(ready, MODULE.FRONTED_LISTENER_MODE)

    retained = {**ready, "occupied_targets": ["release"]}
    with pytest.raises(
        MODULE.SmartDNSRemoteOperationError,
        match="install_target_already_present",
    ):
        MODULE._assert_fresh_install_preflight(
            retained, MODULE.FRONTED_LISTENER_MODE
        )
    MODULE._assert_fresh_install_preflight(
        retained,
        MODULE.FRONTED_LISTENER_MODE,
        allow_retained_exact_release=True,
    )

    with pytest.raises(
        MODULE.SmartDNSRemoteOperationError,
        match="fronted_loopback_listener_occupied",
    ):
        MODULE._assert_fresh_install_preflight(
            {**ready, "loopback_tcp_18443": "busy"},
            MODULE.FRONTED_LISTENER_MODE,
        )


def test_probe_parser_rejects_unbounded_remote_output() -> None:
    assert MODULE._parse_probe("root=yes\ntcp_busy=no") == {
        "root": "yes",
        "tcp_busy": "no",
    }
    with pytest.raises(MODULE.SmartDNSRemoteOperationError):
        MODULE._parse_probe("host=198.51.100.1/path")

    assert MODULE._parse_probe("unclaimed_global_ipv4=one") == {
        "unclaimed_global_ipv4": "one"
    }


def test_tcp_443_bind_scope_is_sanitized_and_fail_closed() -> None:
    assert MODULE._tcp_443_bind_scope(
        {
            "tcp_busy": "no",
            "tcp_wildcard_busy": "no",
            "tcp_expected_ipv4_busy": "no",
        }
    ) == "free"
    assert MODULE._tcp_443_bind_scope(
        {
            "tcp_busy": "yes",
            "tcp_wildcard_busy": "yes",
            "tcp_expected_ipv4_busy": "no",
        }
    ) == "wildcard"
    assert MODULE._tcp_443_bind_scope(
        {
            "tcp_busy": "yes",
            "tcp_wildcard_busy": "no",
            "tcp_expected_ipv4_busy": "yes",
        }
    ) == "expected_address"
    assert MODULE._tcp_443_bind_scope(
        {
            "tcp_busy": "yes",
            "tcp_wildcard_busy": "no",
            "tcp_expected_ipv4_busy": "no",
        }
    ) == "other_address_only"
    with pytest.raises(
        MODULE.SmartDNSRemoteOperationError,
        match="remote_preflight_tcp_scope_invalid",
    ):
        MODULE._tcp_443_bind_scope(
            {
                "tcp_busy": "no",
                "tcp_wildcard_busy": "yes",
                "tcp_expected_ipv4_busy": "no",
            }
        )


def test_address_reuse_followup_never_authorizes_apply() -> None:
    assert MODULE._address_reuse_followup(
        bind_scope="other_address_only", expected_ipv4_assigned=True
    ) == "POTENTIAL_REQUIRES_SEPARATE_ADDRESS_SPECIFIC_GUARD"
    assert MODULE._address_reuse_followup(
        bind_scope="expected_address", expected_ipv4_assigned=True
    ) == "BLOCKED_CURRENT_BIND_SCOPE"
    assert MODULE._address_reuse_followup(
        bind_scope="free", expected_ipv4_assigned=False
    ) == "BLOCKED_EXPECTED_IPV4_NOT_ASSIGNED"


def test_public_ipv4_resolution_is_unique_and_global(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        MODULE.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (MODULE.socket.AF_INET, 1, 6, "", ("1.1.1.1", 0)),
            (MODULE.socket.AF_INET, 1, 6, "", ("1.1.1.1", 0)),
        ],
    )
    assert MODULE._resolve_unique_public_ipv4("owned.invalid") == "1.1.1.1"

    monkeypatch.setattr(
        MODULE.socket,
        "getaddrinfo",
        lambda *_args, **_kwargs: [
            (MODULE.socket.AF_INET, 1, 6, "", ("10.0.0.1", 0))
        ],
    )
    with pytest.raises(MODULE.SmartDNSRemoteOperationError):
        MODULE._resolve_unique_public_ipv4("owned.invalid")


def test_plan_and_report_contract_return_no_endpoint_or_runtime_secrets(
    tmp_path: Path,
) -> None:
    bundle_path = _synthetic_bundle(tmp_path)
    _path, manifest, _contents, digest = MODULE._validated_local_bundle(bundle_path)
    report = {
        "schema_version": MODULE.REPORT_SCHEMA,
        "mode": "PLAN",
        "operation": "install",
        "node_code": "dns-lab",
        "bundle_sha256": digest,
        "source_revision": manifest["created_from"]["revision"],
        "plan": MODULE._plan(operation="install", node_code="dns-lab"),
        "raw_host_returned": False,
        "raw_runtime_material_returned": False,
    }
    serialized = json.dumps(report, sort_keys=True)

    assert "endpoint" not in serialized
    assert "private_key" not in serialized
    assert "password" not in serialized
    assert "doh_hostname" not in serialized
    assert "proxy_ipv4" not in serialized


def test_fronted_plan_is_explicit_and_keeps_frontend_separate() -> None:
    plan = MODULE._plan(
        operation="install",
        node_code="dns-lab",
        listener_mode=MODULE.FRONTED_LISTENER_MODE,
    )

    assert plan["listener_mode"] == MODULE.FRONTED_LISTENER_MODE
    assert "retain_loopback_only_firewall_unchanged_then_enable_service" in plan[
        "ordered_actions"
    ]
    assert "start_and_verify_proxy_v2_tls_doh_before_frontend_migration" in plan[
        "ordered_actions"
    ]
    assert "open_tcp_443_then_enable_service" not in plan["ordered_actions"]
