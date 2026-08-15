"""Bounded subprocess contract for an owned exact-Core emergency probe adapter."""

from __future__ import annotations

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Sequence
from urllib.parse import urlsplit

try:
    from emergency_catalog_crypto import canonical_catalog_bytes
    from emergency_catalog_service import EndpointProbeResult
    from emergency_catalog_source import EmergencyEndpointMaterial
except ImportError:  # pragma: no cover - package import
    from .emergency_catalog_crypto import canonical_catalog_bytes
    from .emergency_catalog_service import EndpointProbeResult
    from .emergency_catalog_source import EmergencyEndpointMaterial


PROBE_ADAPTER_SCHEMA = "pokrov-emergency-probe-adapter-v1"
CONTROLLED_PROBE_HOSTS = frozenset({"api.pokrov.space"})
CONTROLLED_PROBE_PATH = "/api/emergency-probe/payload-v1"
MAX_ADAPTER_OUTPUT_BYTES = 16 * 1024
MAX_ADAPTER_COMMAND_PARTS = 4
_DIGEST_RE = re.compile(r"^[a-f0-9]{64}$")
_SAFE_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,63}$")
_OUTPUT_KEYS = frozenset(
    {
        "schema_version",
        "stable_id",
        "authenticated",
        "payload_ok",
        "payload_sha256",
        "exit_country",
        "latency_ms",
        "verified_at",
        "verification_source",
        "error_code",
    }
)


class EmergencyProbeError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _validated_probe_url(value: str) -> str:
    try:
        parsed = urlsplit(str(value or "").strip())
    except ValueError as exc:
        raise EmergencyProbeError("probe_url_invalid") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname not in CONTROLLED_PROBE_HOSTS
        or parsed.port not in {None, 443}
        or parsed.path != CONTROLLED_PROBE_PATH
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise EmergencyProbeError("probe_url_not_allowed")
    return parsed.geturl()


def _validated_command(parts: Sequence[str]) -> tuple[str, ...]:
    command = tuple(str(part or "").strip() for part in parts)
    if not 1 <= len(command) <= MAX_ADAPTER_COMMAND_PARTS or any(not part for part in command):
        raise EmergencyProbeError("probe_adapter_command_invalid")
    executable = Path(command[0])
    if not executable.is_absolute() or not executable.is_file():
        raise EmergencyProbeError("probe_adapter_missing")
    return command


def _minimal_environment() -> dict[str, str]:
    result = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONIOENCODING": "utf-8"}
    for key in ("SYSTEMROOT", "WINDIR"):
        value = os.environ.get(key)
        if value:
            result[key] = value
    return result


def _parse_adapter_output(
    payload: bytes,
    *,
    stable_id: str,
    expected_payload_sha256: str,
) -> EndpointProbeResult:
    if len(payload) > MAX_ADAPTER_OUTPUT_BYTES:
        raise EmergencyProbeError("probe_adapter_output_too_large")
    try:
        decoded = json.loads(payload.decode("utf-8", errors="strict"))
    except (UnicodeError, ValueError) as exc:
        raise EmergencyProbeError("probe_adapter_output_invalid") from exc
    if not isinstance(decoded, dict) or set(decoded).difference(_OUTPUT_KEYS):
        raise EmergencyProbeError("probe_adapter_output_invalid")
    if decoded.get("schema_version") != PROBE_ADAPTER_SCHEMA:
        raise EmergencyProbeError("probe_adapter_schema_invalid")
    if decoded.get("stable_id") != stable_id:
        raise EmergencyProbeError("probe_adapter_identity_mismatch")
    payload_sha256 = str(decoded.get("payload_sha256") or "").strip().lower()
    if payload_sha256 != expected_payload_sha256 or _DIGEST_RE.fullmatch(payload_sha256) is None:
        raise EmergencyProbeError("probe_adapter_payload_mismatch")
    country = str(decoded.get("exit_country") or "").strip().upper()
    if re.fullmatch(r"[A-Z]{2}", country) is None:
        raise EmergencyProbeError("probe_adapter_country_invalid")
    try:
        latency_ms = int(decoded.get("latency_ms"))
    except (TypeError, ValueError) as exc:
        raise EmergencyProbeError("probe_adapter_latency_invalid") from exc
    if not 0 <= latency_ms <= 60_000:
        raise EmergencyProbeError("probe_adapter_latency_invalid")
    try:
        verified_at = datetime.fromisoformat(str(decoded.get("verified_at") or "").replace("Z", "+00:00"))
    except ValueError as exc:
        raise EmergencyProbeError("probe_adapter_time_invalid") from exc
    if verified_at.tzinfo is None:
        raise EmergencyProbeError("probe_adapter_time_invalid")
    verification_source = str(decoded.get("verification_source") or "controlled_core").strip().lower()
    if _SAFE_CODE_RE.fullmatch(verification_source) is None:
        raise EmergencyProbeError("probe_adapter_source_invalid")
    error_code = str(decoded.get("error_code") or "").strip().lower()
    if error_code and _SAFE_CODE_RE.fullmatch(error_code) is None:
        raise EmergencyProbeError("probe_adapter_error_code_invalid")
    return EndpointProbeResult(
        authenticated=decoded.get("authenticated") is True,
        payload_ok=decoded.get("payload_ok") is True,
        payload_sha256=payload_sha256,
        exit_country=country,
        latency_ms=latency_ms,
        verified_at=verified_at,
        verification_source=verification_source,
        error_code=error_code,
    )


async def run_controlled_probe(
    material: EmergencyEndpointMaterial,
    *,
    adapter_command: Sequence[str],
    probe_url: str,
    expected_payload_sha256: str,
    timeout_seconds: float = 30.0,
) -> EndpointProbeResult:
    command = _validated_command(adapter_command)
    controlled_url = _validated_probe_url(probe_url)
    digest = str(expected_payload_sha256 or "").strip().lower()
    if _DIGEST_RE.fullmatch(digest) is None:
        raise EmergencyProbeError("expected_payload_digest_invalid")
    request = {
        "schema_version": PROBE_ADAPTER_SCHEMA,
        "stable_id": material.stable_id,
        "probe_url": controlled_url,
        "expected_payload_sha256": digest,
        "outbound": material.managed_outbound_fields(),
    }
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=_minimal_environment(),
    )
    try:
        stdout, _stderr = await asyncio.wait_for(
            process.communicate(canonical_catalog_bytes(request)),
            timeout=max(0.1, min(float(timeout_seconds), 60.0)),
        )
    except asyncio.TimeoutError as exc:
        process.kill()
        await process.wait()
        raise EmergencyProbeError("probe_adapter_timeout") from exc
    if process.returncode != 0:
        raise EmergencyProbeError("probe_adapter_failed")
    return _parse_adapter_output(
        stdout,
        stable_id=material.stable_id,
        expected_payload_sha256=digest,
    )
