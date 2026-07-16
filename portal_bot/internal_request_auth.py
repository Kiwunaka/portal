from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import stat
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping


_KEYS_FILE_ENV = "INTERNAL_HMAC_KEYS_FILE"
_MAX_BODY_BYTES = 512 * 1024
_MAX_CLOCK_SKEW_SECONDS = 300
_NONCE_TTL = timedelta(hours=24)
_MAX_REGISTRY_BYTES = 64 * 1024
_HTTP_METHOD_RE = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+\Z")
_KEY_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_REGISTRY_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}\Z")
_SCOPE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,63}\Z")
_TIMESTAMP_RE = re.compile(r"(?:0|[1-9][0-9]{0,10})\Z")
_SIGNATURE_RE = re.compile(r"[0-9a-f]{64}\Z")
_REQUIRED_HEADERS = (
    "x-internal-key-id",
    "x-internal-timestamp",
    "x-internal-nonce",
    "x-internal-signature",
)


class InternalAuthError(RuntimeError):
    __slots__ = ("status_code", "code")

    def __init__(self, status_code: int, code: str) -> None:
        self.status_code = int(status_code)
        self.code = str(code)
        super().__init__(self.code)


@dataclass(frozen=True)
class InternalServiceKey:
    key_id: str
    secret: bytes
    subject: str
    scopes: frozenset[str]
    origins: frozenset[str]
    enabled: bool


@dataclass(frozen=True)
class AuthenticatedInternalRequest:
    key_id: str
    subject: str
    nonce: str
    request_timestamp: datetime
    body_sha256: str


def _canonical_method(method: str) -> str:
    if (
        not isinstance(method, str)
        or not method
        or len(method) > 32
        or _HTTP_METHOD_RE.fullmatch(method) is None
        or method != method.upper()
    ):
        raise ValueError("invalid HTTP method")
    return method


def _is_visible_ascii(value: object, *, maximum: int) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= maximum
        and all(0x21 <= ord(character) <= 0x7E for character in value)
    )


def _canonical_timestamp(timestamp: str) -> str:
    if not isinstance(timestamp, str) or _TIMESTAMP_RE.fullmatch(timestamp) is None:
        raise ValueError("invalid Unix timestamp")
    return timestamp


def _canonical_nonce(nonce: str) -> str:
    if not _is_visible_ascii(nonce, maximum=128):
        raise ValueError("invalid request nonce")
    return nonce


def normalize_signed_path(path: str) -> str:
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("signed path must be absolute")
    if "?" in path or "#" in path or "\\" in path or "%" in path:
        raise ValueError("signed path is ambiguous")
    if any(
        character.isspace()
        or unicodedata.category(character).startswith("C")
        for character in path
    ):
        raise ValueError("signed path contains an unsafe character")

    segments = path.split("/")
    if any(segment in {".", ".."} for segment in segments):
        raise ValueError("signed path contains a dot segment")
    normalized = "/" + "/".join(segment for segment in segments if segment)
    if len(normalized.encode("utf-8")) > 512:
        raise ValueError("signed path is too long")
    return normalized


def signature_preimage(
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    raw_body: bytes,
) -> bytes:
    if not isinstance(raw_body, bytes):
        raise TypeError("raw_body must be bytes")
    canonical_method = _canonical_method(method)
    canonical_path = normalize_signed_path(path)
    canonical_timestamp = _canonical_timestamp(timestamp)
    canonical_nonce = _canonical_nonce(nonce)
    prefix = (
        f"{canonical_method}\n{canonical_path}\n"
        f"{canonical_timestamp}\n{canonical_nonce}\n"
    ).encode("utf-8")
    return prefix + raw_body


def sign_internal_request(
    secret: bytes,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    raw_body: bytes,
) -> str:
    if not isinstance(secret, bytes):
        raise TypeError("secret must be bytes")
    if not secret:
        raise ValueError("secret must not be empty")
    return hmac.new(
        secret,
        signature_preimage(method, path, timestamp, nonce, raw_body),
        hashlib.sha256,
    ).hexdigest()


def _invalid_registry() -> InternalAuthError:
    return InternalAuthError(500, "invalid_key_registry")


def _registry_identifier(value: object) -> str:
    if not isinstance(value, str) or _REGISTRY_ID_RE.fullmatch(value) is None:
        raise _invalid_registry()
    return value


def _registry_values(value: object, *, pattern=_REGISTRY_ID_RE) -> frozenset[str]:
    if (
        not isinstance(value, list)
        or not value
        or len(value) > 32
        or not all(isinstance(item, str) for item in value)
    ):
        raise _invalid_registry()
    if any(pattern.fullmatch(item) is None for item in value):
        raise _invalid_registry()
    normalized = frozenset(value)
    if len(normalized) != len(value):
        raise _invalid_registry()
    return normalized


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate JSON member")
        result[name] = value
    return result


def load_internal_service_key_registry() -> dict[str, InternalServiceKey]:
    configured_path = os.environ.get(_KEYS_FILE_ENV)
    if not configured_path:
        raise InternalAuthError(500, "key_registry_unavailable")

    try:
        path = Path(configured_path)
        with path.open("rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise OSError
            raw_registry = handle.read(_MAX_REGISTRY_BYTES + 1)
        if not raw_registry or len(raw_registry) > _MAX_REGISTRY_BYTES:
            raise ValueError("invalid registry size")
        payload = json.loads(
            raw_registry.decode("utf-8"),
            object_pairs_hook=_unique_json_object,
        )
    except (OSError, UnicodeError):
        raise InternalAuthError(500, "key_registry_unavailable") from None
    except (TypeError, ValueError):
        raise _invalid_registry() from None

    try:
        if not isinstance(payload, dict) or set(payload) != {"keys"}:
            raise _invalid_registry()
        entries = payload["keys"]
        if not isinstance(entries, list) or not entries or len(entries) > 128:
            raise _invalid_registry()

        registry: dict[str, InternalServiceKey] = {}
        expected_fields = {
            "key_id",
            "secret",
            "subject",
            "scopes",
            "origins",
            "enabled",
        }
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != expected_fields:
                raise _invalid_registry()
            key_id = entry["key_id"]
            if not isinstance(key_id, str) or _KEY_ID_RE.fullmatch(key_id) is None:
                raise _invalid_registry()
            secret_text = entry["secret"]
            if not isinstance(secret_text, str):
                raise _invalid_registry()
            secret = secret_text.encode("utf-8")
            if not 16 <= len(secret) <= 512:
                raise _invalid_registry()
            enabled = entry["enabled"]
            if not isinstance(enabled, bool):
                raise _invalid_registry()
            if key_id in registry:
                raise _invalid_registry()
            registry[key_id] = InternalServiceKey(
                key_id=key_id,
                secret=secret,
                subject=_registry_identifier(entry["subject"]),
                scopes=_registry_values(entry["scopes"], pattern=_SCOPE_RE),
                origins=_registry_values(entry["origins"]),
                enabled=enabled,
            )
        return registry
    except InternalAuthError:
        raise
    except (TypeError, ValueError):
        raise _invalid_registry() from None


def _auth_headers(headers: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(headers, Mapping):
        raise InternalAuthError(401, "malformed_auth_header")
    normalized: dict[str, str] = {}
    for name, value in headers.items():
        if not isinstance(name, str):
            raise InternalAuthError(401, "malformed_auth_header")
        lowercase_name = name.lower()
        if lowercase_name not in _REQUIRED_HEADERS:
            continue
        if lowercase_name in normalized or not isinstance(value, str):
            raise InternalAuthError(401, "malformed_auth_header")
        normalized[lowercase_name] = value
    if any(name not in normalized for name in _REQUIRED_HEADERS):
        raise InternalAuthError(401, "missing_auth_header")
    return normalized


def _utc_now(now: datetime) -> datetime:
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise InternalAuthError(500, "invalid_auth_clock")
    return now.astimezone(timezone.utc)


def _ensure_sqlite_outer_transaction(session):
    connection = session.connection()
    bind = session.get_bind()
    if getattr(getattr(bind, "dialect", None), "name", None) != "sqlite":
        return connection
    proxied = getattr(connection, "connection", None)
    driver_connection = getattr(proxied, "driver_connection", proxied)
    if driver_connection is not None and not bool(
        getattr(driver_connection, "in_transaction", True)
    ):
        connection.exec_driver_sql("BEGIN")
    return connection


def _is_replayed_nonce_integrity_error(error) -> bool:
    original = getattr(error, "orig", None)
    diagnostic = getattr(original, "diag", None)
    constraint_name = getattr(diagnostic, "constraint_name", None)
    if constraint_name is not None:
        return constraint_name == "uq_internal_ingest_nonce_scope_key_hash"
    return str(original) == (
        "UNIQUE constraint failed: internal_ingest_nonces.key_scope, "
        "internal_ingest_nonces.key_id, internal_ingest_nonces.nonce_hash"
    )


def _consume_nonce(
    session,
    *,
    key_scope: str,
    key_id: str,
    nonce_hash: str,
    request_path: str,
    request_timestamp: datetime,
    body_sha256: str,
    expires_at: datetime,
) -> None:
    from sqlalchemy.exc import IntegrityError

    try:
        from models import InternalIngestNonce
    except ImportError:
        from .models import InternalIngestNonce

    connection = _ensure_sqlite_outer_transaction(session)
    try:
        with connection.begin_nested():
            connection.execute(
                InternalIngestNonce.__table__.insert().values(
                    key_scope=key_scope,
                    key_id=key_id,
                    nonce_hash=nonce_hash,
                    request_path=request_path,
                    request_timestamp=request_timestamp,
                    body_sha256=body_sha256,
                    expires_at=expires_at,
                )
            )
    except IntegrityError as error:
        if _is_replayed_nonce_integrity_error(error):
            raise InternalAuthError(409, "replayed_nonce") from None
        raise


def authenticate_internal_request(
    session,
    registry,
    *,
    method,
    path,
    raw_body,
    headers,
    required_scope,
    required_origin,
    now,
) -> AuthenticatedInternalRequest:
    if not isinstance(raw_body, bytes):
        raise InternalAuthError(400, "invalid_body")
    if len(raw_body) > _MAX_BODY_BYTES:
        raise InternalAuthError(413, "body_too_large")

    try:
        canonical_method = _canonical_method(method)
    except (TypeError, ValueError):
        raise InternalAuthError(400, "invalid_method") from None
    try:
        canonical_path = normalize_signed_path(path)
    except (TypeError, ValueError):
        raise InternalAuthError(400, "invalid_signed_path") from None

    if (
        not isinstance(required_scope, str)
        or _SCOPE_RE.fullmatch(required_scope) is None
        or not isinstance(required_origin, str)
        or _REGISTRY_ID_RE.fullmatch(required_origin) is None
    ):
        raise InternalAuthError(500, "invalid_auth_requirement")

    supplied = _auth_headers(headers)
    key_id = supplied["x-internal-key-id"]
    timestamp = supplied["x-internal-timestamp"]
    nonce = supplied["x-internal-nonce"]
    signature = supplied["x-internal-signature"]
    if (
        _KEY_ID_RE.fullmatch(key_id) is None
        or _TIMESTAMP_RE.fullmatch(timestamp) is None
        or not _is_visible_ascii(nonce, maximum=128)
        or _SIGNATURE_RE.fullmatch(signature) is None
    ):
        raise InternalAuthError(401, "malformed_auth_header")

    now_utc = _utc_now(now)
    try:
        timestamp_seconds = int(timestamp)
        request_timestamp = datetime.fromtimestamp(
            timestamp_seconds, tz=timezone.utc
        )
    except (OverflowError, OSError, ValueError):
        raise InternalAuthError(401, "malformed_auth_header") from None
    if abs(now_utc.timestamp() - timestamp_seconds) > _MAX_CLOCK_SKEW_SECONDS:
        raise InternalAuthError(401, "stale_timestamp")

    if not isinstance(registry, Mapping):
        raise InternalAuthError(500, "invalid_key_registry")
    key = registry.get(key_id)
    if key is None:
        raise InternalAuthError(401, "unknown_key")
    if not isinstance(key, InternalServiceKey) or key.key_id != key_id:
        raise InternalAuthError(500, "invalid_key_registry")
    if not key.enabled:
        raise InternalAuthError(401, "disabled_key")
    if required_scope not in key.scopes:
        raise InternalAuthError(403, "forbidden_scope")
    if required_origin not in key.origins:
        raise InternalAuthError(403, "forbidden_origin")

    try:
        expected_signature = sign_internal_request(
            key.secret,
            canonical_method,
            canonical_path,
            timestamp,
            nonce,
            raw_body,
        )
    except (TypeError, ValueError):
        raise InternalAuthError(500, "invalid_key_registry") from None
    if not hmac.compare_digest(expected_signature, signature):
        raise InternalAuthError(401, "invalid_signature")

    body_sha256 = hashlib.sha256(raw_body).hexdigest()
    _consume_nonce(
        session,
        key_scope=required_scope,
        key_id=key.key_id,
        nonce_hash=hashlib.sha256(nonce.encode("utf-8")).hexdigest(),
        request_path=canonical_path,
        request_timestamp=request_timestamp,
        body_sha256=body_sha256,
        expires_at=now_utc + _NONCE_TTL,
    )
    return AuthenticatedInternalRequest(
        key_id=key.key_id,
        subject=key.subject,
        nonce=nonce,
        request_timestamp=request_timestamp,
        body_sha256=body_sha256,
    )
