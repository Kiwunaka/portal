from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


ADAPTER_ENV = "NODE_AUTHENTICATED_EGRESS_ADAPTER"
PROFILES_ENV = "NODE_AUTHENTICATED_EGRESS_PROFILES"
DEFAULT_TIMEOUT_SECONDS = 15.0
MAX_REGISTRY_BYTES = 64 * 1024
MAX_ADAPTER_OUTPUT_BYTES = 64 * 1024

_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _result(
    *,
    ok: bool | None,
    error_kind: str = "",
    classification: str = "",
    probed_at: datetime | None = None,
) -> dict[str, object]:
    state = "healthy" if ok is True else ("failed" if ok is False else "unavailable")
    return {
        "ok": ok,
        "state": state,
        "stage": "authenticated_egress",
        "error_kind": str(error_kind or ""),
        "probe_classification": str(classification or error_kind or "authenticated_egress_unavailable"),
        "probed_at": probed_at or _utcnow(),
    }


def _parse_utc(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc).replace(tzinfo=None)


def _secure_runtime_path(path: Path, *, executable: bool) -> bool:
    if not path.is_absolute():
        return False
    try:
        resolved = path.resolve(strict=True)
        path_stat = path.stat()
        path_lstat = path.lstat()
    except OSError:
        return False
    if not stat.S_ISREG(path_stat.st_mode):
        return False
    if os.name != "nt":
        get_euid = getattr(os, "geteuid", None)
        if (
            resolved != path
            or stat.S_ISLNK(path_lstat.st_mode)
            or get_euid is None
            or path_stat.st_uid not in {0, int(get_euid())}
            or path_stat.st_mode & (stat.S_IWGRP | stat.S_IWOTH)
        ):
            return False
    if executable and not os.access(path, os.X_OK):
        return False
    return True


def _adapter_environment() -> dict[str, str]:
    """Return a fixed neutral environment; never inherit service secrets."""

    if os.name == "nt":
        system_root = str(os.environ.get("SystemRoot") or r"C:\Windows")
        return {
            "PATH": str(Path(system_root) / "System32"),
            "SystemRoot": system_root,
        }
    return {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }


def _load_profile(
    *,
    registry_path: Path,
    node_code: str,
    now: datetime,
) -> tuple[dict[str, str] | None, str]:
    if not _secure_runtime_path(registry_path, executable=False):
        return None, "probe_material_unavailable"
    try:
        raw = registry_path.read_bytes()
    except OSError:
        return None, "probe_material_unavailable"
    if not raw or len(raw) > MAX_REGISTRY_BYTES:
        return None, "probe_material_invalid"
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return None, "probe_material_invalid"
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "profiles"}:
        return None, "probe_material_invalid"
    if payload.get("schema_version") != 1 or not isinstance(payload.get("profiles"), dict):
        return None, "probe_material_invalid"
    entry = payload["profiles"].get(node_code)
    if not isinstance(entry, dict) or set(entry) != {"profile_id", "expires_at"}:
        return None, "probe_material_unavailable"
    profile_id = entry.get("profile_id")
    expires_at = _parse_utc(entry.get("expires_at"))
    if not isinstance(profile_id, str) or _CODE_RE.fullmatch(profile_id) is None or expires_at is None:
        return None, "probe_material_invalid"
    if expires_at <= now:
        return None, "probe_material_expired"
    return {"profile_id": profile_id, "expires_at": str(entry["expires_at"])}, ""


def _run_adapter(
    *,
    adapter_path: Path,
    request: dict[str, object],
    timeout_sec: float,
) -> tuple[str, bytes]:
    try:
        process = subprocess.Popen(
            [str(adapter_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=_adapter_environment(),
        )
    except OSError:
        return "probe_material_unavailable", b""

    chunks: list[bytes] = []
    overflow = threading.Event()

    def _read_stdout() -> None:
        total = 0
        assert process.stdout is not None
        while True:
            chunk = process.stdout.read(8192)
            if not chunk:
                return
            remaining = MAX_ADAPTER_OUTPUT_BYTES + 1 - total
            if remaining > 0:
                chunks.append(chunk[:remaining])
                total += min(len(chunk), remaining)
            if total > MAX_ADAPTER_OUTPUT_BYTES or len(chunk) > remaining:
                overflow.set()
                return

    reader = threading.Thread(target=_read_stdout, daemon=True)
    reader.start()
    request_bytes = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    try:
        if process.stdin is not None:
            try:
                process.stdin.write(request_bytes)
                process.stdin.flush()
            except BrokenPipeError:
                pass
            finally:
                process.stdin.close()

        deadline = time.monotonic() + max(1.0, float(timeout_sec))
        while process.poll() is None:
            if overflow.is_set():
                process.kill()
                process.wait(timeout=2.0)
                reader.join(timeout=1.0)
                return "adapter_output_too_large", b""
            if time.monotonic() >= deadline:
                process.kill()
                process.wait(timeout=2.0)
                reader.join(timeout=1.0)
                return "adapter_timeout", b""
            time.sleep(0.01)
        reader.join(timeout=1.0)
    finally:
        if process.poll() is None:
            process.kill()
        if process.stdout is not None:
            process.stdout.close()

    if reader.is_alive():
        return "adapter_timeout", b""
    if overflow.is_set():
        return "adapter_output_too_large", b""
    if process.returncode != 0:
        return "adapter_exit_nonzero", b""
    return "", b"".join(chunks)


def _parse_adapter_response(raw: bytes, *, expected_profile_id: str) -> tuple[bool | None, str, str]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError):
        return False, "adapter_malformed_response", "adapter_failure"
    required = {"schema_version", "profile_id", "status", "classification", "detail_code"}
    if not isinstance(payload, dict) or set(payload) != required:
        return False, "adapter_malformed_response", "adapter_failure"
    schema_version = payload.get("schema_version")
    profile_id = payload.get("profile_id")
    status = payload.get("status")
    classification = payload.get("classification")
    detail_code = payload.get("detail_code")
    if (
        type(schema_version) is not int
        or schema_version != 1
        or not isinstance(profile_id, str)
        or profile_id != expected_profile_id
        or not isinstance(status, str)
        or status not in {"pass", "fail", "not_run"}
        or not isinstance(classification, str)
        or _CODE_RE.fullmatch(classification) is None
        or (
            detail_code is not None
            and (not isinstance(detail_code, str) or _CODE_RE.fullmatch(detail_code) is None)
        )
    ):
        return False, "adapter_malformed_response", "adapter_failure"
    if status == "pass":
        if classification != "authenticated_egress" or detail_code is not None:
            return False, "adapter_invalid_pass", "adapter_failure"
        return True, "", classification
    if status == "fail":
        return False, str(detail_code or "authenticated_egress_failed"), classification
    return None, str(detail_code or "probe_material_unavailable"), classification


def probe_authenticated_egress(
    *,
    node_code: str,
    host: str,
    port: int,
    timeout_sec: float = DEFAULT_TIMEOUT_SECONDS,
    adapter_path: str | Path | None = None,
    profiles_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    """Run a bounded external adapter that proves authenticated proxy egress.

    The adapter owns the canary credential store. This process passes only a
    non-secret profile id and endpoint over stdin, and accepts only a strict,
    machine-readable response. Missing or expired material is unavailable and
    must never be promoted to a successful probe.
    """

    code = str(node_code or "").strip().lower()
    target_host = str(host or "").strip()
    try:
        target_port = int(port)
    except (TypeError, ValueError):
        return _result(ok=None, error_kind="probe_request_invalid")
    if _CODE_RE.fullmatch(code) is None or not target_host or not 1 <= target_port <= 65535:
        return _result(ok=None, error_kind="probe_request_invalid")

    configured_adapter = str(adapter_path or os.getenv(ADAPTER_ENV) or "").strip()
    configured_profiles = str(profiles_path or os.getenv(PROFILES_ENV) or "").strip()
    if not configured_adapter or not configured_profiles:
        return _result(ok=None, error_kind="probe_material_unavailable")

    adapter = Path(configured_adapter)
    registry = Path(configured_profiles)
    if not _secure_runtime_path(adapter, executable=True):
        return _result(ok=None, error_kind="probe_material_unavailable")

    observed_at = now or _utcnow()
    profile, profile_error = _load_profile(registry_path=registry, node_code=code, now=observed_at)
    if profile is None:
        return _result(ok=None, error_kind=profile_error, probed_at=observed_at)

    request = {
        "schema_version": 1,
        "node_code": code,
        "host": target_host,
        "port": target_port,
        "profile_id": profile["profile_id"],
    }
    run_error, raw = _run_adapter(adapter_path=adapter, request=request, timeout_sec=timeout_sec)
    if run_error:
        unavailable = run_error == "probe_material_unavailable"
        return _result(ok=None if unavailable else False, error_kind=run_error, probed_at=observed_at)
    ok, error_kind, classification = _parse_adapter_response(raw, expected_profile_id=profile["profile_id"])
    return _result(
        ok=ok,
        error_kind=error_kind,
        classification=classification,
        probed_at=observed_at,
    )
