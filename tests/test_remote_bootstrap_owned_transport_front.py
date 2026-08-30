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
SCRIPT = SCRIPTS / "remote_bootstrap_owned_transport_front.py"
SPEC = importlib.util.spec_from_file_location("remote_bootstrap_owned_transport_front", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _direct_probe() -> dict[str, object]:
    return {
        "effective_uid_root": True,
        "systemd_present": True,
        "python3_present": True,
        "sqlite3_module_present": True,
        "apt_present": True,
        "haproxy_present": False,
        "haproxy_package_candidate": True,
        "xui_state": "active",
        "xui_enabled": "enabled",
        "frontend_state": "inactive",
        "frontend_enabled": "not-found",
        "default_haproxy_state": "inactive",
        "default_haproxy_enabled": "not-found",
        "config_present": False,
        "config_sha256": "missing",
        "service_present": False,
        "service_sha256": "missing",
        "xui_db_present": True,
        "inbound_found": True,
        "inbound_unique": True,
        "inbound_protocol_vless": True,
        "inbound_enabled": True,
        "inbound_listen_state": "wildcard_empty",
        "inbound_port": 443,
        "inbound_reality": True,
        "inbound_invariant_sha256": "e" * 64,
        "enabled_public_443_inbound_count": 1,
        "public_443_listening": True,
        "backend_10443_listening": False,
        "smart_dns_18443_listening": False,
        "public_443_owned_by_xray": True,
        "backend_10443_owned_by_xray": False,
        "frontend_config_valid": False,
        "expected_state": "direct",
    }


def _fronted_probe(config_sha256: str, service_sha256: str) -> dict[str, object]:
    result = _direct_probe()
    result.update(
        {
            "haproxy_present": True,
            "frontend_state": "active",
            "frontend_enabled": "enabled",
            "default_haproxy_enabled": "masked",
            "config_present": True,
            "config_sha256": config_sha256,
            "service_present": True,
            "service_sha256": service_sha256,
            "inbound_listen_state": "loopback_v4",
            "inbound_port": 10443,
            "enabled_public_443_inbound_count": 0,
            "backend_10443_listening": True,
            "public_443_owned_by_xray": False,
            "backend_10443_owned_by_xray": True,
            "frontend_config_valid": True,
            "expected_state": "fronted",
        }
    )
    return result


def test_canonical_legacy_config_is_one_loopback_backend_and_no_smart_dns() -> None:
    config = MODULE._canonical_text(MODULE.CONFIG_SOURCE)
    service = MODULE._canonical_text(MODULE.SERVICE_SOURCE)
    MODULE._validate_sources(config, service)
    text = config.decode("utf-8")

    assert text.count("bind :443") == 1
    assert text.count("server legacy_reality_fallback 127.0.0.1:10443 check") == 1
    assert text.count("\n    server ") == 1
    assert "smart_dns" not in text.lower()
    assert ":18443" not in text


def test_legacy_config_is_accepted_as_smart_dns_migration_base() -> None:
    from remote_migrate_owned_smart_dns_frontend import build_candidate_config

    candidate, metadata = build_candidate_config(
        base_config=MODULE._canonical_text(MODULE.CONFIG_SOURCE),
        doh_hostname="dns.pokrov.space",
    )

    assert metadata["proxy_protocol"] == "v2"
    assert b"server smart_dns 127.0.0.1:18443 check send-proxy-v2" in candidate
    assert candidate.index(b"use_backend be_smart_dns") < candidate.index(
        b"default_backend be_legacy_reality_fallback"
    )


def test_remote_probe_is_read_only_and_sanitized() -> None:
    source = MODULE._REMOTE_PROBE

    for prohibited in (
        "apt-get install",
        "apt-get remove",
        "systemctl restart",
        "systemctl enable",
        "systemctl disable",
        "update inbounds",
        "delete from",
        "insert into",
        "rm -",
        "install -",
    ):
        assert prohibited not in source.lower()
    assert "mode=ro" in source
    assert "select id,listen,port,protocol,enable,stream_settings" in source.lower()
    assert "print(json.dumps(result" in source
    assert "stream_settings" not in source.split("result = {", 1)[1].split("}", 1)[0]


def test_direct_preflight_requires_exact_single_reality_inbound_and_free_ports() -> None:
    MODULE._assert_direct_preflight(_direct_probe())

    for override in (
        {"inbound_reality": False},
        {"enabled_public_443_inbound_count": 2},
        {"inbound_listen_state": "other"},
        {"backend_10443_listening": True},
        {"smart_dns_18443_listening": True},
        {"public_443_owned_by_xray": False},
        {"config_present": True},
        {"default_haproxy_state": "active"},
    ):
        probe = _direct_probe()
        probe.update(override)
        with pytest.raises(MODULE.TransportFrontBootstrapError):
            MODULE._assert_direct_preflight(probe)


def test_fronted_preflight_is_digest_and_listener_bound() -> None:
    config_sha256 = "a" * 64
    service_sha256 = "b" * 64
    MODULE._assert_fronted_preflight(
        _fronted_probe(config_sha256, service_sha256),
        config_sha256=config_sha256,
        service_sha256=service_sha256,
    )

    for override in (
        {"config_sha256": "c" * 64},
        {"service_sha256": "d" * 64},
        {"backend_10443_owned_by_xray": False},
        {"frontend_config_valid": False},
        {"frontend_state": "inactive"},
        {"inbound_port": 443},
    ):
        probe = _fronted_probe(config_sha256, service_sha256)
        probe.update(override)
        with pytest.raises(MODULE.TransportFrontBootstrapError):
            MODULE._assert_fronted_preflight(
                probe,
                config_sha256=config_sha256,
                service_sha256=service_sha256,
            )


def test_apply_command_arms_trap_uses_sql_cas_and_verifies_owners() -> None:
    command = MODULE._apply_command(
        inbound_id=1,
        stage_config="/root/pokrov-transport-front-bootstrap/id/candidate.cfg",
        stage_service="/root/pokrov-transport-front-bootstrap/id/candidate.service",
        receipt_path="/root/pokrov-transport-front-bootstrap/id/receipt.json",
        config_sha256="a" * 64,
        service_sha256="b" * 64,
        inbound_invariant_sha256="e" * 64,
        haproxy_was_present=False,
    )

    assert command.index("trap rollback EXIT") < command.index("apt-get install")
    assert command.index("apt-get install") < command.rindex("systemctl restart x-ui.service")
    assert "wait_listener_owner x-ui.service 10443 xray" in command
    assert "wait_listener_owner portal-transport-front.service 443 haproxy" in command
    assert "wait_listener_owner x-ui.service 443 xray || rollback_ok=no" in command
    assert "if test \"$front_files\" = yes; then systemctl disable --now portal-transport-front.service" in command
    assert "update inbounds set listen=?,port=?" not in command
    decoded_helper = MODULE._SQL_CAS_HELPER
    assert "coalesce(listen,'')='' and port=?" in decoded_helper
    assert "listen=? and port=?" in decoded_helper
    assert "cur.rowcount != 1" in decoded_helper
    assert "expected_invariant" in decoded_helper
    assert 'grep -qi "$wait_owner"' in command
    assert "automatic_rollback_pass" in command
    assert "automatic_rollback_fail" in command
    assert "rollback_ok=yes" in command
    assert "exit 97" in command
    assert "rm -f -- /etc/portal-transport-front.cfg" in command


def test_apply_does_not_remove_preexisting_haproxy_on_rollback() -> None:
    command = MODULE._apply_command(
        inbound_id=1,
        stage_config="/root/x/candidate.cfg",
        stage_service="/root/x/candidate.service",
        receipt_path="/root/x/receipt.json",
        config_sha256="a" * 64,
        service_sha256="b" * 64,
        inbound_invariant_sha256="e" * 64,
        haproxy_was_present=True,
    )

    assert "installed=no" in command
    assert 'if test "$installed" = yes; then systemctl disable --now haproxy.service' in command
    assert "apt-get purge -y haproxy" in command


def test_receipt_contains_only_safe_digest_bound_rollback_state() -> None:
    raw = MODULE._receipt_payload(
        receipt_id="20260830T010203Z-123-aaaaaaaaaaaa",
        node_code="it",
        inbound_id=1,
        config_sha256="a" * 64,
        service_sha256="b" * 64,
        inbound_invariant_sha256="e" * 64,
        haproxy_was_present=False,
    )
    payload = json.loads(raw)

    assert payload == {
        "schema_version": MODULE.REPORT_SCHEMA,
        "receipt_id": "20260830T010203Z-123-aaaaaaaaaaaa",
        "node_code": "it",
        "inbound_id": 1,
        "from_listen": "wildcard_empty",
        "from_port": 443,
        "to_listen": "127.0.0.1",
        "to_port": 10443,
        "config_sha256": "a" * 64,
        "service_sha256": "b" * 64,
        "inbound_invariant_sha256": "e" * 64,
        "haproxy_was_present": False,
        "state": "armed",
    }
    assert "host" not in payload
    assert "password" not in payload
    assert "private" not in payload


def test_remote_stage_write_is_exclusive_and_writable_with_paramiko() -> None:
    class Handle:
        def __init__(self) -> None:
            self.pipelined = False
            self.content = b""
            self.flushed = False

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def set_pipelined(self, value: bool) -> None:
            self.pipelined = value

        def write(self, value: bytes) -> None:
            self.content += value

        def flush(self) -> None:
            self.flushed = True

    class SFTP:
        def __init__(self) -> None:
            self.handle = Handle()
            self.opened = None
            self.chmod_call = None
            self.closed = False

        def file(self, path: str, mode: str):
            self.opened = (path, mode)
            return self.handle

        def chmod(self, path: str, mode: int) -> None:
            self.chmod_call = (path, mode)

        def close(self) -> None:
            self.closed = True

    class SSH:
        def __init__(self, sftp: SFTP) -> None:
            self.sftp = sftp

        def open_sftp(self) -> SFTP:
            return self.sftp

    sftp = SFTP()
    MODULE._remote_write(SSH(sftp), "/root/stage", b"payload", 0o600)

    assert sftp.opened == ("/root/stage", "x+b")
    assert sftp.handle.pipelined is True
    assert sftp.handle.content == b"payload"
    assert sftp.handle.flushed is True
    assert sftp.chmod_call == ("/root/stage", 0o600)
    assert sftp.closed is True


def test_rollback_purges_package_only_when_receipt_owns_it() -> None:
    retained = MODULE._rollback_command(
        inbound_id=1,
        receipt_path="/root/x/receipt.json",
        inbound_invariant_sha256="e" * 64,
        remove_haproxy=False,
    )
    owned = MODULE._rollback_command(
        inbound_id=1,
        receipt_path="/root/x/receipt.json",
        inbound_invariant_sha256="e" * 64,
        remove_haproxy=True,
    )

    assert "apt-get purge" not in retained
    assert "apt-get purge -y haproxy" in owned
    assert owned.index("direct_db=yes") < owned.index("disable --now")
    assert owned.index("disable --now") < owned.rindex("systemctl restart x-ui.service")
    assert "wait_listener_owner x-ui.service 443 xray" in owned
    assert "wait_listener_owner portal-transport-front.service 443 haproxy" in owned
    assert "rollback_failed_front_restored" in owned
    assert "rollback_failed_unknown" in owned
    assert "rolled_back_cleanup_pending" in owned
    assert "rolled_back" in owned
