"""Signed, one-time and strictly bounded temporary support mode.

The policy contains data-collection allowlists only.  It has no command,
filesystem, routing, DNS, packet-capture or remote-control surface.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any, Mapping

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

try:
    from .models import SupportModePolicy, SupportTicket
except ImportError:
    from models import SupportModePolicy, SupportTicket


SUPPORT_MODE_CATEGORIES = frozenset(
    {"build", "crashes", "events", "network", "redaction", "system"}
)
SUPPORT_MODE_COLLECTORS = frozenset(
    {
        "build_summary",
        "crash_index",
        "network_summary",
        "operational_events",
        "redaction_report",
        "system_summary",
    }
)
SUPPORT_MODE_PLATFORMS = frozenset({"android", "windows"})
MAXIMUM_POLICY_TTL = timedelta(minutes=30)
MINIMUM_BUNDLE_BYTES = 64 * 1024
MAXIMUM_BUNDLE_BYTES = 2 * 1024 * 1024
MAXIMUM_TOTAL_BYTES = 4 * 1024 * 1024
MAXIMUM_BUNDLES = 2

_CATEGORY_COLLECTOR = {
    "build": "build_summary",
    "crashes": "crash_index",
    "events": "operational_events",
    "network": "network_summary",
    "redaction": "redaction_report",
    "system": "system_summary",
}
_KEY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:\+[0-9]+)?$")
_BUILD_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,79}$")
_POLICY_ID_RE = re.compile(r"^spol-[0-9a-f]{24}$")
_NONCE_RE = re.compile(r"^[A-Za-z0-9_-]{22}$")
_ACTIVATION_CODE_RE = re.compile(r"^PSM1-[0-9A-HJKMNPQRSTVWXYZ]{4}-[0-9A-HJKMNPQRSTVWXYZ]{4}$")
_DIAGNOSTIC_CODE_RE = re.compile(
    r"^PSD1-([0-9A-HJKMNPQRSTVWXYZ]{4})-([0-9A-HJKMNPQRSTVWXYZ]{4})-"
    r"([0-9A-HJKMNPQRSTVWXYZ]{4})-([0-9A-HJKMNPQRSTVWXYZ]{4})$"
)
_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_CROCKFORD_DECODE = {char: index for index, char in enumerate(_CROCKFORD)}
_DIAGNOSTIC_EPOCH = date(2020, 1, 1)
_DIAGNOSTIC_MAX_AGE_DAYS = 14
_ROUTE_MODES = ("full_tunnel", "all_except_ru", "selected_apps", "excluded_apps")
_CONNECTION_STATES = (
    "disconnected",
    "connecting",
    "verified",
    "degraded",
    "blocked",
)


class SupportModeError(RuntimeError):
    def __init__(self, code: str, *, status_code: int = 422) -> None:
        self.code = code
        self.status_code = int(status_code)
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class SupportModeIssueSpec:
    platform: str
    app_version: str
    build_number: str
    allowed_categories: tuple[str, ...]
    allowed_collectors: tuple[str, ...]
    ttl_minutes: int
    maximum_bundle_bytes: int
    maximum_total_bytes: int
    maximum_bundles: int


@dataclass(frozen=True, slots=True)
class IssuedSupportMode:
    row: SupportModePolicy
    activation_code: str


@dataclass(frozen=True, slots=True)
class RedeemedSupportMode:
    row: SupportModePolicy
    signed_policy: dict[str, str | int]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(microsecond=0)
    return value.astimezone(timezone.utc).replace(tzinfo=None, microsecond=0)


def _iso(value: datetime) -> str:
    return _as_naive_utc(value).replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_b64url(value: object, *, exact_bytes: int, code: str) -> bytes:
    raw = str(value or "").strip()
    try:
        decoded = base64.b64decode(
            raw + "=" * ((4 - len(raw) % 4) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError, binascii.Error) as exc:
        raise SupportModeError(code, status_code=503) from exc
    if len(decoded) != exact_bytes:
        raise SupportModeError(code, status_code=503)
    return decoded


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(payload),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SupportModeError("support_mode_policy_invalid", status_code=503) from exc


@dataclass(frozen=True, slots=True)
class SupportModeSigner:
    key_id: str
    private_key: Ed25519PrivateKey

    @classmethod
    def from_environment(cls) -> "SupportModeSigner":
        key_id = str(os.getenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID") or "").strip().lower()
        if _KEY_ID_RE.fullmatch(key_id) is None:
            raise SupportModeError("support_mode_signing_unavailable", status_code=503)
        raw = _decode_b64url(
            os.getenv("POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64"),
            exact_bytes=32,
            code="support_mode_signing_unavailable",
        )
        try:
            private_key = Ed25519PrivateKey.from_private_bytes(raw)
        except ValueError as exc:
            raise SupportModeError("support_mode_signing_unavailable", status_code=503) from exc
        return cls(key_id=key_id, private_key=private_key)

    def envelope(self, payload: Mapping[str, Any]) -> dict[str, str | int]:
        payload_bytes = _canonical_bytes(payload)
        return {
            "algorithm": "Ed25519",
            "key_id": self.key_id,
            "payload_b64": _b64url(payload_bytes),
            "schema_version": 1,
            "signature_b64": _b64url(self.private_key.sign(payload_bytes)),
        }


def _code_secret() -> bytes:
    value = str(os.getenv("POKROV_SUPPORT_MODE_CODE_SECRET") or "").encode("utf-8")
    if len(value) < 32:
        raise SupportModeError("support_mode_code_unavailable", status_code=503)
    return value


def _crockford_from_int(value: int, length: int) -> str:
    chars = ["0"] * length
    for index in range(length - 1, -1, -1):
        chars[index] = _CROCKFORD[value & 31]
        value >>= 5
    return "".join(chars)


def activation_code_for_policy_id(policy_id: str) -> str:
    normalized = str(policy_id or "").strip().lower()
    if _POLICY_ID_RE.fullmatch(normalized) is None:
        raise SupportModeError("support_mode_policy_id_invalid", status_code=503)
    digest = hmac.new(
        _code_secret(),
        f"POKROV:support-mode-code:v1:{normalized}".encode("ascii"),
        hashlib.sha256,
    ).digest()
    token = _crockford_from_int(int.from_bytes(digest[:5], "big"), 8)
    return f"PSM1-{token[:4]}-{token[4:]}"


def normalize_activation_code(value: object) -> str:
    raw = re.sub(r"[\s-]+", "", str(value or "").upper())
    normalized = f"{raw[:4]}-{raw[4:8]}-{raw[8:12]}" if len(raw) == 12 else ""
    if _ACTIVATION_CODE_RE.fullmatch(normalized) is None:
        raise SupportModeError("support_mode_code_invalid")
    return normalized


def activation_code_hash(value: object) -> str:
    normalized = normalize_activation_code(value)
    return hashlib.sha256(normalized.encode("ascii")).hexdigest()


def _bounded_int(value: object, *, minimum: int, maximum: int, code: str) -> int:
    if type(value) is not int or not minimum <= int(value) <= maximum:
        raise SupportModeError(code)
    return int(value)


def _closed_list(value: object, *, allowed: frozenset[str], code: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or len(value) > len(allowed):
        raise SupportModeError(code)
    normalized = tuple(sorted(str(item or "").strip().lower() for item in value))
    if len(set(normalized)) != len(normalized) or not set(normalized).issubset(allowed):
        raise SupportModeError(code)
    return normalized


def normalize_issue_spec(payload: Mapping[str, Any]) -> SupportModeIssueSpec:
    allowed_fields = {
        "allowed_categories",
        "allowed_collectors",
        "app_version",
        "build_number",
        "maximum_bundle_bytes",
        "maximum_bundles",
        "maximum_total_bytes",
        "platform",
        "ttl_minutes",
    }
    if set(payload) != allowed_fields:
        raise SupportModeError("support_mode_issue_shape_invalid")
    platform = str(payload.get("platform") or "").strip().lower()
    app_version = str(payload.get("app_version") or "").strip()
    build_number = str(payload.get("build_number") or "").strip()
    if platform not in SUPPORT_MODE_PLATFORMS:
        raise SupportModeError("support_mode_platform_invalid")
    if _VERSION_RE.fullmatch(app_version) is None:
        raise SupportModeError("support_mode_app_version_invalid")
    if _BUILD_RE.fullmatch(build_number) is None:
        raise SupportModeError("support_mode_build_invalid")
    categories = _closed_list(
        payload.get("allowed_categories"),
        allowed=SUPPORT_MODE_CATEGORIES,
        code="support_mode_categories_invalid",
    )
    collectors = _closed_list(
        payload.get("allowed_collectors"),
        allowed=SUPPORT_MODE_COLLECTORS,
        code="support_mode_collectors_invalid",
    )
    required_collectors = {_CATEGORY_COLLECTOR[category] for category in categories}
    if set(collectors) != required_collectors:
        raise SupportModeError("support_mode_collectors_invalid")
    maximum_bundle_bytes = _bounded_int(
        payload.get("maximum_bundle_bytes"),
        minimum=MINIMUM_BUNDLE_BYTES,
        maximum=MAXIMUM_BUNDLE_BYTES,
        code="support_mode_bundle_budget_invalid",
    )
    maximum_total_bytes = _bounded_int(
        payload.get("maximum_total_bytes"),
        minimum=maximum_bundle_bytes,
        maximum=MAXIMUM_TOTAL_BYTES,
        code="support_mode_total_budget_invalid",
    )
    return SupportModeIssueSpec(
        platform=platform,
        app_version=app_version,
        build_number=build_number,
        allowed_categories=categories,
        allowed_collectors=collectors,
        ttl_minutes=_bounded_int(
            payload.get("ttl_minutes"),
            minimum=1,
            maximum=30,
            code="support_mode_ttl_invalid",
        ),
        maximum_bundle_bytes=maximum_bundle_bytes,
        maximum_total_bytes=maximum_total_bytes,
        maximum_bundles=_bounded_int(
            payload.get("maximum_bundles"),
            minimum=1,
            maximum=MAXIMUM_BUNDLES,
            code="support_mode_bundle_count_invalid",
        ),
    )


def issue_support_mode(
    session,
    *,
    ticket: SupportTicket,
    spec: SupportModeIssueSpec,
    actor_tg_id: int,
    now: datetime | None = None,
) -> IssuedSupportMode:
    SupportModeSigner.from_environment()
    _code_secret()
    instant = _as_naive_utc(now or _utcnow())
    row_id = str(uuid.uuid4())
    policy_id = f"spol-{uuid.UUID(row_id).hex[:24]}"
    activation_code = activation_code_for_policy_id(policy_id)
    row = SupportModePolicy(
        id=row_id,
        policy_id=policy_id,
        ticket_id=int(ticket.id),
        owner_tg_id=int(ticket.user_tg_id),
        owner_account_id=str(ticket.account_id or "").strip() or None,
        environment=str(ticket.environment or "production"),
        platform=spec.platform,
        app_version=spec.app_version,
        build_number=spec.build_number,
        allowed_categories_json=json.dumps(list(spec.allowed_categories), separators=(",", ":")),
        allowed_collectors_json=json.dumps(list(spec.allowed_collectors), separators=(",", ":")),
        maximum_bundle_bytes=spec.maximum_bundle_bytes,
        maximum_total_bytes=spec.maximum_total_bytes,
        maximum_bundles=spec.maximum_bundles,
        nonce=_b64url(os.urandom(16)),
        activation_code_hash=activation_code_hash(activation_code),
        status="issued",
        created_by_tg_id=int(actor_tg_id),
        issued_at=instant,
        expires_at=instant + timedelta(minutes=spec.ttl_minutes),
        created_at=instant,
        updated_at=instant,
    )
    session.add(row)
    session.flush()
    return IssuedSupportMode(row=row, activation_code=activation_code)


def _owned(row: SupportModePolicy, *, owner_tg_id: int, owner_account_id: str | None) -> bool:
    policy_account = str(row.owner_account_id or "").strip()
    actor_account = str(owner_account_id or "").strip()
    if policy_account:
        return hmac.compare_digest(policy_account, actor_account)
    return int(row.owner_tg_id) == int(owner_tg_id)


def _policy_payload(row: SupportModePolicy) -> dict[str, Any]:
    categories = json.loads(str(row.allowed_categories_json))
    collectors = json.loads(str(row.allowed_collectors_json))
    return {
        "allowed_categories": categories,
        "allowed_collectors": collectors,
        "audience": {
            "app_version": str(row.app_version),
            "build_number": str(row.build_number),
            "platform": str(row.platform),
        },
        "expires_at": _iso(row.expires_at),
        "issued_at": _iso(row.issued_at),
        "maximum_bundle_bytes": int(row.maximum_bundle_bytes),
        "maximum_bundles": int(row.maximum_bundles),
        "maximum_total_bytes": int(row.maximum_total_bytes),
        "nonce": str(row.nonce),
        "policy_id": str(row.policy_id),
        "profile": "extended",
        "schema_version": 2,
        "type": "pokrov.support.collection_policy",
    }


def redeem_support_mode(
    session,
    *,
    activation_code: object,
    owner_tg_id: int,
    owner_account_id: str | None,
    platform: object,
    app_version: object,
    build_number: object,
    now: datetime | None = None,
) -> RedeemedSupportMode:
    code_hash = activation_code_hash(activation_code)
    query = session.query(SupportModePolicy).filter(
        SupportModePolicy.activation_code_hash == code_hash
    )
    if str(session.get_bind().dialect.name) == "postgresql":
        query = query.with_for_update()
    row = query.one_or_none()
    if row is None or not _owned(
        row,
        owner_tg_id=int(owner_tg_id),
        owner_account_id=owner_account_id,
    ):
        raise SupportModeError("support_mode_code_not_found", status_code=404)
    instant = _as_naive_utc(now or _utcnow())
    if str(row.status) != "issued":
        raise SupportModeError("support_mode_code_consumed", status_code=409)
    if instant >= _as_naive_utc(row.expires_at):
        raise SupportModeError("support_mode_code_expired", status_code=410)
    audience = (
        str(platform or "").strip().lower(),
        str(app_version or "").strip(),
        str(build_number or "").strip(),
    )
    if audience != (str(row.platform), str(row.app_version), str(row.build_number)):
        raise SupportModeError("support_mode_audience_mismatch", status_code=409)
    signer = SupportModeSigner.from_environment()
    envelope = signer.envelope(_policy_payload(row))
    claimed = (
        session.query(SupportModePolicy)
        .filter(
            SupportModePolicy.id == row.id,
            SupportModePolicy.status == "issued",
            SupportModePolicy.expires_at > instant,
        )
        .update(
            {
                SupportModePolicy.status: "redeemed",
                SupportModePolicy.redeemed_at: instant,
                SupportModePolicy.updated_at: instant,
            },
            synchronize_session=False,
        )
    )
    if claimed != 1:
        raise SupportModeError("support_mode_code_consumed", status_code=409)
    row.status = "redeemed"
    row.redeemed_at = instant
    row.updated_at = instant
    return RedeemedSupportMode(row=row, signed_policy=envelope)


def support_mode_public_view(row: SupportModePolicy) -> dict[str, Any]:
    return {
        "policy_id": str(row.policy_id),
        "ticket_id": int(row.ticket_id),
        "platform": str(row.platform),
        "app_version": str(row.app_version),
        "build_number": str(row.build_number),
        "allowed_categories": json.loads(str(row.allowed_categories_json)),
        "allowed_collectors": json.loads(str(row.allowed_collectors_json)),
        "maximum_bundle_bytes": int(row.maximum_bundle_bytes),
        "maximum_total_bytes": int(row.maximum_total_bytes),
        "maximum_bundles": int(row.maximum_bundles),
        "status": str(row.status),
        "issued_at": _iso(row.issued_at),
        "expires_at": _iso(row.expires_at),
    }


def _crc8(value: bytes) -> int:
    crc = 0
    for byte in value:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def _crockford_decode(value: str) -> bytes:
    accumulator = 0
    bits = 0
    output = bytearray()
    for char in value:
        digit = _CROCKFORD_DECODE.get(char)
        if digit is None:
            raise SupportModeError("support_diagnostic_code_invalid")
        accumulator = (accumulator << 5) | digit
        bits += 5
        while bits >= 8:
            bits -= 8
            output.append((accumulator >> bits) & 0xFF)
            accumulator &= (1 << bits) - 1
    if bits and accumulator:
        raise SupportModeError("support_diagnostic_code_invalid")
    return bytes(output)


def decode_diagnostic_code(value: object, *, today: date | None = None) -> dict[str, Any]:
    raw = re.sub(r"[\s-]+", "", str(value or "").upper())
    normalized = (
        f"PSD1-{raw[4:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}"
        if len(raw) == 20 and raw.startswith("PSD1")
        else ""
    )
    match = _DIAGNOSTIC_CODE_RE.fullmatch(normalized)
    if match is None:
        raise SupportModeError("support_diagnostic_code_invalid")
    packed = _crockford_decode("".join(match.groups()))
    if len(packed) != 10 or _crc8(packed[:9]) != packed[9]:
        raise SupportModeError("support_diagnostic_code_invalid")
    facts = packed[0]
    platform_index = (facts >> 5) & 0x01
    route_index = (facts >> 3) & 0x03
    state_index = facts & 0x07
    if state_index >= len(_CONNECTION_STATES):
        raise SupportModeError("support_diagnostic_code_invalid")
    issued_on = _DIAGNOSTIC_EPOCH + timedelta(days=int.from_bytes(packed[1:3], "big"))
    expires_on = issued_on + timedelta(days=_DIAGNOSTIC_MAX_AGE_DAYS)
    current = today or datetime.now(timezone.utc).date()
    return {
        "schema_version": 1,
        "platform": ("android", "windows")[platform_index],
        "route_mode": _ROUTE_MODES[route_index],
        "connection_state": _CONNECTION_STATES[state_index],
        "app_version": f"{packed[3]}.{packed[4]}.{packed[5]}",
        "build_number": int(packed[6]),
        "diagnostic_hash_prefix": packed[7:9].hex(),
        "issued_on": issued_on.isoformat(),
        "expires_on": expires_on.isoformat(),
        "expired": current > expires_on,
        "contains_identity": False,
    }


__all__ = [
    "IssuedSupportMode",
    "RedeemedSupportMode",
    "SupportModeError",
    "SupportModeIssueSpec",
    "activation_code_for_policy_id",
    "decode_diagnostic_code",
    "issue_support_mode",
    "normalize_issue_spec",
    "redeem_support_mode",
    "support_mode_public_view",
]
