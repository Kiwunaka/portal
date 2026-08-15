#!/usr/bin/env python3
"""Exact POKROV Core 1.0.3 adapter for controlled emergency probes.

The adapter accepts one bounded JSON request on stdin and never prints raw
connection material.  It loads only the pinned Windows Core artifact, starts a
loopback mixed inbound, and retrieves the owned deterministic payload through
that inbound.  A probe is successful only when the payload digest and an owned
exit-country response header are both present and valid.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import http.client
import ipaddress
import json
import os
import re
import socket
import ssl
import struct
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping
from urllib.parse import urlsplit


PROBE_SCHEMA = "pokrov-emergency-probe-adapter-v1"
VALIDATION_SCHEMA = "pokrov-emergency-core-runtime-validation-v1"
PINNED_CORE_SHA256 = "7cc83854fc4022b759e9de3d0942b90a24c859cfd51e3231d04e7c7a6b7d5054"
PINNED_CORE_SIZE = 55_134_208
PINNED_CORE_ABI = 2
MAX_STDIN_BYTES = 64 * 1024
MAX_BODY_BYTES = 4 * 1024
CONTROLLED_HOST = "connect.pokrov.space"
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


def _validate_request(request: Mapping[str, Any]) -> tuple[str, str, str, dict[str, Any]]:
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
    expected_digest = str(request.get("expected_payload_sha256") or "").strip().lower()
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
    if not isinstance(outbound, dict) or not outbound or set(outbound).difference(_OUTBOUND_KEYS):
        raise AdapterFailure("outbound_shape_invalid")
    if outbound.get("type") != "vless" or "tag" in outbound or "detour" in outbound:
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
    if transport is not None:
        if not isinstance(transport, dict) or transport.get("type") != "grpc" or outbound.get("flow"):
            raise AdapterFailure("outbound_shape_invalid")
    return stable_id, probe_url, expected_digest, dict(outbound)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class CoreBindings:
    def __init__(self, dll: Any, dll_directory: Any | None) -> None:
        self._dll = dll
        self._dll_directory = dll_directory
        self._free = dll.freeString
        self._free.argtypes = [ctypes.c_void_p]
        self._free.restype = None
        self._setup = dll.setup
        self._setup.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int32,
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_int64,
            ctypes.c_bool,
        ]
        self._setup.restype = ctypes.c_void_p
        self._start = dll.start
        self._start.argtypes = [ctypes.c_char_p, ctypes.c_bool]
        self._start.restype = ctypes.c_void_p
        self._stop = dll.stop
        self._stop.argtypes = []
        self._stop.restype = ctypes.c_void_p
        self._secure = dll.pokrovSecureFile
        self._secure.argtypes = [ctypes.c_char_p]
        self._secure.restype = ctypes.c_void_p

    @classmethod
    def load(cls, core_path: Path) -> "CoreBindings":
        resolved = core_path.resolve(strict=True)
        if resolved.name.lower() != "pokrov-core.dll":
            raise AdapterFailure("core_artifact_invalid")
        if resolved.stat().st_size != PINNED_CORE_SIZE or _sha256_file(resolved) != PINNED_CORE_SHA256:
            raise AdapterFailure("core_artifact_mismatch")
        if not (resolved.parent / "libcronet.dll").is_file():
            raise AdapterFailure("core_dependency_missing")
        dll_directory = os.add_dll_directory(str(resolved.parent)) if hasattr(os, "add_dll_directory") else None
        try:
            dll = ctypes.WinDLL(str(resolved))
            abi = dll.pokrovCoreAbiVersion
            abi.argtypes = []
            abi.restype = ctypes.c_int32
            if int(abi()) != PINNED_CORE_ABI:
                raise AdapterFailure("core_abi_mismatch")
            return cls(dll, dll_directory)
        except Exception:
            if dll_directory is not None:
                dll_directory.close()
            raise

    def _result(self, pointer: int | None) -> str:
        if not pointer:
            return ""
        try:
            return ctypes.string_at(pointer).decode("utf-8", errors="replace")
        finally:
            self._free(pointer)

    def setup(self, root: Path) -> None:
        base = root / "base"
        work = root / "work"
        temp = root / "temp"
        for path in (base, work, temp):
            path.mkdir(parents=True, exist_ok=True)
        error = self._result(
            self._setup(
                os.fsencode(base),
                os.fsencode(work),
                os.fsencode(temp),
                0,
                b"",
                b"",
                0,
                False,
            )
        )
        if error:
            raise AdapterFailure("core_setup_failed")

    def secure_file(self, path: Path) -> None:
        if self._result(self._secure(os.fsencode(path))):
            raise AdapterFailure("core_config_acl_failed")

    def start(self, config_path: Path) -> None:
        if self._result(self._start(os.fsencode(config_path), True)):
            raise AdapterFailure("core_start_failed")

    def stop(self) -> None:
        if self._result(self._stop()):
            raise AdapterFailure("core_stop_failed")

    def close(self) -> None:
        if self._dll_directory is not None:
            self._dll_directory.close()
            self._dll_directory = None


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
            "default_domain_resolver": {"server": "bootstrap", "strategy": "prefer_ipv4"},
            "final": "emergency-probe-out",
        },
    }


def _write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        os.write(descriptor, payload)
    finally:
        os.close(descriptor)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


@contextmanager
def _suppress_native_stdout() -> Iterator[None]:
    """Keep native Core logs out of the adapter's JSON stdout contract."""

    sys.stdout.flush()
    saved_fd = os.dup(1)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    saved_handle: int | None = None
    try:
        os.dup2(null_fd, 1)
        if os.name == "nt":
            import msvcrt

            kernel32 = ctypes.windll.kernel32
            kernel32.GetStdHandle.argtypes = [ctypes.c_uint32]
            kernel32.GetStdHandle.restype = ctypes.c_void_p
            kernel32.SetStdHandle.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
            kernel32.SetStdHandle.restype = ctypes.c_bool
            std_output_handle = ctypes.c_uint32(-11 & 0xFFFFFFFF)
            saved_handle = int(kernel32.GetStdHandle(std_output_handle) or 0)
            kernel32.SetStdHandle(std_output_handle, ctypes.c_void_p(msvcrt.get_osfhandle(null_fd)))
        yield
    finally:
        if os.name == "nt" and saved_handle:
            ctypes.windll.kernel32.SetStdHandle(
                ctypes.c_uint32(-11 & 0xFFFFFFFF),
                ctypes.c_void_p(saved_handle),
            )
        os.dup2(saved_fd, 1)
        os.close(null_fd)
        os.close(saved_fd)


def _redirect_stdout_for_native_runtime() -> tuple[int, int]:
    """Return a clean output fd while leaving process stdout pointed at NUL."""

    sys.stdout.flush()
    output_fd = os.dup(1)
    null_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(null_fd, 1)
    if os.name == "nt":
        import msvcrt

        kernel32 = ctypes.windll.kernel32
        kernel32.SetStdHandle.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
        kernel32.SetStdHandle.restype = ctypes.c_bool
        kernel32.SetStdHandle(
            ctypes.c_uint32(-11 & 0xFFFFFFFF),
            ctypes.c_void_p(msvcrt.get_osfhandle(null_fd)),
        )
    return output_fd, null_fd


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


def _connect_socks5(proxy_port: int, host: str, port: int, timeout: float) -> socket.socket:
    conn = socket.create_connection(("127.0.0.1", proxy_port), timeout=timeout)
    try:
        conn.sendall(b"\x05\x01\x00")
        if _recv_exact(conn, 2) != b"\x05\x00":
            raise AdapterFailure("socks_handshake_failed")
        try:
            packed_host = ipaddress.ip_address(host).packed
            atyp = b"\x01" if len(packed_host) == 4 else b"\x04"
            address = atyp + packed_host
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


def _wait_for_listener(port: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise AdapterFailure("core_listener_unavailable")


def _probe_through_socks(proxy_port: int, probe_url: str, timeout: float = 20.0) -> tuple[bytes, str]:
    parsed = urlsplit(probe_url)
    raw = _connect_socks5(proxy_port, parsed.hostname or "", parsed.port or 443, timeout)
    tls_socket: ssl.SSLSocket | None = None
    try:
        tls_socket = ssl.create_default_context().wrap_socket(raw, server_hostname=parsed.hostname)
        request = (
            f"GET {parsed.path} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}\r\n"
            "User-Agent: POKROV-emergency-core-probe/1\r\n"
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
    core_path: Path,
    outbound: Mapping[str, Any],
    runtime_factory: Callable[[Path], CoreBindings] = CoreBindings.load,
) -> Iterator[tuple[CoreBindings, int]]:
    temp_root = os.environ.get("POKROV_TEST_TEMP_ROOT")
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="pokrov-emergency-core-", dir=temp_root or None) as directory:
        root = Path(directory)
        port = _reserve_loopback_port()
        config_path = root / "probe.json"
        _write_private_json(config_path, _build_config(outbound, listen_port=port))
        with _suppress_native_stdout():
            runtime = runtime_factory(core_path)
            started = False
            try:
                runtime.setup(root)
                runtime.secure_file(config_path)
                runtime.start(config_path)
                started = True
                _wait_for_listener(port)
                yield runtime, port
            finally:
                if started:
                    runtime.stop()
                runtime.close()
                os.chdir(original_cwd)


def run_adapter(
    request: Mapping[str, Any],
    *,
    core_path: Path,
    validate_only: bool = False,
    runtime_factory: Callable[[Path], CoreBindings] = CoreBindings.load,
    probe: Callable[[int, str, float], tuple[bytes, str]] = _probe_through_socks,
) -> dict[str, Any]:
    stable_id, probe_url, expected_digest, outbound = _validate_request(request)
    started_at = time.monotonic()
    with _runtime_session(core_path=core_path, outbound=outbound, runtime_factory=runtime_factory) as (_runtime, port):
        if validate_only:
            return {
                "schema_version": VALIDATION_SCHEMA,
                "stable_id": stable_id,
                "runtime_accepted": True,
                "core_sha256": PINNED_CORE_SHA256,
            }
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
        "latency_ms": min(60_000, max(0, round((time.monotonic() - started_at) * 1000))),
        "verified_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "verification_source": "exact_core_1_0_3",
        "error_code": "",
    }


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="POKROV exact-Core emergency probe adapter")
    parser.add_argument("--core-dll", required=True, type=Path)
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    output_fd: int | None = None
    null_fd: int | None = None
    try:
        args = _parse_args(list(argv or sys.argv[1:]))
        request = _read_request(sys.stdin)
        output_fd, null_fd = _redirect_stdout_for_native_runtime()
        result = run_adapter(request, core_path=args.core_dll, validate_only=bool(args.validate_only))
        payload = (json.dumps(result, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")
        os.write(output_fd, payload)
        return 0
    except AdapterFailure as exc:
        sys.stderr.write(f"emergency_core_probe_failed code={exc.code}\n")
        return 2
    except Exception:
        sys.stderr.write("emergency_core_probe_failed code=unexpected_failure\n")
        return 2
    finally:
        if output_fd is not None:
            os.close(output_fd)
        if null_fd is not None:
            os.close(null_fd)


if __name__ == "__main__":
    raise SystemExit(main())
