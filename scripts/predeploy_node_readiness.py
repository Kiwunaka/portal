from __future__ import annotations

import argparse
import base64
import json
import socket
import ssl
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from audit_node_dns import _build_hosts, _parse_inventory_ipv4, _resolve_with_nslookup
from node_access import DEFAULT_PASSWORDS, connect_node
from node_inventory import DEFAULT_INVENTORY


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class NodeReadinessRow:
    code: str
    host: str
    enabled: bool
    accepting_new_clients: bool
    is_draining: bool
    is_healthy: bool
    health_score: float
    last_health_at: datetime | None
    last_probe_at: datetime | None
    last_probe_stage: str = ""
    last_probe_error_kind: str = ""
    last_probe_error_message: str = ""
    observer_push_configured: bool = False
    observer_last_push_at: datetime | None = None
    observer_unmatched_count: int = 0
    observer_parse_error_count: int = 0
    inbound_id: int = 0
    vless_port: int = 443
    reality_sni: str = ""
    reality_sid: str = ""
    reality_pbk: str = ""


@dataclass
class DataplaneProbeResult:
    code: str
    host: str
    dns_ok: bool
    tcp_ok: bool
    tls_ok: bool
    target_tls_ok: bool
    dns_records: list[str]
    error_kind: str = ""
    error_message: str = ""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _run(ssh, cmd: str, *, timeout: int = 60) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _b64url_nopad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _derive_public_from_private(priv_b64: str) -> str:
    pad = "=" * ((4 - (len(priv_b64) % 4)) % 4)
    priv_bytes = base64.urlsafe_b64decode(priv_b64 + pad)
    priv = x25519.X25519PrivateKey.from_private_bytes(priv_bytes)
    pub_bytes = priv.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _b64url_nopad(pub_bytes)


def _parse_epoch(value: str) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        raw = float(text)
    except Exception:
        return None
    if raw <= 0:
        return None
    return datetime.fromtimestamp(raw, tz=timezone.utc)


def _parse_node_rows(raw: str) -> list[NodeReadinessRow]:
    rows: list[NodeReadinessRow] = []
    for line in raw.splitlines():
        parts = line.split("|")
        if len(parts) < 15:
            continue
        rows.append(
            NodeReadinessRow(
                code=str(parts[0]).strip().lower(),
                host=str(parts[1]).strip(),
                enabled=str(parts[2]).strip().lower() in {"t", "true", "1"},
                accepting_new_clients=str(parts[3]).strip().lower() in {"t", "true", "1"},
                is_draining=str(parts[4]).strip().lower() in {"t", "true", "1"},
                is_healthy=str(parts[5]).strip().lower() in {"t", "true", "1"},
                health_score=float(parts[6] or 0.0),
                last_health_at=_parse_epoch(parts[7]),
                last_probe_at=_parse_epoch(parts[8]),
                last_probe_stage=str(parts[9]).strip(),
                last_probe_error_kind=str(parts[10]).strip(),
                last_probe_error_message=str(parts[11]).strip(),
                observer_push_configured=str(parts[12]).strip().lower() in {"t", "true", "1"},
                observer_last_push_at=_parse_epoch(parts[13]) if len(parts) > 13 else None,
                observer_unmatched_count=int(parts[14] or 0) if len(parts) > 14 else 0,
                observer_parse_error_count=int(parts[15] or 0) if len(parts) > 15 else 0,
                inbound_id=int(parts[16] or 0) if len(parts) > 16 else 0,
                vless_port=int(parts[17] or 443) if len(parts) > 17 else 443,
                reality_sni=str(parts[18]).strip() if len(parts) > 18 else "",
                reality_sid=str(parts[19]).strip() if len(parts) > 19 else "",
                reality_pbk=str(parts[20]).strip() if len(parts) > 20 else "",
            )
        )
    return rows


def _remote_node_columns(ssh) -> set[str]:
    query = (
        r"""runuser -u postgres -- psql -d portal -Atc "select column_name """
        r"""from information_schema.columns where table_schema='public' and table_name='nodes';" """
    )
    code, out, err = _run(ssh, query, timeout=60)
    if code != 0:
        raise RuntimeError((err or out or "unable to inspect nodes table columns").strip())
    return {str(line or "").strip() for line in out.splitlines() if str(line or "").strip()}


def _load_node_rows_from_brain(*, brain_ip: str, ssh_user: str, ssh_port: int, passwords: Path) -> list[NodeReadinessRow]:
    ssh, _auth_method = connect_node(code="brain", host=brain_ip, user=ssh_user, port=ssh_port, passwords_path=passwords)
    try:
        columns = _remote_node_columns(ssh)
        probe_epoch_sql = "coalesce(extract(epoch from last_probe_at),0)" if "last_probe_at" in columns else "0"
        probe_stage_sql = "coalesce(last_probe_stage,'')" if "last_probe_stage" in columns else "''"
        probe_error_kind_sql = "coalesce(last_probe_error_kind,'')" if "last_probe_error_kind" in columns else "''"
        probe_error_message_sql = (
            r"""coalesce(replace(last_probe_error_message, E'\n', ' '),'')"""
            if "last_probe_error_message" in columns
            else "''"
        )
        observer_push_configured_sql = (
            "case when coalesce(observer_push_secret,'') <> '' then true else false end"
            if "observer_push_secret" in columns
            else "false"
        )
        observer_push_epoch_sql = (
            "coalesce(extract(epoch from observer_last_push_at),0)"
            if "observer_last_push_at" in columns
            else "0"
        )
        observer_unmatched_sql = "coalesce(observer_unmatched_count,0)" if "observer_unmatched_count" in columns else "0"
        observer_parse_error_sql = (
            "coalesce(observer_parse_error_count,0)" if "observer_parse_error_count" in columns else "0"
        )
        query = (
            r"""runuser -u postgres -- psql -d portal -Atc "select """
            r"""code,host,enabled,accepting_new_clients,is_draining,coalesce(is_healthy,false),"""
            r"""coalesce(round(health_score::numeric,3),0),"""
            r"""coalesce(extract(epoch from last_health_at),0),"""
            + probe_epoch_sql
            + r""","""
            + probe_stage_sql
            + r""","""
            + probe_error_kind_sql
            + r""","""
            + probe_error_message_sql
            + r""","""
            + observer_push_configured_sql
            + r""","""
            + observer_push_epoch_sql
            + r""","""
            + observer_unmatched_sql
            + r""","""
            + observer_parse_error_sql
            + r""","""
            r"""coalesce(inbound_id,0),coalesce(vless_port,443),"""
            r"""coalesce(reality_sni,''),coalesce(reality_sid,''),coalesce(reality_pbk,'') """
            r"""from nodes where enabled=true order by code;" """
        )
        code, out, err = _run(ssh, query, timeout=60)
        if code != 0:
            raise RuntimeError((err or out or "psql query failed").strip())
        return _parse_node_rows(out)
    finally:
        ssh.close()


def _readiness_failures(
    rows: list[NodeReadinessRow],
    *,
    stale_after_seconds: int,
    observer_stale_after_seconds: int,
    now: datetime,
) -> list[str]:
    failures: list[str] = []
    for row in rows:
        if not row.enabled:
            continue
        if not row.is_healthy:
            failures.append(f"unhealthy:{row.code}")
        age_from = row.last_probe_at or row.last_health_at
        if age_from is None or (now - age_from).total_seconds() > stale_after_seconds:
            failures.append(f"stale:{row.code}")
        if row.last_probe_error_kind:
            failures.append(f"probe_error:{row.code}:{row.last_probe_error_kind}")
        if row.observer_push_configured:
            if row.observer_last_push_at is None or (now - row.observer_last_push_at).total_seconds() > observer_stale_after_seconds:
                failures.append(f"observer_stale:{row.code}")
    return failures


def _collect_dns_report(*, domain: str, inventory_path: Path, include_brain: bool) -> dict:
    inventory = _parse_inventory_ipv4(inventory_path)
    hosts = _build_hosts(domain=domain.strip().lower(), include_brain=include_brain, inventory=inventory)
    report = {"domain": domain, "hosts": [], "warnings": []}
    aaaa_map: dict[str, list[str]] = {}
    expected_map: dict[str, str | None] = {}
    for node in hosts:
        a_records, aaaa_records, _raw = _resolve_with_nslookup(node.host)
        expected_map[node.host] = node.expected_ipv4
        warnings: list[str] = []
        if not a_records:
            warnings.append("missing_a_record")
        if node.expected_ipv4 and node.expected_ipv4 not in a_records:
            warnings.append(f"expected_ipv4_not_found:{node.expected_ipv4}")
        if aaaa_records:
            warnings.append("has_aaaa_records")
        for ip6 in aaaa_records:
            aaaa_map.setdefault(ip6, []).append(node.host)
        report["hosts"].append(
            {
                "code": node.code,
                "host": node.host,
                "expected_ipv4": node.expected_ipv4,
                "a_records": a_records,
                "aaaa_records": aaaa_records,
                "warnings": warnings,
            }
        )
    for ip6, bound_hosts in aaaa_map.items():
        if len(bound_hosts) < 2:
            continue
        if len({expected_map.get(host) for host in bound_hosts}) > 1:
            report["warnings"].append({"type": "shared_aaaa_across_different_nodes", "ip6": ip6, "hosts": bound_hosts})
    return report


def _tls_handshake(host: str, *, server_hostname: str, timeout: float = 6.0) -> tuple[bool, str]:
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=server_hostname) as wrapped:
                cert = wrapped.getpeercert() or {}
                subject = cert.get("subject", [])
                common_names = []
                for item in subject:
                    for key, value in item:
                        if key == "commonName":
                            common_names.append(str(value))
                return True, ",".join(common_names[:3])
    except Exception as exc:
        return False, str(exc)[:200]


def _probe_node_dataplane(row: NodeReadinessRow, *, timeout: float = 5.0) -> DataplaneProbeResult:
    try:
        infos = socket.getaddrinfo(row.host, row.vless_port or 443, type=socket.SOCK_STREAM)
        dns_records = sorted({info[4][0] for info in infos if info and info[4]})
    except Exception as exc:
        return DataplaneProbeResult(
            code=row.code,
            host=row.host,
            dns_ok=False,
            tcp_ok=False,
            tls_ok=False,
            target_tls_ok=False,
            dns_records=[],
            error_kind="dns_error",
            error_message=str(exc)[:200],
        )

    try:
        with socket.create_connection((row.host, row.vless_port or 443), timeout=timeout):
            pass
    except Exception as exc:
        return DataplaneProbeResult(
            code=row.code,
            host=row.host,
            dns_ok=True,
            tcp_ok=False,
            tls_ok=False,
            target_tls_ok=False,
            dns_records=dns_records,
            error_kind="tcp_connect_error",
            error_message=str(exc)[:200],
        )

    tls_ok = False
    tls_note = ""
    if row.reality_sni:
        tls_ok, tls_note = _tls_handshake(row.host, server_hostname=row.reality_sni, timeout=timeout)

    target_tls_ok = False
    target_note = ""
    if row.reality_sni:
        target_tls_ok, target_note = _tls_handshake(row.reality_sni, server_hostname=row.reality_sni, timeout=timeout)

    error_kind = ""
    error_message = ""
    if row.reality_sni and not tls_ok:
        error_kind = "node_tls_error"
        error_message = tls_note
    elif row.reality_sni and not target_tls_ok:
        error_kind = "target_tls_error"
        error_message = target_note

    return DataplaneProbeResult(
        code=row.code,
        host=row.host,
        dns_ok=True,
        tcp_ok=True,
        tls_ok=tls_ok or not row.reality_sni,
        target_tls_ok=target_tls_ok or not row.reality_sni,
        dns_records=dns_records,
        error_kind=error_kind,
        error_message=error_message,
    )


def _probe_node_dataplane_with_retry(
    row: NodeReadinessRow,
    *,
    timeout: float = 5.0,
    attempts: int = 3,
    retry_delay_sec: float = 1.0,
) -> DataplaneProbeResult:
    last_result: DataplaneProbeResult | None = None
    total_attempts = max(1, int(attempts))
    for attempt in range(total_attempts):
        result = _probe_node_dataplane(row, timeout=timeout)
        last_result = result
        if result.dns_ok and result.tcp_ok and result.tls_ok and result.target_tls_ok:
            return result
        if attempt + 1 < total_attempts:
            time.sleep(max(0.0, float(retry_delay_sec)))
    return last_result or _probe_node_dataplane(row, timeout=timeout)


def _inspect_runtime_inbound(row: NodeReadinessRow, *, ssh_user: str, ssh_port: int, passwords: Path) -> dict:
    ssh, auth_method = connect_node(code=row.code, host=row.host, user=ssh_user, port=ssh_port, passwords_path=passwords)
    try:
        sql = (
            "sqlite3 -readonly /etc/x-ui/x-ui.db "
            f"\"PRAGMA busy_timeout=5000; select id, port, protocol, stream_settings, remark, enable from inbounds where id={int(row.inbound_id)};\""
        )
        code, out, err = _run(ssh, sql, timeout=30)
    finally:
        ssh.close()
    rows = [line.strip() for line in str(out or "").splitlines() if "|" in str(line or "")]
    if code != 0 and not rows:
        return {"inspect_error": f"sqlite_query_error:{str(err or '').strip()[:120]}", "auth_method": auth_method}
    if not rows:
        return {"inspect_error": "inbound_not_found", "auth_method": auth_method}
    parts = rows[-1].split("|", 5)
    try:
        stream = json.loads(parts[3])
    except Exception:
        stream = {}
    reality = stream.get("realitySettings") or {}
    private_key = str(reality.get("privateKey") or "")
    return {
        "inspect_error": "",
        "auth_method": auth_method,
        "inbound_id": int(parts[0]),
        "port": int(parts[1]),
        "protocol": parts[2],
        "remark": parts[4],
        "enable": bool(int(parts[5]) if len(parts) > 5 else 1),
        "network": stream.get("network"),
        "security": stream.get("security"),
        "dest": reality.get("dest", ""),
        "server_names": reality.get("serverNames") or [],
        "short_ids": reality.get("shortIds") or [],
        "public_key": _derive_public_from_private(private_key) if private_key else "",
    }


def _collect_drift_payload(rows: list[NodeReadinessRow], *, ssh_user: str, ssh_port: int, passwords: Path) -> dict:
    results: list[dict] = []
    for row in rows:
        inspected = _inspect_runtime_inbound(row, ssh_user=ssh_user, ssh_port=ssh_port, passwords=passwords)
        server_names = [str(item or "").strip() for item in inspected.get("server_names", [])]
        dest = str(inspected.get("dest") or "").strip()
        checks = {
            "inbound_present": not bool(inspected.get("inspect_error")),
            "enabled_match": bool(inspected.get("enable")) is True,
            "port_match": int(inspected.get("port") or 0) == int(row.vless_port or 443),
            "protocol_match": str(inspected.get("protocol") or "") == "vless",
            "network_match": str(inspected.get("network") or "") == "tcp",
            "security_match": str(inspected.get("security") or "") == "reality",
            "sni_match": (not row.reality_sni) or (row.reality_sni in server_names) or dest.startswith(f"{row.reality_sni}:"),
            "sid_match": (not row.reality_sid) or (row.reality_sid in [str(item or "").strip() for item in inspected.get("short_ids", [])]),
            "pbk_match": (not row.reality_pbk) or (row.reality_pbk == str(inspected.get("public_key") or "")),
        }
        mismatches = [name for name, ok in checks.items() if not ok]
        results.append(
            {
                "node_code": row.code,
                "node_host": row.host,
                "status": "ok" if not mismatches else "drift",
                "mismatches": mismatches,
                "checks": checks,
            }
        )
    return {
        "summary": {
            "total": len(results),
            "ok": sum(1 for row in results if row["status"] == "ok"),
            "drift": sum(1 for row in results if row["status"] != "ok"),
        },
        "results": results,
    }


def _aggregate_predeploy_failures(*, readiness_failures: list[str], dns_report: dict, drift_payload: dict, probe_results: list[DataplaneProbeResult] | None = None) -> list[str]:
    failures = list(readiness_failures)
    for host in dns_report.get("hosts", []) or []:
        code = str(host.get("code") or "").strip()
        for warning in host.get("warnings", []) or []:
            failures.append(f"dns:{code}:{warning}")
    for warning in dns_report.get("warnings", []) or []:
        warning_type = str((warning or {}).get("type") or "unknown").strip()
        if warning_type:
            failures.append(f"dns_warning:{warning_type}")
    for row in drift_payload.get("results", []) or []:
        if str(row.get("status") or "") == "ok":
            continue
        code = str(row.get("node_code") or "").strip()
        mismatches = ",".join(str(item) for item in (row.get("mismatches") or []))
        failures.append(f"drift:{code}:{mismatches}")
    for probe in probe_results or []:
        if not probe.dns_ok:
            failures.append(f"dataplane_dns:{probe.code}")
        if probe.dns_ok and not probe.tcp_ok:
            failures.append(f"dataplane_tcp:{probe.code}")
        if probe.tcp_ok and not probe.tls_ok:
            failures.append(f"dataplane_tls:{probe.code}")
        if probe.tls_ok and not probe.target_tls_ok:
            failures.append(f"target_tls:{probe.code}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail predeploy when node readiness, DNS, drift, or dataplane safety is degraded.")
    parser.add_argument("--brain-ip", required=True)
    parser.add_argument("--web-domain", default="pokrov.space")
    parser.add_argument("--ssh-user", default="root")
    parser.add_argument("--ssh-port", type=int, default=29374)
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--stale-after-seconds", type=int, default=1800)
    parser.add_argument("--observer-stale-after-seconds", type=int, default=180)
    parser.add_argument("--json-out", default="")
    args = parser.parse_args()

    passwords = Path(args.passwords)
    rows = _load_node_rows_from_brain(
        brain_ip=args.brain_ip,
        ssh_user=args.ssh_user,
        ssh_port=int(args.ssh_port),
        passwords=passwords,
    )
    readiness = _readiness_failures(
        rows,
        stale_after_seconds=int(args.stale_after_seconds),
        observer_stale_after_seconds=int(args.observer_stale_after_seconds),
        now=_utcnow(),
    )
    dns_report = _collect_dns_report(domain=args.web_domain, inventory_path=Path(args.inventory), include_brain=False)
    drift_payload = _collect_drift_payload(rows, ssh_user=args.ssh_user, ssh_port=int(args.ssh_port), passwords=passwords)
    probe_results = [_probe_node_dataplane_with_retry(row) for row in rows]
    failures = _aggregate_predeploy_failures(
        readiness_failures=readiness,
        dns_report=dns_report,
        drift_payload=drift_payload,
        probe_results=probe_results,
    )

    payload = {
        "checked_at": _utcnow().isoformat(),
        "rows": [asdict(row) for row in rows],
        "dns_report": dns_report,
        "drift_payload": drift_payload,
        "probe_results": [asdict(item) for item in probe_results],
        "failures": failures,
        "ok": not failures,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(out_path)
    else:
        print(text)
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
