from __future__ import annotations

import argparse
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


def _resolve_dns(host: str, port: int) -> dict:
    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    resolved_ips: list[str] = []
    for info in infos:
        ip = str(info[4][0] or "").strip()
        if ip and ip not in resolved_ips:
            resolved_ips.append(ip)
    if not resolved_ips:
        raise RuntimeError("dns lookup returned no addresses")
    return {
        "stage": "dns",
        "resolved_ips": resolved_ips,
    }


def _probe_tcp(host: str, port: int, timeout_sec: float) -> dict:
    started = time.perf_counter()
    sock = socket.create_connection((host, port), timeout=timeout_sec)
    try:
        latency_ms = int((time.perf_counter() - started) * 1000)
    finally:
        sock.close()
    return {
        "stage": f"tcp_{port}",
        "latency_ms": latency_ms,
    }


def _probe_tls(host: str, port: int, sni: str, timeout_sec: float) -> dict:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, port), timeout=timeout_sec) as sock:
        with context.wrap_socket(sock, server_hostname=sni) as tls_sock:
            cert = tls_sock.getpeercert() or {}
            certificate_names = _certificate_names(cert)
            target_ok = _certificate_matches_expected_target(sni, certificate_names)
            result = {
                "stage": "reality_target" if target_ok else "tls_sni",
                "tls_protocol": str(tls_sock.version() or ""),
                "tls_cipher": str((tls_sock.cipher() or ("", "", ""))[0] or ""),
                "certificate_names": certificate_names,
                "target_ok": target_ok,
            }
            if not target_ok:
                result["stage"] = "reality_target"
                result["error_kind"] = "reality_target_mismatch"
                result["error_message"] = "certificate names do not match expected reality target"
            return result


def probe_node_endpoint(*, host: str, port: int = 443, sni: str | None = None, timeout_sec: float = 5.0) -> dict:
    target_sni = str(sni or host).strip()
    probed_at = _utcnow()
    payload = {
        "ok": False,
        "host": host,
        "port": int(port),
        "sni": target_sni,
        "resolved_ips": [],
        "latency_ms": None,
        "tls_protocol": "",
        "tls_cipher": "",
        "certificate_names": [],
        "target_ok": False,
        "stage": "",
        "error_kind": "",
        "error_message": "",
        "probed_at": probed_at,
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
