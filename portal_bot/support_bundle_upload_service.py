"""Case-bound resumable storage for opaque encrypted support bundles.

This module never decrypts or interprets bundle content. It validates only the
upload contract and writes fixed-name ciphertext chunks into private quarantine.
Decryption and payload validation belong to ``support_bundle_ingest_service``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from sqlalchemy.exc import IntegrityError

try:
    from .models import (
        SupportBundleChunk,
        SupportBundleUpload,
        SupportTicket,
        SupportTicketMessage,
    )
except ImportError:
    from models import (
        SupportBundleChunk,
        SupportBundleUpload,
        SupportTicket,
        SupportTicketMessage,
    )


SUPPORT_BUNDLE_CONTENT_TYPE = "application/vnd.pokrov.support-bundle+json"
MAX_BUNDLE_BYTES = 2_621_440
MAX_CHUNK_BYTES = 262_144
MAX_CHUNKS = 16
DEFAULT_TICKET_TTL = timedelta(minutes=15)

_BUNDLE_ID = re.compile(r"^diag-[a-f0-9]{24}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._-]{8,64}$")
_ANONYMOUS_NONCE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
_TOKEN_FIELDS = frozenset(
    {
        "bundle_id",
        "content_type",
        "exp",
        "owner_binding_hash",
        "sha256",
        "size_bytes",
        "upload_id",
        "version",
    }
)
_FORBIDDEN_SUMMARY = (
    "://",
    "authorization",
    "bearer ",
    "private-key",
    "refresh_token",
    "server_address",
    "session_token",
)


class SupportBundleUploadError(ValueError):
    def __init__(self, code: str, *, status_code: int = 422) -> None:
        super().__init__(code)
        self.code = code
        self.status_code = int(status_code)


@dataclass(frozen=True, slots=True)
class SupportBundleUploadSpec:
    idempotency_key: str
    bundle_id: str
    size_bytes: int
    sha256: str
    content_type: str
    case_summary: str
    case_subject: str


@dataclass(frozen=True, slots=True)
class SupportBundleTicketResult:
    upload_id: str
    ticket_id: int
    upload_ticket: str
    expires_at: datetime
    next_offset: int
    status: str
    object_name: str | None
    failure_code: str | None


@dataclass(frozen=True, slots=True)
class SupportBundleChunkResult:
    upload_id: str
    next_offset: int
    complete: bool
    repeated: bool


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_upload_spec(
    *,
    idempotency_key: object,
    bundle_id: object,
    size_bytes: object,
    sha256: object,
    content_type: object,
    case_summary: object,
    case_subject: object = "Диагностика POKROV",
) -> SupportBundleUploadSpec:
    normalized_idempotency = str(idempotency_key or "").strip()
    normalized_bundle = str(bundle_id or "").strip().lower()
    normalized_sha = str(sha256 or "").strip().lower()
    normalized_type = str(content_type or "").strip().lower()
    try:
        normalized_size = int(size_bytes)
    except (TypeError, ValueError):
        raise SupportBundleUploadError("invalid_size") from None
    if _IDEMPOTENCY_KEY.fullmatch(normalized_idempotency) is None:
        raise SupportBundleUploadError("invalid_idempotency_key")
    if _BUNDLE_ID.fullmatch(normalized_bundle) is None:
        raise SupportBundleUploadError("invalid_bundle_id")
    if normalized_size <= 0 or normalized_size > MAX_BUNDLE_BYTES:
        raise SupportBundleUploadError("invalid_size")
    if _SHA256.fullmatch(normalized_sha) is None:
        raise SupportBundleUploadError("invalid_checksum")
    if normalized_type != SUPPORT_BUNDLE_CONTENT_TYPE:
        raise SupportBundleUploadError("unsupported_content_type", status_code=415)
    summary = _safe_case_text(case_summary, maximum=500, code="invalid_case_summary")
    subject = _safe_case_text(case_subject, maximum=120, code="invalid_case_subject")
    if not summary:
        raise SupportBundleUploadError("invalid_case_summary")
    if not subject:
        subject = "Диагностика POKROV"
    return SupportBundleUploadSpec(
        idempotency_key=normalized_idempotency,
        bundle_id=normalized_bundle,
        size_bytes=normalized_size,
        sha256=normalized_sha,
        content_type=normalized_type,
        case_summary=summary,
        case_subject=subject,
    )


def owner_binding_hash(
    *,
    owner_tg_id: int,
    owner_account_id: str | None,
    anonymous_nonce: object = None,
) -> str:
    account = str(owner_account_id or "").strip().lower()
    if account:
        material = f"account:{account}"
    else:
        nonce = str(anonymous_nonce or "").strip()
        if _ANONYMOUS_NONCE.fullmatch(nonce) is None:
            raise SupportBundleUploadError("anonymous_nonce_required")
        material = f"anonymous:{int(owner_tg_id)}:{nonce}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def issue_upload_ticket(
    session,
    *,
    owner_tg_id: int,
    owner_account_id: str | None,
    owner_binding: str,
    spec: SupportBundleUploadSpec,
    signing_secret: str | bytes,
    ticket_id: int | None = None,
    now: datetime | None = None,
    ttl: timedelta = DEFAULT_TICKET_TTL,
) -> SupportBundleTicketResult:
    current = now or utcnow()
    if ttl <= timedelta(0) or ttl > timedelta(minutes=30):
        raise SupportBundleUploadError("invalid_ticket_ttl", status_code=503)
    existing = (
        session.query(SupportBundleUpload)
        .filter(
            SupportBundleUpload.owner_binding_hash == owner_binding,
            SupportBundleUpload.idempotency_key == spec.idempotency_key,
        )
        .first()
    )
    if existing is not None:
        _require_same_spec(existing, spec, requested_ticket_id=ticket_id)
        if existing.expires_at <= current and existing.status in {
            "issued",
            "uploading",
        }:
            existing.expires_at = current + ttl
            existing.updated_at = current
            session.flush()
        return _ticket_result(existing, signing_secret)

    selected_ticket_id = ticket_id
    if selected_ticket_id is None:
        ticket = SupportTicket(
            user_tg_id=int(owner_tg_id),
            account_id=str(owner_account_id or "").strip() or None,
            status="open",
            subject=spec.case_subject,
            created_at=current,
            updated_at=current,
        )
        session.add(ticket)
        session.flush()
        message = SupportTicketMessage(
            ticket_id=int(ticket.id),
            sender_tg_id=int(owner_tg_id),
            sender_role="user",
            body=spec.case_summary,
            created_at=current,
        )
        session.add(message)
        selected_ticket_id = int(ticket.id)
    if selected_ticket_id is None or int(selected_ticket_id) <= 0:
        raise SupportBundleUploadError("ticket_required")

    conflicting = (
        session.query(SupportBundleUpload)
        .filter(
            SupportBundleUpload.ticket_id == int(selected_ticket_id),
            SupportBundleUpload.bundle_id == spec.bundle_id,
        )
        .first()
    )
    if conflicting is not None:
        raise SupportBundleUploadError("bundle_binding_conflict", status_code=409)

    row = SupportBundleUpload(
        upload_id=str(uuid.uuid4()),
        ticket_id=int(selected_ticket_id),
        owner_tg_id=int(owner_tg_id),
        owner_account_id=str(owner_account_id or "").strip() or None,
        owner_binding_hash=owner_binding,
        idempotency_key=spec.idempotency_key,
        bundle_id=spec.bundle_id,
        expected_size_bytes=spec.size_bytes,
        expected_sha256=spec.sha256,
        content_type=spec.content_type,
        received_size_bytes=0,
        status="issued",
        expires_at=current + ttl,
        created_at=current,
        updated_at=current,
    )
    session.add(row)
    try:
        session.flush()
    except IntegrityError:
        raise SupportBundleUploadError(
            "upload_binding_conflict", status_code=409
        ) from None
    return _ticket_result(row, signing_secret)


def accept_upload_chunk(
    session,
    *,
    upload_id: str,
    upload_ticket: str,
    owner_binding: str,
    offset_bytes: int,
    chunk_sha256: str,
    chunk: bytes,
    signing_secret: str | bytes,
    quarantine_root: Path,
    now: datetime | None = None,
) -> SupportBundleChunkResult:
    current = now or utcnow()
    token = verify_upload_ticket(
        upload_ticket,
        signing_secret=signing_secret,
        now=current,
        expected_owner_binding=owner_binding,
        expected_upload_id=upload_id,
    )
    row = _upload_row(session, upload_id)
    _require_token_matches_row(token, row)
    if row.expires_at <= current:
        raise SupportBundleUploadError("upload_ticket_expired", status_code=410)
    if row.status not in {"issued", "uploading"}:
        raise SupportBundleUploadError("upload_not_writable", status_code=409)
    try:
        offset = int(offset_bytes)
    except (TypeError, ValueError):
        raise SupportBundleUploadError("invalid_chunk_offset") from None
    digest = str(chunk_sha256 or "").strip().lower()
    if _SHA256.fullmatch(digest) is None or not hmac.compare_digest(
        hashlib.sha256(chunk).hexdigest(), digest
    ):
        raise SupportBundleUploadError("chunk_checksum_mismatch", status_code=409)
    if not chunk or len(chunk) > MAX_CHUNK_BYTES:
        raise SupportBundleUploadError("invalid_chunk_size", status_code=413)
    if offset < 0 or offset + len(chunk) > int(row.expected_size_bytes):
        raise SupportBundleUploadError("invalid_chunk_range")

    repeated = (
        session.query(SupportBundleChunk)
        .filter(
            SupportBundleChunk.upload_id == int(row.id),
            SupportBundleChunk.offset_bytes == offset,
        )
        .first()
    )
    if repeated is not None:
        if int(repeated.size_bytes) != len(chunk) or not hmac.compare_digest(
            str(repeated.sha256), digest
        ):
            raise SupportBundleUploadError("chunk_replay_conflict", status_code=409)
        return SupportBundleChunkResult(
            upload_id=row.upload_id,
            next_offset=int(row.received_size_bytes),
            complete=int(row.received_size_bytes) == int(row.expected_size_bytes),
            repeated=True,
        )
    if offset != int(row.received_size_bytes):
        raise SupportBundleUploadError("unexpected_chunk_offset", status_code=409)
    if (
        session.query(SupportBundleChunk)
        .filter(SupportBundleChunk.upload_id == int(row.id))
        .count()
        >= MAX_CHUNKS
    ):
        raise SupportBundleUploadError("chunk_count_exceeded", status_code=413)

    root = _private_storage_root(quarantine_root)
    stored_name = f"{row.upload_id}.{offset:010d}.{digest[:16]}.chunk"
    target = _owned_child(root, stored_name)
    _write_exclusive(target, chunk)
    chunk_row = SupportBundleChunk(
        upload_id=int(row.id),
        offset_bytes=offset,
        size_bytes=len(chunk),
        sha256=digest,
        stored_name=stored_name,
        created_at=current,
    )
    session.add(chunk_row)
    row.received_size_bytes = offset + len(chunk)
    row.status = "uploading"
    row.updated_at = current
    try:
        session.flush()
    except Exception:
        _unlink_owned(target, root)
        raise
    return SupportBundleChunkResult(
        upload_id=row.upload_id,
        next_offset=int(row.received_size_bytes),
        complete=int(row.received_size_bytes) == int(row.expected_size_bytes),
        repeated=False,
    )


def complete_upload(
    session,
    *,
    upload_id: str,
    upload_ticket: str,
    owner_binding: str,
    signing_secret: str | bytes,
    now: datetime | None = None,
) -> SupportBundleUpload:
    current = now or utcnow()
    row = _upload_row(session, upload_id)
    token = verify_upload_ticket(
        upload_ticket,
        signing_secret=signing_secret,
        now=current,
        expected_owner_binding=owner_binding,
        expected_upload_id=upload_id,
        allow_expired_for_completed=row.status in {"queued", "validated"},
    )
    _require_token_matches_row(token, row)
    if row.status in {"queued", "validated"}:
        return row
    if row.status == "rejected":
        raise SupportBundleUploadError("upload_rejected", status_code=409)
    if row.expires_at <= current:
        raise SupportBundleUploadError("upload_ticket_expired", status_code=410)
    chunks = (
        session.query(SupportBundleChunk)
        .filter(SupportBundleChunk.upload_id == int(row.id))
        .order_by(SupportBundleChunk.offset_bytes.asc())
        .all()
    )
    if not chunks or len(chunks) > MAX_CHUNKS:
        raise SupportBundleUploadError("upload_incomplete", status_code=409)
    cursor = 0
    for chunk in chunks:
        if int(chunk.offset_bytes) != cursor:
            raise SupportBundleUploadError("upload_incomplete", status_code=409)
        cursor += int(chunk.size_bytes)
    if cursor != int(row.expected_size_bytes) or cursor != int(row.received_size_bytes):
        raise SupportBundleUploadError("upload_incomplete", status_code=409)
    row.status = "queued"
    row.object_name = f"{row.upload_id}.pokrov-support"
    row.completed_at = current
    row.updated_at = current
    session.flush()
    return row


def get_upload_status(
    session,
    *,
    upload_id: str,
    upload_ticket: str,
    owner_binding: str,
    signing_secret: str | bytes,
    now: datetime | None = None,
) -> SupportBundleTicketResult:
    current = now or utcnow()
    row = _upload_row(session, upload_id)
    token = verify_upload_ticket(
        upload_ticket,
        signing_secret=signing_secret,
        now=current,
        expected_owner_binding=owner_binding,
        expected_upload_id=upload_id,
        allow_expired_for_completed=row.status in {"queued", "validated", "rejected"},
    )
    _require_token_matches_row(token, row)
    return _ticket_result(row, signing_secret)


def verify_upload_ticket(
    token: str,
    *,
    signing_secret: str | bytes,
    now: datetime,
    expected_owner_binding: str,
    expected_upload_id: str,
    allow_expired_for_completed: bool = False,
) -> dict[str, Any]:
    secret = _signing_secret(signing_secret)
    parts = str(token or "").split(".")
    if len(parts) != 3 or parts[0] != "v1":
        raise SupportBundleUploadError("invalid_upload_ticket", status_code=401)
    encoded, supplied_signature = parts[1], parts[2]
    expected_signature = _b64url(
        hmac.new(secret, f"v1.{encoded}".encode("ascii"), hashlib.sha256).digest()
    )
    if not hmac.compare_digest(expected_signature, supplied_signature):
        raise SupportBundleUploadError("invalid_upload_ticket", status_code=401)
    try:
        raw = _decode_b64url(encoded, maximum_bytes=2048)
        payload = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_keys
        )
    except (UnicodeError, ValueError):
        raise SupportBundleUploadError(
            "invalid_upload_ticket", status_code=401
        ) from None
    if not isinstance(payload, dict) or set(payload) != _TOKEN_FIELDS:
        raise SupportBundleUploadError("invalid_upload_ticket", status_code=401)
    if payload.get("version") != 1:
        raise SupportBundleUploadError("invalid_upload_ticket", status_code=401)
    if not hmac.compare_digest(
        str(payload.get("owner_binding_hash") or ""), expected_owner_binding
    ):
        raise SupportBundleUploadError("upload_owner_mismatch", status_code=403)
    if not hmac.compare_digest(
        str(payload.get("upload_id") or ""), str(expected_upload_id)
    ):
        raise SupportBundleUploadError("upload_ticket_mismatch", status_code=409)
    try:
        expires_at = datetime.fromtimestamp(
            int(payload["exp"]), tz=timezone.utc
        ).replace(tzinfo=None)
    except (KeyError, TypeError, ValueError, OverflowError):
        raise SupportBundleUploadError(
            "invalid_upload_ticket", status_code=401
        ) from None
    if expires_at <= now and not allow_expired_for_completed:
        raise SupportBundleUploadError("upload_ticket_expired", status_code=410)
    return payload


def load_configured_signed_key_set(raw_json: str) -> dict[str, Any]:
    if not raw_json or len(raw_json.encode("utf-8")) > 24 * 1024:
        raise SupportBundleUploadError("support_key_set_unavailable", status_code=503)
    try:
        value = json.loads(raw_json, object_pairs_hook=_reject_duplicate_keys)
    except ValueError:
        raise SupportBundleUploadError(
            "support_key_set_unavailable", status_code=503
        ) from None
    expected = {"algorithm", "key_id", "payload_b64", "schema_version", "signature_b64"}
    if not isinstance(value, dict) or set(value) != expected:
        raise SupportBundleUploadError("support_key_set_unavailable", status_code=503)
    if value.get("algorithm") != "Ed25519" or value.get("schema_version") != 1:
        raise SupportBundleUploadError("support_key_set_unavailable", status_code=503)
    if (
        re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,63}", str(value.get("key_id") or ""))
        is None
    ):
        raise SupportBundleUploadError("support_key_set_unavailable", status_code=503)
    try:
        _decode_b64url(str(value.get("payload_b64") or ""), maximum_bytes=16 * 1024)
        signature = _decode_b64url(
            str(value.get("signature_b64") or ""),
            maximum_bytes=64,
        )
    except ValueError:
        raise SupportBundleUploadError(
            "support_key_set_unavailable",
            status_code=503,
        ) from None
    if len(signature) != 64:
        raise SupportBundleUploadError("support_key_set_unavailable", status_code=503)
    return value


def _ticket_result(
    row: SupportBundleUpload,
    signing_secret: str | bytes,
) -> SupportBundleTicketResult:
    payload = {
        "bundle_id": row.bundle_id,
        "content_type": row.content_type,
        "exp": int(row.expires_at.replace(tzinfo=timezone.utc).timestamp()),
        "owner_binding_hash": row.owner_binding_hash,
        "sha256": row.expected_sha256,
        "size_bytes": int(row.expected_size_bytes),
        "upload_id": row.upload_id,
        "version": 1,
    }
    encoded = _b64url(_canonical_json(payload))
    signature = _b64url(
        hmac.new(
            _signing_secret(signing_secret),
            f"v1.{encoded}".encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    return SupportBundleTicketResult(
        upload_id=row.upload_id,
        ticket_id=int(row.ticket_id),
        upload_ticket=f"v1.{encoded}.{signature}",
        expires_at=row.expires_at,
        next_offset=int(row.received_size_bytes),
        status=row.status,
        object_name=row.object_name,
        failure_code=row.failure_code,
    )


def _require_same_spec(
    row: SupportBundleUpload,
    spec: SupportBundleUploadSpec,
    *,
    requested_ticket_id: int | None,
) -> None:
    same = (
        row.bundle_id == spec.bundle_id
        and int(row.expected_size_bytes) == spec.size_bytes
        and hmac.compare_digest(row.expected_sha256, spec.sha256)
        and row.content_type == spec.content_type
        and (
            requested_ticket_id is None
            or int(row.ticket_id) == int(requested_ticket_id)
        )
    )
    if not same:
        raise SupportBundleUploadError("idempotency_conflict", status_code=409)


def _require_token_matches_row(
    token: Mapping[str, Any], row: SupportBundleUpload
) -> None:
    same = (
        token.get("bundle_id") == row.bundle_id
        and token.get("content_type") == row.content_type
        and int(token.get("size_bytes") or -1) == int(row.expected_size_bytes)
        and hmac.compare_digest(str(token.get("sha256") or ""), row.expected_sha256)
        and hmac.compare_digest(
            str(token.get("owner_binding_hash") or ""), row.owner_binding_hash
        )
    )
    if not same:
        raise SupportBundleUploadError("upload_ticket_mismatch", status_code=409)


def _upload_row(session, upload_id: str) -> SupportBundleUpload:
    try:
        normalized = str(uuid.UUID(str(upload_id)))
    except (ValueError, AttributeError, TypeError):
        raise SupportBundleUploadError("upload_not_found", status_code=404) from None
    row = (
        session.query(SupportBundleUpload)
        .filter(SupportBundleUpload.upload_id == normalized)
        .first()
    )
    if row is None:
        raise SupportBundleUploadError("upload_not_found", status_code=404)
    return row


def _safe_case_text(raw: object, *, maximum: int, code: str) -> str:
    value = " ".join(str(raw or "").strip().split())
    if len(value) > maximum or any(
        fragment in value.lower() for fragment in _FORBIDDEN_SUMMARY
    ):
        raise SupportBundleUploadError(code)
    if any(ord(character) < 0x20 for character in value):
        raise SupportBundleUploadError(code)
    return value


def _private_storage_root(path: Path) -> Path:
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or (
        callable(getattr(root, "is_junction", None)) and root.is_junction()
    ):
        raise SupportBundleUploadError("quarantine_unavailable", status_code=503)
    return root.resolve(strict=True)


def _owned_child(root: Path, name: str) -> Path:
    if re.fullmatch(r"[0-9a-f-]{36}\.[0-9]{10}\.[a-f0-9]{16}\.chunk", name) is None:
        raise SupportBundleUploadError("unsafe_chunk_name", status_code=500)
    target = (root / name).resolve(strict=False)
    if target.parent != root:
        raise SupportBundleUploadError("unsafe_chunk_name", status_code=500)
    return target


def _write_exclusive(path: Path, value: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        raise SupportBundleUploadError(
            "chunk_storage_conflict", status_code=409
        ) from None
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise


def _unlink_owned(path: Path, root: Path) -> None:
    if path.parent == root and path.name.endswith(".chunk"):
        path.unlink(missing_ok=True)


def _signing_secret(value: str | bytes) -> bytes:
    secret = value.encode("utf-8") if isinstance(value, str) else bytes(value)
    if len(secret) < 32:
        raise SupportBundleUploadError("upload_signing_unavailable", status_code=503)
    return secret


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_b64url(value: str, *, maximum_bytes: int) -> bytes:
    if (
        not value
        or len(value) > ((maximum_bytes + 2) // 3) * 4
        or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None
    ):
        raise ValueError("invalid base64url")
    decoded = base64.urlsafe_b64decode(value + ("=" * ((4 - len(value) % 4) % 4)))
    if len(decoded) > maximum_bytes:
        raise ValueError("decoded value too large")
    return decoded


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value
