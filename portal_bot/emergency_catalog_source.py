"""Fail-closed parsing for the approved emergency VLESS/REALITY feed.

This module deliberately does no network or database I/O.  Source labels,
fragments and ordering are untrusted.  Only a small outbound-only schema is
accepted; trusted reachability/exit verification is applied separately before
an endpoint can become a catalog candidate.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import ipaddress
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Mapping
from urllib.parse import parse_qsl, unquote, urlsplit
from uuid import UUID


MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_SOURCE_LINES = 1_000
MAX_LINE_BYTES = 8_192
MAX_QUERY_FIELDS = 24

SOURCE_CONTRACT = "pokrov-emergency-vless-reality-v1"
STABLE_ID_PREFIX = "emg_"

_SUPPORTED_TRANSPORTS = frozenset({"tcp", "raw", "grpc"})
_SUPPORTED_FINGERPRINTS = frozenset({"chrome", "edge", "firefox", "ios", "safari"})
_SUPPORTED_ENDPOINT_PORTS = frozenset({443, 4_443, 6_443, 7_443, 8_443})
_COMMON_QUERY_KEYS = frozenset(
    {"type", "security", "pbk", "sid", "sni", "fp", "flow", "encryption"}
)
_TRANSPORT_QUERY_KEYS = {
    "tcp": frozenset({"headertype"}),
    "grpc": frozenset({"servicename", "path", "mode"}),
}
_DNS_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SHORT_ID_RE = re.compile(r"^[0-9a-f]{2,16}$")
_GRPC_SERVICE_RE = re.compile(r"^[A-Za-z0-9._~/-]{1,128}$")


class EmergencyCatalogSourceError(ValueError):
    """Whole-source rejection containing a stable, non-sensitive code only."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class EmergencySourceRejection:
    line_number: int
    code: str


@dataclass(frozen=True, slots=True)
class EmergencyEndpointMaterial:
    """Normalized credential material; repr intentionally hides all secrets."""

    stable_id: str
    transport: str
    endpoint_host: str = field(repr=False)
    endpoint_port: int = field(repr=False)
    user_uuid: str = field(repr=False)
    server_name: str = field(repr=False)
    reality_public_key: str = field(repr=False)
    reality_short_id: str = field(repr=False)
    fingerprint: str = field(repr=False)
    flow: str = field(repr=False)
    grpc_service_name: str = field(default="", repr=False)

    def safe_projection(self) -> dict[str, str]:
        """Return fields safe for logs, evidence and pre-auth catalog surfaces."""

        return {
            "stable_id": self.stable_id,
            "transport": self.transport,
            "source_contract": SOURCE_CONTRACT,
        }

    def managed_outbound_fields(self) -> dict[str, object]:
        """Return the bounded outbound material for protected profile building."""

        result: dict[str, object] = {
            "type": "vless",
            "server": self.endpoint_host,
            "server_port": self.endpoint_port,
            "uuid": self.user_uuid,
            "flow": self.flow,
            "packet_encoding": "xudp",
            "tls": {
                "enabled": True,
                "server_name": self.server_name,
                "utls": {"enabled": True, "fingerprint": self.fingerprint},
                "reality": {
                    "enabled": True,
                    "public_key": self.reality_public_key,
                    "short_id": self.reality_short_id,
                },
            },
        }
        if not self.flow:
            result.pop("flow")
        if self.transport == "grpc":
            result["transport"] = {
                "type": "grpc",
                "service_name": self.grpc_service_name,
            }
        return result


@dataclass(frozen=True, slots=True)
class EmergencySourceParseResult:
    accepted: tuple[EmergencyEndpointMaterial, ...]
    rejected: tuple[EmergencySourceRejection, ...]
    candidate_line_count: int


@dataclass(frozen=True, slots=True)
class EndpointVerification:
    """Trusted probe projection supplied by our verifier, never by the feed."""

    country_code: str
    verified_at: datetime


@dataclass(frozen=True, slots=True)
class VerifiedCandidateSelection:
    accepted: tuple[EmergencyEndpointMaterial, ...]
    rejected: tuple[EmergencySourceRejection, ...]


def _canonical_query_key(value: str) -> str:
    return value.strip().lower().replace("_", "")


def _normalize_dns_name(value: str) -> str:
    raw = unquote(value).strip().rstrip(".")
    if not raw or len(raw) > 253 or "*" in raw:
        raise EmergencyCatalogSourceError("invalid_server_name")
    try:
        normalized = raw.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise EmergencyCatalogSourceError("invalid_server_name") from exc
    labels = normalized.split(".")
    if len(labels) < 2 or any(not _DNS_LABEL_RE.fullmatch(label) for label in labels):
        raise EmergencyCatalogSourceError("invalid_server_name")
    return normalized


def _normalize_endpoint_host(value: str) -> str:
    raw = unquote(value).strip().rstrip(".")
    if not raw or len(raw) > 253:
        raise EmergencyCatalogSourceError("invalid_host")
    try:
        address = ipaddress.ip_address(raw)
    except ValueError:
        try:
            normalized = raw.encode("idna").decode("ascii").lower()
        except UnicodeError as exc:
            raise EmergencyCatalogSourceError("invalid_host") from exc
        labels = normalized.split(".")
        if len(labels) < 2 or any(not _DNS_LABEL_RE.fullmatch(label) for label in labels):
            raise EmergencyCatalogSourceError("invalid_host")
        return normalized
    if not address.is_global:
        raise EmergencyCatalogSourceError("non_public_host")
    return address.compressed


def _normalize_uuid(value: str) -> str:
    try:
        parsed = UUID(unquote(value).strip())
    except (ValueError, AttributeError) as exc:
        raise EmergencyCatalogSourceError("invalid_uuid") from exc
    if parsed.int == 0:
        raise EmergencyCatalogSourceError("invalid_uuid")
    return str(parsed)


def _normalize_public_key(value: str) -> str:
    key = unquote(value).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}", key):
        raise EmergencyCatalogSourceError("invalid_public_key")
    try:
        decoded = base64.urlsafe_b64decode(key + "=")
    except (ValueError, binascii.Error) as exc:
        raise EmergencyCatalogSourceError("invalid_public_key") from exc
    if len(decoded) != 32:
        raise EmergencyCatalogSourceError("invalid_public_key")
    return key


def _normalize_short_id(value: str) -> str:
    short_id = unquote(value).strip().lower()
    if len(short_id) % 2 != 0 or not _SHORT_ID_RE.fullmatch(short_id):
        raise EmergencyCatalogSourceError("invalid_short_id")
    return short_id


def _stable_id(material: Mapping[str, object]) -> str:
    canonical = json.dumps(material, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(
        b"pokrov-emergency-endpoint-v1\0" + canonical.encode("utf-8")
    ).hexdigest()
    return STABLE_ID_PREFIX + digest[:24]


def _parse_candidate(line: str) -> EmergencyEndpointMaterial:
    try:
        parsed = urlsplit(line)
    except ValueError as exc:
        raise EmergencyCatalogSourceError("malformed_uri") from exc
    if parsed.scheme.lower() != "vless":
        raise EmergencyCatalogSourceError("unsupported_scheme")
    if parsed.password is not None or not parsed.username:
        raise EmergencyCatalogSourceError("invalid_uuid")

    user_uuid = _normalize_uuid(parsed.username)
    endpoint_host = _normalize_endpoint_host(parsed.hostname or "")
    try:
        endpoint_port = parsed.port
    except ValueError as exc:
        raise EmergencyCatalogSourceError("invalid_port") from exc
    if endpoint_port is None or endpoint_port not in _SUPPORTED_ENDPOINT_PORTS:
        raise EmergencyCatalogSourceError("invalid_port")

    try:
        raw_pairs = parse_qsl(
            parsed.query,
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=MAX_QUERY_FIELDS,
        )
    except (ValueError, TypeError) as exc:
        raise EmergencyCatalogSourceError("malformed_query") from exc
    query: dict[str, str] = {}
    for raw_key, raw_value in raw_pairs:
        key = _canonical_query_key(raw_key)
        if not key:
            raise EmergencyCatalogSourceError("malformed_query")
        if key in query:
            raise EmergencyCatalogSourceError("duplicate_query_key")
        query[key] = raw_value.strip()

    insecure_keys = {"allowinsecure", "insecure", "skiptlsverify"}
    if insecure_keys.intersection(query):
        raise EmergencyCatalogSourceError("insecure_not_allowed")

    transport_raw = query.get("type", "tcp").strip().lower()
    if transport_raw not in _SUPPORTED_TRANSPORTS:
        raise EmergencyCatalogSourceError("unsupported_transport")
    transport = "tcp" if transport_raw in {"tcp", "raw"} else transport_raw
    allowed_keys = _COMMON_QUERY_KEYS | _TRANSPORT_QUERY_KEYS[transport]
    if set(query).difference(allowed_keys):
        raise EmergencyCatalogSourceError("unknown_query_key")

    if query.get("security", "").strip().lower() != "reality":
        raise EmergencyCatalogSourceError("reality_required")
    encryption = query.get("encryption", "none").strip().lower()
    if encryption != "none":
        raise EmergencyCatalogSourceError("invalid_encryption")

    flow = query.get("flow", "").strip().lower()
    if flow not in {"", "xtls-rprx-vision"}:
        raise EmergencyCatalogSourceError("unsupported_flow")
    if transport == "grpc" and flow:
        raise EmergencyCatalogSourceError("flow_transport_conflict")
    if transport == "grpc" and query.get("mode", "gun").strip().lower() != "gun":
        raise EmergencyCatalogSourceError("unsupported_grpc_mode")
    if transport == "tcp" and query.get("headertype", "none").strip().lower() not in {"", "none"}:
        raise EmergencyCatalogSourceError("unsupported_tcp_header")

    fingerprint = query.get("fp", "").strip().lower()
    if fingerprint not in _SUPPORTED_FINGERPRINTS:
        raise EmergencyCatalogSourceError("unsupported_fingerprint")

    server_name = _normalize_dns_name(query.get("sni", ""))
    public_key = _normalize_public_key(query.get("pbk", ""))
    short_id = _normalize_short_id(query.get("sid", ""))

    grpc_service_name = ""
    if transport == "grpc":
        service_values = [query[key] for key in ("servicename", "path") if query.get(key)]
        if len(service_values) != 1 or not _GRPC_SERVICE_RE.fullmatch(service_values[0]):
            raise EmergencyCatalogSourceError("invalid_grpc_service")
        grpc_service_name = service_values[0]

    canonical_material: dict[str, object] = {
        "contract": SOURCE_CONTRACT,
        "transport": transport,
        "endpoint_host": endpoint_host,
        "endpoint_port": endpoint_port,
        "user_uuid": user_uuid,
        "server_name": server_name,
        "reality_public_key": public_key,
        "reality_short_id": short_id,
        "fingerprint": fingerprint,
        "flow": flow,
        "grpc_service_name": grpc_service_name,
    }
    return EmergencyEndpointMaterial(
        stable_id=_stable_id(canonical_material),
        transport=transport,
        endpoint_host=endpoint_host,
        endpoint_port=endpoint_port,
        user_uuid=user_uuid,
        server_name=server_name,
        reality_public_key=public_key,
        reality_short_id=short_id,
        fingerprint=fingerprint,
        flow=flow,
        grpc_service_name=grpc_service_name,
    )


def parse_emergency_source(payload: bytes | str) -> EmergencySourceParseResult:
    """Parse a bounded source payload without retaining or echoing rejected rows."""

    if isinstance(payload, str):
        encoded = payload.encode("utf-8")
    elif isinstance(payload, bytes):
        encoded = payload
    else:
        raise EmergencyCatalogSourceError("invalid_source_type")
    if len(encoded) > MAX_SOURCE_BYTES:
        raise EmergencyCatalogSourceError("source_too_large")
    try:
        text = encoded.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise EmergencyCatalogSourceError("invalid_source_encoding") from exc

    lines = text.splitlines()
    if len(lines) > MAX_SOURCE_LINES:
        raise EmergencyCatalogSourceError("too_many_source_lines")

    accepted: list[EmergencyEndpointMaterial] = []
    rejected: list[EmergencySourceRejection] = []
    seen_ids: set[str] = set()
    candidate_line_count = 0
    for line_number, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue
        candidate_line_count += 1
        if len(stripped.encode("utf-8")) > MAX_LINE_BYTES:
            rejected.append(EmergencySourceRejection(line_number, "source_line_too_long"))
            continue
        try:
            material = _parse_candidate(stripped)
        except EmergencyCatalogSourceError as exc:
            rejected.append(EmergencySourceRejection(line_number, exc.code))
            continue
        if material.stable_id in seen_ids:
            rejected.append(EmergencySourceRejection(line_number, "duplicate_endpoint"))
            continue
        seen_ids.add(material.stable_id)
        accepted.append(material)

    return EmergencySourceParseResult(tuple(accepted), tuple(rejected), candidate_line_count)


def select_verified_non_ru_candidates(
    candidates: tuple[EmergencyEndpointMaterial, ...],
    verifications: Mapping[str, EndpointVerification],
    *,
    now: datetime | None = None,
    max_verification_age: timedelta = timedelta(hours=24),
) -> VerifiedCandidateSelection:
    """Apply trusted exit verification; source-provided geography is ignored."""

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise EmergencyCatalogSourceError("verification_clock_not_utc")
    accepted: list[EmergencyEndpointMaterial] = []
    rejected: list[EmergencySourceRejection] = []
    for ordinal, candidate in enumerate(candidates, start=1):
        verification = verifications.get(candidate.stable_id)
        if verification is None:
            rejected.append(EmergencySourceRejection(ordinal, "exit_unverified"))
            continue
        verified_at = verification.verified_at
        if verified_at.tzinfo is None:
            rejected.append(EmergencySourceRejection(ordinal, "verification_time_invalid"))
            continue
        if verified_at > current + timedelta(minutes=5):
            rejected.append(EmergencySourceRejection(ordinal, "verification_from_future"))
            continue
        if current - verified_at > max_verification_age:
            rejected.append(EmergencySourceRejection(ordinal, "verification_stale"))
            continue
        country_code = verification.country_code.strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", country_code):
            rejected.append(EmergencySourceRejection(ordinal, "exit_country_invalid"))
            continue
        if country_code == "RU":
            rejected.append(EmergencySourceRejection(ordinal, "exit_country_ru"))
            continue
        accepted.append(candidate)
    return VerifiedCandidateSelection(tuple(accepted), tuple(rejected))
