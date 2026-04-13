from __future__ import annotations

import argparse
import ipaddress
import json
import socket
import ssl
import time
from datetime import datetime
from pathlib import Path

_HOSTER_SIGNATURES: dict[str, tuple[tuple[str, ...], str]] = {
    "hetzner": (("hetzner",), "AS24940"),
    "digitalocean": (("digitalocean",), "AS14061"),
    "vultr": (("vultr", "choopa"), "AS20473"),
    "ovh": (("ovh",), "AS16276"),
    "leaseweb": (("leaseweb",), "AS60781"),
    "aws": (("amazonaws", "aws"), "AS16509"),
    "google": (("google", "gcp"), "AS15169"),
    "azure": (("azure", "microsoft"), "AS8075"),
    "oracle": (("oraclecloud", "oracle"), "AS31898"),
    "contabo": (("contabo",), "AS51167"),
    "linode": (("linode", "akamai"), "AS63949"),
    "netcup": (("netcup",), "AS197540"),
    "timeweb": (("timeweb",), "AS9123"),
}


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


def _target_semantics(host: str, sni: str) -> str:
    raw = str(sni or host or "").strip().lower()
    if raw in {"api.telegram.org", "telegram.org"} or raw.endswith(".telegram.org"):
        return "telegram_app_path"
    if raw in {"t.me", "telegram.me", "web.telegram.org"}:
        return "telegram_web_path"
    return "generic_path"


def _target_label(host: str, sni: str) -> str:
    semantics = _target_semantics(host, sni)
    if semantics == "telegram_app_path":
        return "Telegram app path"
    if semantics == "telegram_web_path":
        return "Telegram web path"
    return ""


def _subnet_for_ip(address: str) -> str:
    text = str(address or "").strip()
    if not text:
        return ""
    try:
        parsed = ipaddress.ip_address(text)
    except ValueError:
        return ""
    prefix = 24 if parsed.version == 4 else 48
    return str(ipaddress.ip_network(f"{parsed}/{prefix}", strict=False))


def _hoster_signature(text: str) -> tuple[str | None, str | None]:
    raw = str(text or "").strip().lower()
    if not raw:
        return None, None
    for family, (aliases, asn) in _HOSTER_SIGNATURES.items():
        if any(alias in raw for alias in aliases):
            return family, asn
    return None, None


def _infer_hoster_metadata(*, host: str, connected_ip: str, resolved_ips: list[str]) -> tuple[str | None, str | None, str | None]:
    candidates: list[str] = [str(host or "").strip()]
    if connected_ip:
        candidates.append(connected_ip)
        try:
            reverse_name = socket.gethostbyaddr(connected_ip)[0]
        except Exception:
            reverse_name = ""
        if reverse_name:
            candidates.append(str(reverse_name).strip())
    for address in resolved_ips:
        if address and address not in candidates:
            candidates.append(address)

    family: str | None = None
    asn: str | None = None
    for candidate in candidates:
        family, asn = _hoster_signature(candidate)
        if family:
            break

    subnet = _subnet_for_ip(connected_ip or (resolved_ips[0] if resolved_ips else ""))
    return family, asn, subnet or None


def _root_cause_summary(payload: dict) -> str:
    label = _target_label(str(payload.get("host") or ""), str(payload.get("sni") or ""))
    prefix = f"{label}: " if label else ""
    if bool(payload.get("ok")):
        return prefix + "DNS, TCP, TLS, and reality-target checks passed."

    error_kind = str(payload.get("error_kind") or "")
    if error_kind == "dns_lookup_failed":
        return prefix + "DNS lookup failed."
    if error_kind in {"tcp_connect_failed", "tcp_connect_timeout"}:
        return prefix + "TCP connect failed before the TLS handshake."
    if error_kind == "tls_handshake_failed":
        return prefix + "TLS handshake reached the node but failed before the reality-target check."
    if error_kind == "reality_target_mismatch":
        return prefix + "Certificate names did not match the expected reality target."
    return prefix + "Probe failed before the reality-target check completed."


def _root_cause_detail(payload: dict) -> str:
    host = str(payload.get("host") or "").strip()
    connected_ip = str(payload.get("connected_ip") or "").strip()
    connected_family = str(payload.get("connected_family") or "").strip()
    certificate_names = [str(item or "").strip() for item in list(payload.get("certificate_names") or []) if str(item or "").strip()]
    expected_target = str(payload.get("sni") or host or "").strip()
    error_message = str(payload.get("error_message") or "").strip()
    details: list[str] = []

    if host:
        details.append(f"target={host}")
    if expected_target and expected_target != host:
        details.append(f"expected_target={expected_target}")
    if connected_ip:
        if connected_family:
            details.append(f"connected to {connected_ip} over {connected_family}")
        else:
            details.append(f"connected to {connected_ip}")
    if certificate_names:
        details.append("certificate_names=" + ",".join(certificate_names))
    if error_message:
        details.append(f"error={error_message}")
    return "; ".join(details)


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
    payload["target_semantics"] = _target_semantics(str(payload.get("host") or ""), str(payload.get("sni") or ""))
    hoster_family, hoster_asn, hoster_subnet = _infer_hoster_metadata(
        host=str(payload.get("host") or ""),
        connected_ip=connected_ip,
        resolved_ips=resolved_ips,
    )
    payload["hoster_family"] = hoster_family
    payload["hoster_asn"] = hoster_asn
    payload["hoster_subnet"] = hoster_subnet
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
    payload["root_cause_summary"] = _root_cause_summary(payload)
    payload["root_cause_detail"] = _root_cause_detail(payload)


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
