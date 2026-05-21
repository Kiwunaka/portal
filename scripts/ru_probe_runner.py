from __future__ import annotations

import argparse
import http.client
import json
import socket
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import node_dataplane_probe as dataplane_probe


REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"
DEFAULT_TIMEOUT_SEC = 5.0


def _utcnow_text() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_inventory(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|") or "`" not in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) < 7:
            continue
        code = parts[0].strip("`").strip().lower()
        if not code or code == "code":
            continue
        rows.append(
            {
                "code": code,
                "physical_name": parts[1].strip("`").strip(),
                "country": parts[2].strip("`").strip().upper(),
                "role": parts[3].strip("`").strip(),
                "runtime_status": parts[4].strip("`").strip(),
                "plan": parts[5].strip("`").strip(),
                "ip": parts[6].strip("`").strip(),
            }
        )
    return rows


def _build_default_targets(inventory_path: Path, reserve_host: str = "", reserve_hysteria_port: int = 443) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = [
        {
            "name": "google",
            "kind": "internet",
            "host": "google.com",
            "port": 443,
            "sni": "google.com",
            "include_http": True,
            "http_path": "/",
        },
        {
            "name": "pokrov-space",
            "kind": "canonical",
            "host": "pokrov.space",
            "port": 443,
            "sni": "pokrov.space",
            "include_http": True,
            "http_path": "/",
        },
        {
            "name": "app-pokrov-space",
            "kind": "canonical",
            "host": "app.pokrov.space",
            "port": 443,
            "sni": "app.pokrov.space",
            "include_http": True,
            "http_path": "/",
        },
        {
            "name": "api-pokrov-space",
            "kind": "canonical",
            "host": "api.pokrov.space",
            "port": 443,
            "sni": "api.pokrov.space",
            "include_http": True,
            "http_path": "/api/health",
        },
    ]

    for row in _parse_inventory(inventory_path):
        code = str(row.get("code") or "").strip().lower()
        country = str(row.get("country") or "").strip().upper()
        role = str(row.get("role") or "").strip().lower()
        ip = str(row.get("ip") or "").strip()
        if not code or not ip:
            continue
        if code in {"brain", "mini", "rf1"} or country == "RU":
            continue
        if "delivery" not in role and "pool" not in role:
            continue
        targets.append(
            {
                "name": f"node-{code}",
                "kind": "foreign_node",
                "host": ip,
                "port": 443,
                "sni": "",
                "include_http": False,
                "node_code": code,
            }
        )

    reserve = str(reserve_host or "").strip()
    if reserve:
        targets.append(
            {
                "name": "reserve-xhttp",
                "kind": "reserve_xhttp",
                "host": reserve,
                "port": 443,
                "sni": reserve,
                "include_http": False,
            }
        )
        targets.append(
            {
                "name": "reserve-hysteria",
                "kind": "reserve_hysteria",
                "host": reserve,
                "port": int(reserve_hysteria_port),
                "sni": "",
                "include_udp": True,
            }
        )
    return targets


def _probe_https_head(*, host: str, port: int, sni: str, path: str, timeout_sec: float) -> dict[str, Any]:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    started = time.perf_counter()
    conn = http.client.HTTPSConnection(host=host, port=port, timeout=timeout_sec, context=context)
    try:
        conn.request("HEAD", path or "/", headers={"Host": sni or host, "User-Agent": "pokrov-ru-probe/1.0"})
        response = conn.getresponse()
        response.read()
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "http_ok": 200 <= int(response.status) < 500,
            "http_status": int(response.status),
            "http_reason": str(response.reason or "").strip(),
            "http_latency_ms": latency_ms,
            "http_error_kind": "",
            "http_error_message": "",
        }
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "http_ok": False,
            "http_status": None,
            "http_reason": "",
            "http_latency_ms": None,
            "http_error_kind": "http_probe_failed",
            "http_error_message": str(exc).strip(),
        }
    finally:
        conn.close()


def _probe_udp_port(*, host: str, port: int, timeout_sec: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
        if not infos:
            raise OSError("dns lookup returned no udp addresses")
        family, socktype, proto, _, sockaddr = infos[0]
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout_sec)
        try:
            sock.connect(sockaddr)
            sock.send(b"\x00")
            latency_ms = int((time.perf_counter() - started) * 1000)
            try:
                sock.recv(1)
                detail = "response"
            except TimeoutError:
                detail = "sent_no_response"
            return {
                "udp_ok": True,
                "udp_latency_ms": latency_ms,
                "udp_detail": detail,
                "udp_error_kind": "",
                "udp_error_message": "",
            }
        finally:
            sock.close()
    except Exception as exc:  # pragma: no cover - defensive fallback
        return {
            "udp_ok": False,
            "udp_latency_ms": None,
            "udp_detail": "",
            "udp_error_kind": "udp_probe_failed",
            "udp_error_message": str(exc).strip(),
        }


def _run_target_probe(target: dict[str, Any], *, timeout_sec: float) -> dict[str, Any]:
    host = str(target.get("host") or "").strip()
    port = int(target.get("port") or 443)
    sni = str(target.get("sni") or "").strip() or None
    include_http = bool(target.get("include_http"))
    include_udp = bool(target.get("include_udp"))

    payload: dict[str, Any] = {
        "name": str(target.get("name") or host),
        "kind": str(target.get("kind") or "target"),
        "host": host,
        "port": port,
        "sni": sni or "",
        "ok": False,
        "stage": "",
        "error_kind": "",
        "error_message": "",
        "resolved_ips": [],
        "dns_ok": False,
        "tcp_ok": None,
        "tcp_latency_ms": None,
        "tls_ok": None,
        "tls_protocol": "",
        "tls_cipher": "",
        "http_ok": None,
        "http_status": None,
        "http_reason": "",
        "http_latency_ms": None,
        "udp_ok": None,
        "udp_latency_ms": None,
        "udp_detail": "",
        "detail": "",
    }

    if include_udp:
        try:
            dns = dataplane_probe._resolve_dns(host, port)
            payload["resolved_ips"] = list(dns.get("resolved_ips") or [])
            payload["dns_ok"] = bool(payload["resolved_ips"])
        except Exception as exc:
            payload["stage"] = "dns"
            payload["error_kind"] = "dns_lookup_failed"
            payload["error_message"] = str(exc).strip()
            payload["detail"] = payload["error_message"] or "dns lookup failed"
            return payload

        udp_result = _probe_udp_port(host=host, port=port, timeout_sec=timeout_sec)
        payload["udp_ok"] = bool(udp_result.get("udp_ok"))
        payload["udp_latency_ms"] = udp_result.get("udp_latency_ms")
        payload["udp_detail"] = str(udp_result.get("udp_detail") or "")
        payload["ok"] = bool(udp_result.get("udp_ok"))
        payload["stage"] = "udp_443"
        payload["error_kind"] = str(udp_result.get("udp_error_kind") or "")
        payload["error_message"] = str(udp_result.get("udp_error_message") or "")
        payload["detail"] = payload["udp_detail"] or payload["error_message"] or ("udp ok" if payload["ok"] else "udp failed")
        return payload

    base = dataplane_probe.probe_node_endpoint(host=host, port=port, sni=sni, timeout_sec=timeout_sec)
    payload["resolved_ips"] = list(base.get("resolved_ips") or [])
    payload["dns_ok"] = bool(payload["resolved_ips"])
    payload["tcp_ok"] = base.get("latency_ms") is not None
    payload["tcp_latency_ms"] = base.get("latency_ms")
    payload["tls_ok"] = bool(base.get("tls_protocol"))
    payload["tls_protocol"] = str(base.get("tls_protocol") or "")
    payload["tls_cipher"] = str(base.get("tls_cipher") or "")
    payload["stage"] = str(base.get("stage") or "")
    payload["error_kind"] = str(base.get("error_kind") or "")
    payload["error_message"] = str(base.get("error_message") or "")
    payload["ok"] = bool(base.get("ok"))

    if include_http and payload["ok"]:
        http_result = _probe_https_head(
            host=host,
            port=port,
            sni=str(sni or host),
            path=str(target.get("http_path") or "/"),
            timeout_sec=timeout_sec,
        )
        payload["http_ok"] = bool(http_result.get("http_ok"))
        payload["http_status"] = http_result.get("http_status")
        payload["http_reason"] = str(http_result.get("http_reason") or "")
        payload["http_latency_ms"] = http_result.get("http_latency_ms")
        if not payload["http_ok"]:
            payload["error_kind"] = str(http_result.get("http_error_kind") or payload["error_kind"])
            payload["error_message"] = str(http_result.get("http_error_message") or payload["error_message"])
        payload["ok"] = bool(payload["http_ok"])
        payload["stage"] = "http"
        payload["detail"] = (
            f"http {payload['http_status']}"
            if payload["http_status"] is not None
            else (payload["error_message"] or "http probe failed")
        )
        return payload

    if include_http:
        payload["http_ok"] = False
        payload["detail"] = payload["error_message"] or "tls probe failed before http"
        return payload

    if payload["kind"] == "foreign_node":
        payload["ok"] = bool(payload["tls_ok"] or payload["tcp_ok"])
        if payload["ok"] and payload["error_kind"] == "reality_target_mismatch":
            payload["error_kind"] = ""
            payload["error_message"] = ""
        payload["detail"] = "tls handshake ok" if payload["tls_ok"] else ("tcp ok" if payload["tcp_ok"] else payload["detail"])
        return payload

    payload["detail"] = payload["error_message"] or ("tls ok" if payload["ok"] else "probe failed")
    return payload


def _build_nodes_view(targets: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}
    for target in targets:
        if str(target.get("kind") or "") != "foreign_node":
            continue
        code = str(target.get("name") or "").replace("node-", "", 1)
        nodes[code] = {
            "address": f"{target.get('host')}:{target.get('port')}",
            "reachable": bool(target.get("ok")),
            "detail": str(target.get("detail") or ""),
        }
    return nodes


def _build_reserve_summary(targets: list[dict[str, Any]]) -> dict[str, Any]:
    reserve_host = ""
    xhttp_alive = False
    hysteria_alive = False
    for target in targets:
        kind = str(target.get("kind") or "")
        if kind == "reserve_xhttp":
            reserve_host = str(target.get("host") or reserve_host)
            xhttp_alive = bool(target.get("ok"))
        elif kind == "reserve_hysteria":
            reserve_host = str(target.get("host") or reserve_host)
            hysteria_alive = bool(target.get("ok"))
    return {
        "host": reserve_host,
        "xhttp_alive": xhttp_alive,
        "hysteria_alive": hysteria_alive,
    }


def _classify_probe_report(payload: dict[str, Any]) -> list[str]:
    classifications: list[str] = []
    google_reachable = bool(payload.get("google_reachable"))
    targets = list(payload.get("targets") or [])
    reserve = dict(payload.get("reserve") or {})

    if not google_reachable:
        classifications.append("probe_host_problem")

    canonical_failed = any(str(item.get("kind") or "") == "canonical" and not bool(item.get("ok")) for item in targets)
    foreign_failed = any(str(item.get("kind") or "") == "foreign_node" and not bool(item.get("ok")) for item in targets)
    if canonical_failed:
        classifications.append("canonical_host_problem")
    if foreign_failed:
        classifications.append("foreign_edge_problem")
        classifications.append("eu_node_problem")
    if bool(reserve.get("xhttp_alive")):
        classifications.append("xhttp_alive")
    if bool(reserve.get("hysteria_alive")):
        classifications.append("hysteria_alive")
    return classifications


def _build_probe_notes(*, probe_host: str) -> list[str]:
    probe_host_value = str(probe_host or "").strip().lower()
    if probe_host_value == "current":
        origin_note = "Probe executed from the operator workstation currently in use."
    elif probe_host_value == "brain":
        origin_note = "Probe executed from the control-plane host 82.21.114.104."
    elif probe_host_value in {"mini", "ru", "ru-origin"}:
        origin_note = "Probe executed from an external RU host outside the control plane."
    else:
        origin_note = "Probe executed from the declared probe host; verify the host label before drawing origin-specific conclusions."
    return [
        origin_note,
        "UDP checks are best-effort and should be interpreted as a viability hint for Hysteria2, not a full QUIC handshake guarantee.",
    ]


def _run_probe(*, inventory_path: Path, reserve_host: str, reserve_hysteria_port: int, probe_host: str, probe_public_ip: str, timeout_sec: float) -> dict[str, Any]:
    targets = _build_default_targets(
        inventory_path=inventory_path,
        reserve_host=reserve_host,
        reserve_hysteria_port=reserve_hysteria_port,
    )
    results = [_run_target_probe(target, timeout_sec=timeout_sec) for target in targets]
    reserve = _build_reserve_summary(results)
    payload: dict[str, Any] = {
        "timestamp_utc": _utcnow_text(),
        "probe_host": probe_host or socket.gethostname(),
        "probe_public_ip": probe_public_ip or "unknown",
        "google_reachable": next((bool(item.get("ok")) for item in results if item.get("name") == "google"), False),
        "targets": results,
        "nodes": _build_nodes_view(results),
        "reserve": reserve,
        "notes": _build_probe_notes(probe_host=probe_host or socket.gethostname()),
    }
    payload["classifications"] = _classify_probe_report(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run layered RU-origin reachability checks for public hosts, delivery nodes, and the RF reserve bridge."
    )
    parser.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    parser.add_argument("--reserve-host", default="")
    parser.add_argument("--reserve-hysteria-port", type=int, default=443)
    parser.add_argument("--probe-host", default="")
    parser.add_argument("--probe-public-ip", default="")
    parser.add_argument("--timeout-sec", type=float, default=DEFAULT_TIMEOUT_SEC)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    payload = _run_probe(
        inventory_path=Path(args.inventory),
        reserve_host=str(args.reserve_host or "").strip(),
        reserve_hysteria_port=int(args.reserve_hysteria_port),
        probe_host=str(args.probe_host or "").strip(),
        probe_public_ip=str(args.probe_public_ip or "").strip(),
        timeout_sec=float(args.timeout_sec),
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(out_path)
    else:
        print(text)
    return 0 if payload.get("google_reachable") else 2


if __name__ == "__main__":
    raise SystemExit(main())
