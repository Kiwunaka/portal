#!/root/portal_bot/venv/bin/python
"""Pinned Linux sing-box adapter for production emergency-catalog probes.

The worker starts this file as a standalone executable. It accepts one bounded
JSON request on stdin, validates a source-owned VLESS/REALITY outbound, runs the
exact pinned embedded-engine build through a loopback SOCKS listener, and emits
one safe JSON result. Raw connection material and child-process logs never
reach stdout or stderr.
"""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import os
import re
import signal
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping
from urllib.parse import urlsplit


PROBE_SCHEMA = "pokrov-emergency-probe-adapter-v1"
PINNED_ENGINE_PATH = Path(
    "/usr/local/lib/pokrov-emergency/pokrov-sing-box-linux-amd64"
)
PINNED_ENGINE_SHA256 = (
    "d97cdb22be9f69843241f3d1589be2c63dbb18a281cb357e9f9141e6e886ddb2"
)
PINNED_ENGINE_SIZE = 73_756_820
PINNED_ENGINE_VERSION = "1.13.0"
MAX_STDIN_BYTES = 64 * 1024
MAX_BODY_BYTES = 4 * 1024
CONTROLLED_HOST = "api.pokrov.space"
CONTROLLED_PATH = "/api/emergency-probe/payload-v1"
COUNTRY_HEADER = "X-Pokrov-Exit-Country"
PAYLOAD_SCHEMA_HEADER = "X-Pokrov-Probe-Schema"
PAYLOAD_SCHEMA_VALUE = "pokrov-emergency-probe-payload-v1"
_HEX64_RE = re.compile(r"^[a-f0-9]{64}$")
_STABLE_ID_RE = re.compile(r"^emg_[a-f0-9]{24}$")
_COUNTRY_RE = re.compile(r"^[A-Z]{2}$")
_OUTBOUND_KEYS = frozenset(
    {
        "type",
        "server",
        "server_port",
        "uuid",
        "flow",
        "packet_encoding",
        "tls",
        "transport",
    }
)


class AdapterFailure(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _read_request(stream: Any) -> dict[str, Any]:
    payload = stream.buffer.read(MAX_STDIN_BYTES + 1)
    if len(payload) > MAX_STDIN_BYTES:
        raise AdapterFailure("request_too_large")
    try:
        decoded = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeError, ValueError) as exc:
        raise AdapterFailure("request_invalid") from exc
    if not isinstance(decoded, dict):
        raise AdapterFailure("request_invalid")
    return decoded


def _validate_request(
    request: Mapping[str, Any],
) -> tuple[str, str, str, dict[str, Any]]:
    if set(request) != {
        "schema_version",
        "stable_id",
        "probe_url",
        "expected_payload_sha256",
        "outbound",
    }:
        raise AdapterFailure("request_shape_invalid")
    if request.get("schema_version") != PROBE_SCHEMA:
        raise AdapterFailure("request_schema_invalid")
    stable_id = str(request.get("stable_id") or "").strip().lower()
    if _STABLE_ID_RE.fullmatch(stable_id) is None:
        raise AdapterFailure("stable_id_invalid")
    expected_digest = str(
        request.get("expected_payload_sha256") or ""
    ).strip().lower()
    if _HEX64_RE.fullmatch(expected_digest) is None:
        raise AdapterFailure("payload_digest_invalid")

    probe_url = str(request.get("probe_url") or "").strip()
    try:
        parsed = urlsplit(probe_url)
    except ValueError as exc:
        raise AdapterFailure("probe_url_invalid") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != CONTROLLED_HOST
        or parsed.port not in {None, 443}
        or parsed.path != CONTROLLED_PATH
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise AdapterFailure("probe_url_invalid")

    outbound = request.get("outbound")
    if (
        not isinstance(outbound, dict)
        or not outbound
        or set(outbound).difference(_OUTBOUND_KEYS)
        or outbound.get("type") != "vless"
        or "tag" in outbound
        or "detour" in outbound
    ):
        raise AdapterFailure("outbound_shape_invalid")
    if not isinstance(outbound.get("server"), str) or not outbound["server"].strip():
        raise AdapterFailure("outbound_shape_invalid")
    try:
        server_port = int(outbound.get("server_port"))
    except (TypeError, ValueError) as exc:
        raise AdapterFailure("outbound_shape_invalid") from exc
    if not 1 <= server_port <= 65535:
        raise AdapterFailure("outbound_shape_invalid")
    tls = outbound.get("tls")
    if not isinstance(tls, dict) or tls.get("enabled") is not True:
        raise AdapterFailure("outbound_shape_invalid")
    reality = tls.get("reality")
    if not isinstance(reality, dict) or reality.get("enabled") is not True:
        raise AdapterFailure("outbound_shape_invalid")
    transport = outbound.get("transport")
    if transport is not None and (
        not isinstance(transport, dict)
        or transport.get("type") != "grpc"
        or bool(outbound.get("flow"))
    ):
        raise AdapterFailure("outbound_shape_invalid")
    return stable_id, probe_url, expected_digest, dict(outbound)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_engine(path: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise AdapterFailure("engine_artifact_missing") from exc
    if (
        resolved != PINNED_ENGINE_PATH
        or not resolved.is_file()
        or resolved.stat().st_size != PINNED_ENGINE_SIZE
        or _sha256_file(resolved) != PINNED_ENGINE_SHA256
        or not os.access(resolved, os.X_OK)
    ):
        raise AdapterFailure("engine_artifact_mismatch")
    return resolved


def _reserve_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _build_config(outbound: Mapping[str, Any], *, listen_port: int) -> dict[str, Any]:
    managed = dict(outbound)
    managed["tag"] = "emergency-probe-out"
    return {
        "log": {"level": "error", "timestamp": True},
        "dns": {
            "servers": [{"type": "local", "tag": "bootstrap"}],
            "final": "bootstrap",
        },
        "inbounds": [
            {
                "type": "mixed",
                "tag": "emergency-probe-in",
                "listen": "127.0.0.1",
                "listen_port": listen_port,
            }
        ],
        "outbounds": [managed, {"type": "direct", "tag": "direct"}],
        "route": {
            "default_domain_resolver": {
                "server": "bootstrap",
                "strategy": "prefer_ipv4",
            },
            "final": "emergency-probe-out",
        },
    }


def _write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)


def _recv_exact(conn: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = conn.recv(remaining)
        if not chunk:
            raise AdapterFailure("socks_handshake_failed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _connect_socks5(
    proxy_port: int,
    host: str,
    port: int,
    timeout: float,
) -> socket.socket:
    conn = socket.create_connection(("127.0.0.1", proxy_port), timeout=timeout)
    try:
        conn.sendall(b"\x05\x01\x00")
        if _recv_exact(conn, 2) != b"\x05\x00":
            raise AdapterFailure("socks_handshake_failed")
        try:
            packed_host = ipaddress.ip_address(host).packed
            address = (b"\x01" if len(packed_host) == 4 else b"\x04") + packed_host
        except ValueError:
            encoded_host = host.encode("idna")
            if not 1 <= len(encoded_host) <= 255:
                raise AdapterFailure("socks_target_invalid")
            address = b"\x03" + bytes([len(encoded_host)]) + encoded_host
        conn.sendall(b"\x05\x01\x00" + address + struct.pack("!H", port))
        header = _recv_exact(conn, 4)
        if header[:2] != b"\x05\x00":
            raise AdapterFailure("socks_connect_failed")
        address_type = header[3]
        if address_type == 1:
            _recv_exact(conn, 4)
        elif address_type == 4:
            _recv_exact(conn, 16)
        elif address_type == 3:
            _recv_exact(conn, _recv_exact(conn, 1)[0])
        else:
            raise AdapterFailure("socks_handshake_failed")
        _recv_exact(conn, 2)
        return conn
    except Exception:
        conn.close()
        raise


def _wait_for_listener(
    process: subprocess.Popen[bytes],
    port: int,
    timeout: float = 8.0,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AdapterFailure("engine_start_failed")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise AdapterFailure("engine_listener_unavailable")


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3.0)
    except (OSError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            process.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            pass


def _probe_through_socks(
    proxy_port: int,
    probe_url: str,
    timeout: float = 20.0,
) -> tuple[bytes, str]:
    parsed = urlsplit(probe_url)
    raw = _connect_socks5(proxy_port, parsed.hostname or "", parsed.port or 443, timeout)
    tls_socket: ssl.SSLSocket | None = None
    try:
        tls_socket = ssl.create_default_context().wrap_socket(
            raw,
            server_hostname=parsed.hostname,
        )
        request = (
            f"GET {parsed.path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}\r\n"
            "User-Agent: POKROV-emergency-engine-probe/1\r\n"
            "Accept: application/octet-stream\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        tls_socket.sendall(request)
        response = http.client.HTTPResponse(tls_socket)
        response.begin()
        body = response.read(MAX_BODY_BYTES + 1)
        if response.status != 200 or len(body) > MAX_BODY_BYTES:
            raise AdapterFailure("probe_response_invalid")
        if response.getheader(PAYLOAD_SCHEMA_HEADER, "") != PAYLOAD_SCHEMA_VALUE:
            raise AdapterFailure("probe_response_invalid")
        country = response.getheader(COUNTRY_HEADER, "").strip().upper()
        if _COUNTRY_RE.fullmatch(country) is None or country == "RU":
            raise AdapterFailure("probe_country_unavailable")
        return body, country
    finally:
        if tls_socket is not None:
            tls_socket.close()
        else:
            raw.close()


@contextmanager
def _runtime_session(
    *,
    engine_path: Path,
    outbound: Mapping[str, Any],
    process_factory: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> Iterator[int]:
    engine = _validate_engine(engine_path)
    with tempfile.TemporaryDirectory(prefix="pokrov-emergency-engine-") as directory:
        root = Path(directory)
        port = _reserve_loopback_port()
        config_path = root / "probe.json"
        _write_private_json(config_path, _build_config(outbound, listen_port=port))
        child_env = {
            "HOME": str(root),
            "TMPDIR": str(root),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        process = process_factory(
            [str(engine), "run", "-c", str(config_path)],
            cwd=str(root),
            env=child_env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            _wait_for_listener(process, port)
            yield port
        finally:
            _stop_process(process)


def run_adapter(
    request: Mapping[str, Any],
    *,
    engine_path: Path = PINNED_ENGINE_PATH,
    runtime_session: Callable[..., Iterator[int]] = _runtime_session,
    probe: Callable[[int, str, float], tuple[bytes, str]] = _probe_through_socks,
) -> dict[str, Any]:
    stable_id, probe_url, expected_digest, outbound = _validate_request(request)
    started_at = time.monotonic()
    with runtime_session(engine_path=engine_path, outbound=outbound) as port:
        body, country = probe(port, probe_url, 20.0)
    digest = hashlib.sha256(body).hexdigest()
    if digest != expected_digest:
        raise AdapterFailure("probe_payload_mismatch")
    return {
        "schema_version": PROBE_SCHEMA,
        "stable_id": stable_id,
        "authenticated": True,
        "payload_ok": True,
        "payload_sha256": digest,
        "exit_country": country,
        "latency_ms": min(
            60_000,
            max(0, round((time.monotonic() - started_at) * 1000)),
        ),
        "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "verification_source": "exact_embedded_engine_1_13_0_linux",
        "error_code": "",
    }


def main() -> int:
    try:
        request = _read_request(sys.stdin)
        result = run_adapter(request)
        sys.stdout.write(
            json.dumps(result, ensure_ascii=True, separators=(",", ":")) + "\n"
        )
        return 0
    except AdapterFailure as exc:
        sys.stderr.write(f"emergency_linux_probe_failed code={exc.code}\n")
        return 2
    except Exception:
        sys.stderr.write("emergency_linux_probe_failed code=unexpected_failure\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
