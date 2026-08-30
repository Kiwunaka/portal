from __future__ import annotations

import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "remote_prepare_owned_smart_dns_runtime.py"
SPEC = importlib.util.spec_from_file_location("remote_prepare_owned_smart_dns_runtime", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _ready() -> dict[str, bool]:
    return {
        "effective_uid_root": True,
        "apt_get_present": True,
        "python3_present": True,
        "openssl_present": True,
        "sha256sum_present": True,
        "install_present": True,
        "ss_present": True,
        "systemctl_present": True,
        "certbot_present": False,
        "ufw_present": True,
        "ufw_active": True,
        "ufw_tcp_80_rule_present": False,
        "tcp_80_free": True,
        "runtime_dir_present": False,
        "live_cert_present": False,
        "live_key_present": False,
        "renewal_hook_present": False,
        "smart_dns_service_present": False,
        "upstream_dot_reachable": True,
    }


def test_rendered_fronted_config_is_exact_and_passes_installer_contract(tmp_path: Path) -> None:
    template = (REPO_ROOT / "infra" / "owned-smart-dns" / "config.fronted.template.json").read_bytes()
    rendered = MODULE._render_config(
        template,
        doh_hostname="dns.pokrov.space",
        proxy_ipv4="1.1.1.1",
        upstream_dot_ip="8.8.8.8",
        upstream_dot_server_name="dns.google",
    )
    path = tmp_path / "config.json"
    path.write_bytes(rendered)
    command = MODULE.installer._runtime_contract_check(
        str(path), "1.1.1.1", MODULE.installer.FRONTED_LISTENER_MODE
    )

    parts = shlex.split(command)
    assert parts[0] == "python3"
    parts[0] = sys.executable
    result = subprocess.run(parts, check=False)
    assert result.returncode == 0
    payload = json.loads(rendered)
    assert payload["listen"] == "127.0.0.1:18443"
    assert payload["accept_proxy_protocol_v2"] is True
    assert payload["doh_hostname"] == "dns.pokrov.space"
    assert "POKROV_" not in rendered.decode("utf-8")


def test_preflight_is_read_only_sanitized_and_checks_required_boundaries() -> None:
    command = MODULE._preflight_command(
        runtime_dir="/root/pokrov-smart-dns-runtime-staging/" + "a" * 64,
        live_dir="/etc/letsencrypt/live/dns.pokrov.space",
        upstream_dot_ip="8.8.8.8",
        upstream_dot_server_name="dns.google",
    )
    for prohibited in (
        "apt-get update",
        "apt-get install",
        "certbot certonly",
        "ufw allow",
        "install -d",
        "rm -",
    ):
        assert prohibited not in command
    assert "tcp_80_free" in command
    assert "upstream_dot_reachable" in command
    assert "runtime_dir_present" in command
    assert "live_key_present" in command
    assert "cat " not in command


def test_apply_preflight_rejects_conflict_partial_material_or_missing_dot() -> None:
    MODULE._assert_apply_preflight(_ready())
    for override in (
        {"runtime_dir_present": True},
        {"renewal_hook_present": True},
        {"live_cert_present": True, "live_key_present": False},
        {"upstream_dot_reachable": False},
        {"tcp_80_free": False},
        {"smart_dns_service_present": True},
    ):
        with pytest.raises(MODULE.SmartDNSRuntimePreparationError):
            MODULE._assert_apply_preflight({**_ready(), **override})


def test_apply_command_keeps_private_key_on_server_and_binds_validation() -> None:
    command = MODULE._prepare_command(
        runtime_dir="/root/pokrov-smart-dns-runtime-staging/" + "a" * 64,
        live_dir="/etc/letsencrypt/live/dns.pokrov.space",
        doh_hostname="dns.pokrov.space",
        contact_email="support@pokrov.space",
        config_sha256="b" * 64,
        expected_proxy_ipv4="1.1.1.1",
        ufw_active=True,
        ufw_rule_present=False,
        certbot_present=False,
    )
    assert "certbot certonly --standalone" in command
    assert "ufw allow 80/tcp" in command
    assert "apt-get install -y certbot" in command
    assert "/etc/letsencrypt/live/dns.pokrov.space/privkey.pem" in command
    assert "openssl pkey" in command
    assert "runtime_contract" not in command
    assert "${EXPECTED_PROXY_IPV4}" not in command
    assert "1.1.1.1" not in command
    assert "scp " not in command
    assert "cat " not in command


def test_cleanup_is_targeted_and_preserves_acme_and_packages() -> None:
    runtime_dir = "/root/pokrov-smart-dns-runtime-staging/" + "a" * 64
    command = MODULE._cleanup_command(
        runtime_dir=runtime_dir,
        ufw_active=True,
        ufw_rule_present=False,
    )
    assert "rm -rf" not in command
    assert "apt-get remove" not in command
    assert "/etc/letsencrypt/live" not in command
    assert "ufw --force delete allow 80/tcp" in command
    assert runtime_dir in command


def test_domains_and_addresses_fail_closed() -> None:
    assert MODULE._domain("DNS.Pokrov.Space.", label="doh") == "dns.pokrov.space"
    assert MODULE._public_ipv4("1.1.1.1", label="upstream") == "1.1.1.1"
    with pytest.raises(MODULE.SmartDNSRuntimePreparationError):
        MODULE._domain("dns.pokrov.space\ninvalid", label="doh")
    with pytest.raises(MODULE.SmartDNSRuntimePreparationError):
        MODULE._public_ipv4("127.0.0.1", label="upstream")


def test_parser_rejects_duplicate_and_unbounded_probe_values() -> None:
    with pytest.raises(MODULE.SmartDNSRuntimePreparationError):
        MODULE._parse_probe("root=yes\nroot=no")
    with pytest.raises(MODULE.SmartDNSRuntimePreparationError):
        MODULE._parse_probe("root=contains whitespace")


def test_renewal_hook_only_updates_existing_installed_runtime() -> None:
    hook = MODULE._renewal_hook("dns.pokrov.space").decode("utf-8")
    assert "set -eu" in hook
    assert "if [ -f \"$dst/fullchain.pem\" ]" in hook
    assert "systemctl try-restart pokrov-smart-dns-lab.service" in hook
    assert "cat " not in hook
