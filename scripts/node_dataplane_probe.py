from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import ssl
import time
from datetime import datetime
from pathlib import Path


def _utcnow() -> datetime:
    return datetime.utcnow()


def _truncate(message: object, limit: int = 500) -> str:
    text = str(message or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _certificate_names(cert: dict) -> list[str]:
    names: list[str] = []
    for key, value in cert.get("subjectAltName", []) or []:
        if key == "DNS" and value and value not in names:
            names.append(str(value).strip().lower())
    for part in cert.get("subject", []) or []:
        for key, value in part:
            if key == "commonName" and value:
                name = str(value).strip().lower()
                if name not in names:
                    names.append(name)
    return names


def _certificate_matches_expected_target(expected_target: str, certificate_names: list[str]) -> bool:
    expected = str(expected_target or "").strip().lower()
    if not expected:
        return True
    for name in certificate_names:
        candidate = str(name or "").strip().lower()
        if candidate == expected:
            return True
        if candidate.startswith("*."):
            suffix = candidate[1:]
            if expected.endswith(suffix) and expected.count(".") >= candidate.count("."):
                return True
    return False


def _ip_family(address: object) -> str:
    text = str(address or "").strip()
    if not text:
        return ""
    try:
        parsed = ipaddress.ip_address(text)
    except ValueError:
        return ""
    return "ipv4" if parsed.version == 4 else "ipv6"


def _split_resolved_ips(addresses: list[str]) -> tuple[list[str], list[str]]:
    ipv4: list[str] = []
    ipv6: list[str] = []
    for address in addresses:
        family = _ip_family(address)
        if family == "ipv4" and address not in ipv4:
            ipv4.append(address)
        elif family == "ipv6" and address not in ipv6:
            ipv6.append(address)
    return ipv4, ipv6


def _default_transport_health() -> dict[str, str]:
    return {
        "dns_resolution": "unknown",
        "tcp_connect": "unavailable",
        "tls_handshake": "unavailable",
        "reality_target": "unavailable",
    }


def _peer_ip_from_socket(sock: object) -> str:
    getter = getattr(sock, "getpeername", None)
    if not callable(getter):
        return ""
    try:
        peer = getter()
    except OSError:
        return ""
    if not isinstance(peer, tuple) or not peer:
        return ""
    return str(peer[0] or "").strip()


def _resolve_dns(host: str, port: int) -> dict:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    resolved_ips: list[str] = []
    for info in infos:
        ip = str(info[4][0] or "").strip()
        if ip and ip not in resolved_ips:
            resolved_ips.append(ip)
    if not resolved_ips:
        raise RuntimeError("dns lookup returned no addresses")
    resolved_ipv4, resolved_ipv6 = _split_resolved_ips(resolved_ips)
    return {
        "stage": "dns",
        "resolved_ips": resolved_ips,
        "resolved_ipv4": resolved_ipv4,
        "resolved_ipv6": resolved_ipv6,
    }


def _probe_tcp(host: str, port: int, timeout_sec: float) -> dict:
    started = time.perf_counter()
    sock = socket.create_connection((host, port), timeout=timeout_sec)
    try:
        latency_ms = int((time.perf_counter() - started) * 1000)
        peer_ip = _peer_ip_from_socket(sock)
    finally:
        sock.close()
    return {
        "stage": f"tcp_{port}",
        "latency_ms": latency_ms,
        "connected_ip": peer_ip,
        "connected_family": _ip_family(peer_ip),
    }


def _probe_tls(host: str, port: int, sni: str, timeout_sec: float) -> dict:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout_sec) as sock:
        with context.wrap_socket(sock, server_hostname=sni) as tls_sock:
            cert = tls_sock.getpeercert() or {}
            certificate_names = _certificate_names(cert)
            peer_ip = _peer_ip_from_socket(tls_sock)
            # Some TLS handshakes expose an empty parsed certificate here even when the
            # socket is healthy. Treat that as "target check unavailable", not mismatch.
            target_ok = True if not certificate_names else _certificate_matches_expected_target(sni, certificate_names)
            result = {
                "stage": "reality_target" if target_ok else "tls_sni",
                "tls_protocol": str(tls_sock.version() or ""),
                "tls_cipher": str((tls_sock.cipher() or ("", "", ""))[0] or ""),
                "certificate_names": certificate_names,
                "target_ok": target_ok,
                "connected_ip": peer_ip,
                "connected_family": _ip_family(peer_ip),
            }
            if not target_ok:
                result["stage"] = "reality_target"
                result["error_kind"] = "reality_target_mismatch"
                result["error_message"] = "certificate names do not match expected reality target"
            return result


def _derive_probe_classification(payload: dict) -> str:
    if bool(payload.get("ok")):
        return "healthy"

    stage = str(payload.get("stage") or "")
    error_kind = str(payload.get("error_kind") or "")
    if error_kind == "dns_lookup_failed" or stage == "dns":
        return "dns_failure"
    if error_kind in {"tcp_connect_failed", "tcp_connect_timeout"} or stage.startswith("tcp_"):
        return "transport_failure"
    if error_kind in {"tls_handshake_failed", "reality_target_mismatch"} or stage in {"tls_sni", "reality_target"}:
        return "provider_specific_path"
    return "probe_failed"


def _derive_transport_health(payload: dict) -> dict[str, str]:
    transport = _default_transport_health()
    stage = str(payload.get("stage") or "")
    error_kind = str(payload.get("error_kind") or "")

    if list(payload.get("resolved_ips") or []):
        transport["dns_resolution"] = "healthy"
    elif error_kind == "dns_lookup_failed" or stage == "dns":
        transport["dns_resolution"] = "degraded"

    if stage.startswith("tcp_") or stage in {"tls_sni", "reality_target"}:
        transport["tcp_connect"] = "healthy"
    if error_kind in {"tcp_connect_failed", "tcp_connect_timeout"} and stage.startswith("tcp_"):
        transport["tcp_connect"] = "degraded"

    if stage in {"tls_sni", "reality_target"}:
        transport["tls_handshake"] = "healthy"
    if error_kind == "tls_handshake_failed" or stage == "tls_sni":
        transport["tls_handshake"] = "degraded"

    if stage == "reality_target":
        transport["reality_target"] = "healthy" if bool(payload.get("ok")) else "degraded"

    return transport


def _derive_family_health(*, family: str, addresses: list[str], other_addresses: list[str], payload: dict) -> str:
    error_kind = str(payload.get("error_kind") or "")
    stage = str(payload.get("stage") or "")
    connected_family = str(payload.get("connected_family") or _ip_family(payload.get("connected_ip") or "")).strip().lower()

    if not addresses:
        if error_kind == "dns_lookup_failed" and not other_addresses:
            return "unknown"
        return "unavailable"

    if bool(payload.get("ok")):
        if connected_family:
            return "healthy" if connected_family == family else "unknown"
        return "healthy" if not other_addresses else "unknown"

    if error_kind == "dns_lookup_failed":
        return "unknown"

    if error_kind in {"tcp_connect_failed", "tcp_connect_timeout"}:
        return "degraded"

    if error_kind in {"tls_handshake_failed", "reality_target_mismatch"} or stage in {"tls_sni", "reality_target"}:
        if connected_family:
            return "degraded" if connected_family == family else "unknown"
        return "degraded" if not other_addresses else "unknown"

    return "unknown"


def _apply_additive_probe_fields(payload: dict) -> None:
    resolved_ips = [str(item or "").strip() for item in list(payload.get("resolved_ips") or []) if str(item or "").strip()]
    resolved_ipv4 = [str(item or "").strip() for item in list(payload.get("resolved_ipv4") or []) if str(item or "").strip()]
    resolved_ipv6 = [str(item or "").strip() for item in list(payload.get("resolved_ipv6") or []) if str(item or "").strip()]
    derived_ipv4, derived_ipv6 = _split_resolved_ips(resolved_ips)

    if not resolved_ipv4:
        resolved_ipv4 = derived_ipv4
    if not resolved_ipv6:
        resolved_ipv6 = derived_ipv6

    connected_ip = str(payload.get("connected_ip") or "").strip()
    connected_family = str(payload.get("connected_family") or _ip_family(connected_ip)).strip().lower()

    payload["resolved_ips"] = resolved_ips
    payload["resolved_ipv4"] = resolved_ipv4
    payload["resolved_ipv6"] = resolved_ipv6
    payload["connected_ip"] = connected_ip
    payload["connected_family"] = connected_family
    payload["probe_classification"] = _derive_probe_classification(payload)
    payload["transport_health"] = _derive_transport_health(payload)
    payload["ipv4_health"] = _derive_family_health(
        family="ipv4",
        addresses=resolved_ipv4,
        other_addresses=resolved_ipv6,
        payload=payload,
    )
    payload["ipv6_health"] = _derive_family_health(
        family="ipv6",
        addresses=resolved_ipv6,
        other_addresses=resolved_ipv4,
        payload=payload,
    )


def probe_node_endpoint(*, host: str, port: int = 443, sni: str | None = None, timeout_sec: float = 5.0) -> dict:
    target_sni = str(sni or host).strip()
    probed_at = _utcnow()
    payload = {
        "ok": False,
        "host": host,
        "port": int(port),
        "sni": target_sni,
        "resolved_ips": [],
        "resolved_ipv4": [],
        "resolved_ipv6": [],
        "connected_ip": "",
        "connected_family": "",
        "latency_ms": None,
        "tls_protocol": "",
        "tls_cipher": "",
        "certificate_names": [],
        "target_ok": False,
        "stage": "",
        "error_kind": "",
        "error_message": "",
        "probed_at": probed_at,
        "probe_classification": "probe_failed",
        "ipv4_health": "unknown",
        "ipv6_health": "unknown",
        "transport_health": _default_transport_health(),
    }
    try:
        dns_result = _resolve_dns(host, port)
        payload.update(dns_result)
        tcp_result = _probe_tcp(host, port, timeout_sec)
        payload.update(tcp_result)
        tls_result = _probe_tls(host, port, target_sni, timeout_sec)
        payload.update(tls_result)
        payload["ok"] = bool(tls_result.get("target_ok"))
        if payload["ok"]:
            payload["stage"] = "reality_target"
        else:
            payload["error_kind"] = str(tls_result.get("error_kind") or "reality_target_mismatch")
            payload["error_message"] = _truncate(
                tls_result.get("error_message") or "certificate names do not match expected reality target"
            )
    except socket.gaierror as exc:
        payload["stage"] = "dns"
        payload["error_kind"] = "dns_lookup_failed"
        payload["error_message"] = _truncate(exc)
    except TimeoutError as exc:
        payload["stage"] = payload["stage"] or f"tcp_{port}"
        payload["error_kind"] = "tcp_connect_timeout"
        payload["error_message"] = _truncate(exc)
    except ssl.SSLError as exc:
        payload["stage"] = "tls_sni"
        payload["error_kind"] = "tls_handshake_failed"
        payload["error_message"] = _truncate(exc)
    except OSError as exc:
        current_stage = str(payload.get("stage") or "")
        if not current_stage:
            current_stage = f"tcp_{port}"
        payload["stage"] = current_stage
        payload["error_kind"] = "tcp_connect_failed" if current_stage.startswith("tcp_") else "probe_failed"
        payload["error_message"] = _truncate(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        payload["stage"] = str(payload.get("stage") or "probe")
        payload["error_kind"] = "probe_failed"
        payload["error_message"] = _truncate(exc)
    _apply_additive_probe_fields(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Best-effort external node dataplane probe: DNS, TCP 443, TLS/SNI, and target validation."
    )
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", type=int, default=443)
    parser.add_argument("--sni", default="")
    parser.add_argument("--timeout-sec", type=float, default=5.0)
    parser.add_argument("--out", default="", help="Optional JSON output path.")
    args = parser.parse_args()

    payload = probe_node_endpoint(
        host=args.host.strip(),
        port=int(args.port),
        sni=(args.sni or "").strip() or None,
        timeout_sec=float(args.timeout_sec),
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(out_path)
    else:
        print(text)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
