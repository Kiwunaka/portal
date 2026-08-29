from __future__ import annotations

import importlib.util
import json
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
    assert "runtime_placeholders_absent" in command
    assert "runtime_contract_valid" in command
    assert "python3" in command
    assert "cat " not in command


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
    assert "disable --now pokrov-smart-dns-lab.service" in rollback
    assert "ufw --force delete allow 443/tcp" in rollback
    assert rollback.index("listener_after_stop=free") < rollback.index("rm -f")
    assert rollback.rindex("listener_after_stop") > rollback.index("rm -f")
    assert digest in rollback
    assert "readlink -f /opt/pokrov/smart-dns/current" in rollback
    assert "rm -rf" not in rollback
    assert f"test -d {release}" in rollback


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


def test_probe_parser_rejects_unbounded_remote_output() -> None:
    assert MODULE._parse_probe("root=yes\ntcp_busy=no") == {
        "root": "yes",
        "tcp_busy": "no",
    }
    with pytest.raises(MODULE.SmartDNSRemoteOperationError):
        MODULE._parse_probe("host=198.51.100.1/path")


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
