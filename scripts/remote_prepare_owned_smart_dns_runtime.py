#!/usr/bin/env python3
"""Guarded PLAN/APPLY for server-side Smart DNS TLS runtime material."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import shlex
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    import remote_install_owned_smart_dns_lab as installer
    from node_access import DEFAULT_PASSWORDS, connect_node
except ImportError:  # pragma: no cover - package import for tests
    from . import remote_install_owned_smart_dns_lab as installer
    from .node_access import DEFAULT_PASSWORDS, connect_node


REPORT_SCHEMA = "pokrov-owned-smart-dns-runtime-preparation-v1"
BACKUP_ROOT = "/root/pokrov-smart-dns-runtime-prep-receipts"
RENEWAL_HOOK = "/etc/letsencrypt/renewal-hooks/deploy/pokrov-smart-dns"
SAFE_DOMAIN_RE = re.compile(
    r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
)


class SmartDNSRuntimePreparationError(RuntimeError):
    """Raised when server-side runtime preparation cannot prove its contract."""


def _q(value: str) -> str:
    return shlex.quote(str(value))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _domain(value: str, *, label: str) -> str:
    normalized = str(value or "").strip().lower().rstrip(".")
    if not SAFE_DOMAIN_RE.fullmatch(normalized):
        raise SmartDNSRuntimePreparationError(f"{label}_invalid")
    return normalized


def _public_ipv4(value: str, *, label: str) -> str:
    try:
        address = ipaddress.ip_address(str(value or "").strip())
    except ValueError as exc:
        raise SmartDNSRuntimePreparationError(f"{label}_invalid") from exc
    if address.version != 4 or not address.is_global:
        raise SmartDNSRuntimePreparationError(f"{label}_not_public_ipv4")
    return address.compressed


def _resolve_unique_public_ipv4(hostname: str) -> str:
    try:
        addresses = {
            _public_ipv4(item[4][0], label="resolved_address")
            for item in socket.getaddrinfo(hostname, None, socket.AF_INET)
        }
    except (OSError, SmartDNSRuntimePreparationError) as exc:
        raise SmartDNSRuntimePreparationError("doh_hostname_public_ipv4_unavailable") from exc
    if len(addresses) != 1:
        raise SmartDNSRuntimePreparationError("doh_hostname_public_ipv4_not_unique")
    return next(iter(addresses))


def _release_id(bundle_sha256: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{now}-{os.getpid()}-{bundle_sha256[:12]}"


def _render_config(
    template: bytes,
    *,
    doh_hostname: str,
    proxy_ipv4: str,
    upstream_dot_ip: str,
    upstream_dot_server_name: str,
) -> bytes:
    try:
        text = template.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SmartDNSRuntimePreparationError("runtime_template_utf8_invalid") from exc
    replacements = {
        "${POKROV_SMART_DNS_DOH_HOSTNAME}": doh_hostname,
        "${POKROV_SMART_DNS_PROXY_IPV4}": proxy_ipv4,
        "${POKROV_SMART_DNS_UPSTREAM_DOT_IP}": upstream_dot_ip,
        "${POKROV_SMART_DNS_UPSTREAM_DOT_SERVER_NAME}": upstream_dot_server_name,
    }
    for marker, replacement in replacements.items():
        if text.count(marker) != 1:
            raise SmartDNSRuntimePreparationError("runtime_template_placeholder_mismatch")
        text = text.replace(marker, replacement)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SmartDNSRuntimePreparationError("rendered_runtime_json_invalid") from exc
    if "POKROV_" in json.dumps(payload, sort_keys=True):
        raise SmartDNSRuntimePreparationError("rendered_runtime_placeholder_retained")
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _run(ssh: Any, command: str, *, label: str, timeout: int = 180) -> str:
    try:
        return installer._run(ssh, command, label=label, timeout=timeout)
    except Exception as exc:
        code = str(exc).split(":", 1)[0]
        raise SmartDNSRuntimePreparationError(code) from exc


def _connect_owned(*, code: str, host: str, passwords: Path) -> tuple[Any, str]:
    try:
        return connect_node(code=code, host=host, passwords_path=passwords)
    except Exception as exc:
        raise SmartDNSRuntimePreparationError(f"{code}_ssh_connect_failed") from exc


def _parse_probe(raw: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" not in line:
            raise SmartDNSRuntimePreparationError("remote_preflight_shape_invalid")
        key, value = line.split("=", 1)
        if (
            not re.fullmatch(r"[a-z0-9_]{1,64}", key)
            or not re.fullmatch(r"[A-Za-z0-9_.:-]{0,128}", value)
            or key in parsed
        ):
            raise SmartDNSRuntimePreparationError("remote_preflight_value_invalid")
        parsed[key] = value
    return parsed


def _preflight_command(
    *,
    runtime_dir: str,
    live_dir: str,
    upstream_dot_ip: str,
    upstream_dot_server_name: str,
) -> str:
    def emit(name: str, command: str) -> str:
        return f"emit_bool {name} {_q(command)}"

    return "\n".join(
        [
            "set -u",
            "emit_bool() { if sh -c \"$2\" >/dev/null 2>&1; then printf '%s=yes\\n' \"$1\"; else printf '%s=no\\n' \"$1\"; fi; }",
            emit("effective_uid_root", 'test "$(id -u)" = 0'),
            emit("apt_get_present", "command -v apt-get"),
            emit("python3_present", "command -v python3"),
            emit("openssl_present", "command -v openssl"),
            emit("sha256sum_present", "command -v sha256sum"),
            emit("install_present", "command -v install"),
            emit("ss_present", "command -v ss"),
            emit("systemctl_present", "command -v systemctl"),
            emit("certbot_present", "command -v certbot"),
            emit("ufw_present", "command -v ufw"),
            emit("ufw_active", "ufw status | grep -Fxq 'Status: active'"),
            emit(
                "ufw_tcp_80_rule_present",
                "ufw status | grep -Eq '(^|[[:space:]])80/tcp([[:space:]]|$)'",
            ),
            emit("tcp_80_free", "! ss -H -ltn 'sport = :80' | grep -q ."),
            emit("runtime_dir_present", f"test -e {_q(runtime_dir)}"),
            emit("live_cert_present", f"test -f {_q(live_dir + '/fullchain.pem')}"),
            emit("live_key_present", f"test -f {_q(live_dir + '/privkey.pem')}"),
            emit("renewal_hook_present", f"test -e {_q(RENEWAL_HOOK)}"),
            emit("smart_dns_service_present", f"test -e {_q(installer.SERVICE_PATH)}"),
            emit(
                "upstream_dot_reachable",
                "timeout 12 openssl s_client -connect "
                + _q(upstream_dot_ip + ":853")
                + " -servername "
                + _q(upstream_dot_server_name)
                + " -verify_hostname "
                + _q(upstream_dot_server_name)
                + " -brief </dev/null 2>&1 | grep -q 'Verification: OK'",
            ),
        ]
    )


def _remote_preflight(
    node: Any,
    *,
    runtime_dir: str,
    live_dir: str,
    upstream_dot_ip: str,
    upstream_dot_server_name: str,
) -> dict[str, bool]:
    raw = _run(
        node,
        _preflight_command(
            runtime_dir=runtime_dir,
            live_dir=live_dir,
            upstream_dot_ip=upstream_dot_ip,
            upstream_dot_server_name=upstream_dot_server_name,
        ),
        label="runtime_preflight",
        timeout=60,
    )
    values = _parse_probe(raw)
    expected = {
        "effective_uid_root",
        "apt_get_present",
        "python3_present",
        "openssl_present",
        "sha256sum_present",
        "install_present",
        "ss_present",
        "systemctl_present",
        "certbot_present",
        "ufw_present",
        "ufw_active",
        "ufw_tcp_80_rule_present",
        "tcp_80_free",
        "runtime_dir_present",
        "live_cert_present",
        "live_key_present",
        "renewal_hook_present",
        "smart_dns_service_present",
        "upstream_dot_reachable",
    }
    if set(values) != expected or any(value not in {"yes", "no"} for value in values.values()):
        raise SmartDNSRuntimePreparationError("remote_preflight_fields_invalid")
    return {key: value == "yes" for key, value in values.items()}


def _assert_apply_preflight(preflight: Mapping[str, bool]) -> None:
    required = (
        "effective_uid_root",
        "apt_get_present",
        "python3_present",
        "openssl_present",
        "sha256sum_present",
        "install_present",
        "ss_present",
        "systemctl_present",
        "ufw_present",
        "tcp_80_free",
        "upstream_dot_reachable",
    )
    if not all(preflight.get(key) for key in required):
        raise SmartDNSRuntimePreparationError("runtime_prepare_prerequisite_missing")
    if preflight.get("runtime_dir_present") or preflight.get("renewal_hook_present"):
        raise SmartDNSRuntimePreparationError("runtime_prepare_target_conflict")
    if preflight.get("live_cert_present") != preflight.get("live_key_present"):
        raise SmartDNSRuntimePreparationError("letsencrypt_material_partial")
    if preflight.get("smart_dns_service_present"):
        raise SmartDNSRuntimePreparationError("smart_dns_service_already_present")


def _receipt_command(
    *,
    receipt_dir: str,
    bundle_sha256: str,
    source_revision: str,
    node_code: str,
    certbot_present: bool,
    ufw_rule_present: bool,
    live_material_present: bool,
) -> str:
    fields = {
        "bundle_sha256": bundle_sha256,
        "source_revision": source_revision,
        "node_code": node_code,
        "certbot_present_before": "yes" if certbot_present else "no",
        "ufw_tcp_80_rule_present_before": "yes" if ufw_rule_present else "no",
        "live_material_present_before": "yes" if live_material_present else "no",
        "state": "preparing",
    }
    lines = [
        "set -e",
        f"test ! -e {_q(receipt_dir)}",
        f"install -d -o root -g root -m 0700 {_q(receipt_dir)}",
    ]
    for name, value in fields.items():
        lines.append(f"printf '%s\\n' {_q(value)} > {_q(receipt_dir + '/' + name)}")
    return "\n".join(lines)


def _renewal_hook(doh_hostname: str) -> bytes:
    live_dir = f"/etc/letsencrypt/live/{doh_hostname}"
    script = f"""#!/bin/sh
set -eu
src={_q(live_dir)}
dst={_q(installer.TLS_ROOT)}
if [ -f "$dst/fullchain.pem" ] && [ -f "$dst/privkey.pem" ] && getent group pokrov-smart-dns >/dev/null 2>&1; then
  install -o root -g pokrov-smart-dns -m 0644 "$src/fullchain.pem" "$dst/fullchain.pem"
  install -o root -g pokrov-smart-dns -m 0640 "$src/privkey.pem" "$dst/privkey.pem"
  systemctl try-restart {installer.SERVICE_NAME} >/dev/null
fi
"""
    return script.encode("utf-8")


def _prepare_command(
    *,
    runtime_dir: str,
    live_dir: str,
    doh_hostname: str,
    contact_email: str,
    config_sha256: str,
    expected_proxy_ipv4: str,
    ufw_active: bool,
    ufw_rule_present: bool,
    certbot_present: bool,
) -> str:
    lines = ["set -e"]
    if ufw_active and not ufw_rule_present:
        lines.append("ufw allow 80/tcp comment 'POKROV ACME HTTP-01' >/dev/null")
    if not certbot_present:
        lines.extend(
            [
                "DEBIAN_FRONTEND=noninteractive apt-get update >/dev/null",
                "DEBIAN_FRONTEND=noninteractive apt-get install -y certbot >/dev/null",
            ]
        )
    lines.extend(
        [
            "test \"$(command -v certbot)\" != \"\"",
            "certbot certonly --standalone --non-interactive --agree-tos "
            + "--keep-until-expiring --cert-name "
            + _q(doh_hostname)
            + " --email "
            + _q(contact_email)
            + " -d "
            + _q(doh_hostname),
            f"test -f {_q(live_dir + '/fullchain.pem')} && test -f {_q(live_dir + '/privkey.pem')}",
            f"openssl x509 -in {_q(live_dir + '/fullchain.pem')} -noout -checkend 1209600",
            f"openssl x509 -in {_q(live_dir + '/fullchain.pem')} -noout -checkhost {_q(doh_hostname)} >/dev/null",
            f"install -d -o root -g root -m 0700 {_q(runtime_dir)}",
            f"test \"$(sha256sum {_q(runtime_dir + '/config.json')} | awk '{{print $1}}')\" = {_q(config_sha256)}",
            f"install -o root -g root -m 0644 {_q(live_dir + '/fullchain.pem')} {_q(runtime_dir + '/fullchain.pem')}",
            f"install -o root -g root -m 0600 {_q(live_dir + '/privkey.pem')} {_q(runtime_dir + '/privkey.pem')}",
            "cert_pub=$(openssl x509 -in "
            + _q(runtime_dir + "/fullchain.pem")
            + " -pubkey -noout | openssl pkey -pubin -outform DER 2>/dev/null | sha256sum | awk '{print $1}')",
            "key_pub=$(openssl pkey -in "
            + _q(runtime_dir + "/privkey.pem")
            + " -pubout -outform DER 2>/dev/null | sha256sum | awk '{print $1}')",
            "test -n \"$cert_pub\" && test \"$cert_pub\" = \"$key_pub\"",
            installer._runtime_contract_check(
                runtime_dir + "/config.json",
                expected_proxy_ipv4,
                installer.FRONTED_LISTENER_MODE,
            ),
            f"test \"$(stat -c %a {_q(runtime_dir)})\" = 700",
            f"test \"$(stat -c %a {_q(runtime_dir + '/config.json')})\" = 600",
            f"test \"$(stat -c %a {_q(runtime_dir + '/privkey.pem')})\" = 600",
        ]
    )
    return "\n".join(lines)


def _cleanup_command(
    *,
    runtime_dir: str,
    ufw_active: bool,
    ufw_rule_present: bool,
) -> str:
    lines = ["set +e"]
    lines.append(
        f"rm -f {_q(runtime_dir + '/config.json')} {_q(runtime_dir + '/fullchain.pem')} "
        f"{_q(runtime_dir + '/privkey.pem')} {_q(runtime_dir + '/renewal-hook')}"
    )
    lines.append(f"rmdir {_q(runtime_dir)} 2>/dev/null || true")
    lines.append(f"rm -f {_q(RENEWAL_HOOK)}")
    if ufw_active and not ufw_rule_present:
        lines.append("ufw --force delete allow 80/tcp >/dev/null 2>&1 || true")
    return "\n".join(lines)


def _write_report(report: Mapping[str, Any], raw_path: str) -> None:
    value = str(raw_path or "").strip()
    if not value:
        return
    path = Path(value).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dict(report), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--brain-host", required=True)
    parser.add_argument("--node-code", required=True)
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--doh-hostname", required=True)
    parser.add_argument("--contact-email", required=True)
    parser.add_argument("--upstream-dot-ip", required=True)
    parser.add_argument("--upstream-dot-server-name", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-bundle-sha256", default="")
    parser.add_argument("--confirm-source-revision", default="")
    parser.add_argument("--confirm-node-code", default="")
    parser.add_argument("--confirm-dns-a-matches-node", default="")
    parser.add_argument("--confirm-acme-mutation", default="")
    parser.add_argument("--json-out", default="")
    return parser


def main() -> int:
    args = _parser().parse_args()
    failure_context: dict[str, Any] = {
        "receipt_id": "",
        "receipt_created": False,
        "mutation_attempted": False,
        "automatic_cleanup_status": "NOT_ARMED",
    }
    node = None
    brain = None
    preflight: dict[str, bool] = {}
    runtime_dir = ""
    try:
        node_code = installer._safe_component(args.node_code, label="node_code")
        doh_hostname = _domain(args.doh_hostname, label="doh_hostname")
        contact_email = str(args.contact_email or "").strip().lower()
        if not re.fullmatch(r"[^@\s]{1,64}@[^@\s]{1,190}", contact_email):
            raise SmartDNSRuntimePreparationError("contact_email_invalid")
        upstream_dot_ip = _public_ipv4(args.upstream_dot_ip, label="upstream_dot_ip")
        upstream_dot_server_name = _domain(
            args.upstream_dot_server_name, label="upstream_dot_server_name"
        )
        bundle_path, manifest, contents, bundle_sha256 = installer._validated_local_bundle(
            args.bundle, installer.FRONTED_LISTENER_MODE
        )
        source_revision = str((manifest.get("created_from") or {}).get("revision") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{40}", source_revision):
            raise SmartDNSRuntimePreparationError("bundle_source_revision_invalid")
        runtime_dir = f"{installer.RUNTIME_STAGE_ROOT}/{bundle_sha256}"
        live_dir = f"/etc/letsencrypt/live/{doh_hostname}"
        known_hosts = Path(args.known_hosts).resolve(strict=True)
        passwords = Path(args.passwords).resolve()
        if not known_hosts.is_file():
            raise SmartDNSRuntimePreparationError("known_hosts_missing")

        os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)
        os.environ["POKROV_SSH_TRUST_ON_FIRST_USE"] = "0"
        brain, brain_auth = _connect_owned(
            code="brain", host=str(args.brain_host), passwords=passwords
        )
        host = installer._resolve_node_host(brain, node_code)
        expected_proxy_ipv4 = installer._resolve_unique_public_ipv4(host)
        dns_a_unique = False
        dns_matches_node = False
        try:
            dns_ipv4 = _resolve_unique_public_ipv4(doh_hostname)
            dns_a_unique = True
            dns_matches_node = dns_ipv4 == expected_proxy_ipv4
        except SmartDNSRuntimePreparationError:
            # PLAN remains useful before publication; APPLY still fails closed below.
            pass
        node, node_auth = _connect_owned(code=node_code, host=host, passwords=passwords)
        preflight = _remote_preflight(
            node,
            runtime_dir=runtime_dir,
            live_dir=live_dir,
            upstream_dot_ip=upstream_dot_ip,
            upstream_dot_server_name=upstream_dot_server_name,
        )
        config = _render_config(
            contents["config/config.fronted.template.json"],
            doh_hostname=doh_hostname,
            proxy_ipv4=expected_proxy_ipv4,
            upstream_dot_ip=upstream_dot_ip,
            upstream_dot_server_name=upstream_dot_server_name,
        )
        config_sha256 = _sha256_bytes(config)
        report: dict[str, Any] = {
            "schema_version": REPORT_SCHEMA,
            "mode": "APPLY" if args.apply else "PLAN",
            "node_code": node_code,
            "listener_mode": installer.FRONTED_LISTENER_MODE,
            "bundle_sha256": bundle_sha256,
            "bundle_size_bytes": bundle_path.stat().st_size,
            "source_revision": source_revision,
            "policy_sha256": manifest["policy_sha256"],
            "config_sha256": config_sha256,
            "doh_hostname": doh_hostname,
            "dns_a_unique": dns_a_unique,
            "dns_a_matches_owned_node": dns_matches_node,
            "upstream_dot_server_name": upstream_dot_server_name,
            "known_hosts_sha256": _sha256_file(known_hosts),
            "brain_auth_method": installer._auth_family(brain_auth),
            "node_auth_method": installer._auth_family(node_auth),
            "preflight": preflight,
            "mutation_performed": False,
            "runtime_material_ready": False,
            "raw_host_returned": False,
            "raw_proxy_ipv4_returned": False,
            "raw_runtime_material_returned": False,
            "private_key_returned": False,
        }
        if not args.apply:
            report["ordered_actions"] = [
                "verify_public_dns_a_matches_owned_node",
                "retain_root_only_pre_mutation_receipt",
                "open_tcp_80_only_when_ufw_is_active_and_rule_absent",
                "install_certbot_only_when_absent",
                "issue_or_reuse_server_side_acme_certificate",
                "render_receipt_bound_root_only_runtime_material",
                "install_certificate_renewal_deploy_hook",
                "verify_certificate_key_config_and_permissions_without_returning_material",
            ]
            _write_report(report, args.json_out)
            print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
            return 0

        if args.confirm_bundle_sha256.strip().lower() != bundle_sha256:
            raise SmartDNSRuntimePreparationError("confirm_bundle_sha256_mismatch")
        if args.confirm_source_revision.strip().lower() != source_revision:
            raise SmartDNSRuntimePreparationError("confirm_source_revision_mismatch")
        if args.confirm_node_code.strip().lower() != node_code:
            raise SmartDNSRuntimePreparationError("confirm_node_code_mismatch")
        if args.confirm_dns_a_matches_node.strip() != "DNS_A_MATCHES_OWNED_NODE":
            raise SmartDNSRuntimePreparationError("dns_a_confirmation_missing")
        if args.confirm_acme_mutation.strip() != "ACME_RUNTIME_MUTATION_AUTHORIZED":
            raise SmartDNSRuntimePreparationError("acme_mutation_confirmation_missing")
        if not dns_a_unique:
            raise SmartDNSRuntimePreparationError("dns_a_not_unique_or_unavailable")
        if not dns_matches_node:
            raise SmartDNSRuntimePreparationError("dns_a_does_not_match_owned_node")
        _assert_apply_preflight(preflight)

        receipt_id = _release_id(bundle_sha256)
        failure_context["receipt_id"] = receipt_id
        receipt_dir = f"{BACKUP_ROOT}/{receipt_id}"
        _run(
            node,
            _receipt_command(
                receipt_dir=receipt_dir,
                bundle_sha256=bundle_sha256,
                source_revision=source_revision,
                node_code=node_code,
                certbot_present=preflight["certbot_present"],
                ufw_rule_present=preflight["ufw_tcp_80_rule_present"],
                live_material_present=preflight["live_cert_present"],
            ),
            label="runtime_receipt",
        )
        failure_context["receipt_created"] = True
        failure_context["automatic_cleanup_status"] = "ARMED"
        failure_context["mutation_attempted"] = True

        _run(
            node,
            "set -e; install -d -o root -g root -m 0700 " + _q(runtime_dir),
            label="runtime_stage_prepare",
        )
        sftp = node.open_sftp()
        try:
            installer._remote_write(sftp, runtime_dir + "/config.json", config, 0o600)
            installer._remote_write(
                sftp, runtime_dir + "/renewal-hook", _renewal_hook(doh_hostname), 0o700
            )
        finally:
            sftp.close()

        command = _prepare_command(
            runtime_dir=runtime_dir,
            live_dir=live_dir,
            doh_hostname=doh_hostname,
            contact_email=contact_email,
            config_sha256=config_sha256,
            expected_proxy_ipv4=expected_proxy_ipv4,
            ufw_active=preflight["ufw_active"],
            ufw_rule_present=preflight["ufw_tcp_80_rule_present"],
            certbot_present=preflight["certbot_present"],
        )
        command += (
            "\ninstall -D -o root -g root -m 0700 "
            + _q(runtime_dir + "/renewal-hook")
            + " "
            + _q(RENEWAL_HOOK)
        )
        command += "\nprintf '%s\\n' applied > " + _q(receipt_dir + "/state")
        _run(node, command, label="runtime_prepare_apply", timeout=600)
        failure_context["automatic_cleanup_status"] = "NOT_NEEDED"
        report.update(
            {
                "mutation_performed": True,
                "runtime_material_ready": True,
                "receipt_id": receipt_id,
                "certificate_server_side": True,
                "certificate_valid_at_least_14_days": True,
                "renewal_hook_installed": True,
                "tcp_80_rule_added": bool(
                    preflight["ufw_active"] and not preflight["ufw_tcp_80_rule_present"]
                ),
                "certbot_installed": not preflight["certbot_present"],
                "automatic_cleanup_status": "NOT_NEEDED",
            }
        )
        _write_report(report, args.json_out)
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        if node is not None and failure_context["automatic_cleanup_status"] == "ARMED":
            try:
                _run(
                    node,
                    _cleanup_command(
                        runtime_dir=runtime_dir,
                        ufw_active=bool(preflight.get("ufw_active")),
                        ufw_rule_present=bool(preflight.get("ufw_tcp_80_rule_present")),
                    ),
                    label="automatic_cleanup",
                )
                failure_context["automatic_cleanup_status"] = "PASS"
            except Exception:
                failure_context["automatic_cleanup_status"] = "FAIL"
        code = str(exc).split(":", 1)[0][:160]
        failure_report = {
            "schema_version": REPORT_SCHEMA,
            "mode": "ERROR",
            "error_code": code,
            "receipt_id": failure_context["receipt_id"] or None,
            "receipt_created": failure_context["receipt_created"],
            "mutation_attempted": failure_context["mutation_attempted"],
            "automatic_cleanup_status": failure_context["automatic_cleanup_status"],
            "certbot_and_acme_material_may_be_retained_after_failed_apply": bool(
                failure_context["mutation_attempted"]
            ),
            "raw_host_returned": False,
            "raw_proxy_ipv4_returned": False,
            "raw_runtime_material_returned": False,
            "private_key_returned": False,
        }
        try:
            _write_report(failure_report, str(getattr(args, "json_out", "") or ""))
        except Exception:
            pass
        print(
            "owned Smart DNS runtime preparation failed: "
            f"{type(exc).__name__}: {code} "
            f"automatic_cleanup_status={failure_context['automatic_cleanup_status']}",
            file=sys.stderr,
        )
        return 1
    finally:
        if node is not None:
            node.close()
        if brain is not None:
            brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
