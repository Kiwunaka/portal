"""Isolated validation worker for encrypted POKROV support bundles.

The API process must not import this module. The worker assembles bounded
ciphertext chunks, calls an injected decryptor, validates the plaintext in
memory and persists only the original encrypted envelope.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

try:
    from .models import SupportBundleChunk, SupportBundleUpload
    from .support_bundle_upload_service import (
        MAX_BUNDLE_BYTES,
        MAX_CHUNKS,
        SUPPORT_BUNDLE_CONTENT_TYPE,
    )
except ImportError:
    from models import SupportBundleChunk, SupportBundleUpload
    from support_bundle_upload_service import (
        MAX_BUNDLE_BYTES,
        MAX_CHUNKS,
        SUPPORT_BUNDLE_CONTENT_TYPE,
    )


MAX_PLAINTEXT_BYTES = 2 * 1024 * 1024
MAX_FILES = 6
ENVELOPE_FIELDS = frozenset(
    {
        "algorithm",
        "bundle_sha256",
        "ciphertext_b64",
        "diagnostic_id",
        "ephemeral_public_key_b64",
        "mac_b64",
        "manifest_sha256",
        "nonce_b64",
        "recipient_key_id",
        "schema_version",
    }
)
PAYLOAD_FIELDS = frozenset({"files", "manifest", "schema_version"})
MANIFEST_FIELDS = frozenset(
    {
        "build",
        "diagnostic_id",
        "files",
        "profile",
        "redaction",
        "schema_version",
    }
)
FILE_ENTRY_FIELDS = frozenset({"content_b64", "path"})
FILE_DESCRIPTOR_FIELDS = frozenset({"category", "path", "sha256", "size"})
ALGORITHM = "X25519-HKDF-SHA256-AES-256-GCM"

_DIAGNOSTIC_ID = re.compile(r"^diag-[a-f0-9]{24}$")
_KEY_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_CHUNK_NAME = re.compile(
    r"^(?P<upload>[0-9a-f-]{36})\.(?P<offset>[0-9]{10})\."
    r"(?P<digest>[a-f0-9]{16})\.chunk$"
)
_IPV4 = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
_HOSTNAME = re.compile(r"\b(?:[a-z0-9-]+\.)+[a-z]{2,63}\b", re.IGNORECASE)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_FORBIDDEN_CONTENT = (
    "://",
    "access-token",
    "authorization",
    "bearer ",
    "cookie",
    "credential",
    "outbounds",
    "package_name",
    "private-key",
    "refresh_token",
    "server_address",
    "session_token",
)
_MALWARE_MARKERS = (
    "eicar-standard-antivirus-test-file",
    "powershell -encodedcommand",
    "powershell.exe -enc",
    "cmd.exe /c",
    "#!/bin/",
    "<script",
    "mzmz",
)
_PATH_CATEGORY = {
    "build/identity.json": "build",
    "crash/index.jsonl": "crashes",
    "events/recent.jsonl": "events",
    "network/summary.json": "network",
    "redaction/report.json": "redaction",
    "system/summary.json": "system",
}
_CORE_PATHS = frozenset(
    {
        "build/identity.json",
        "network/summary.json",
        "redaction/report.json",
    }
)
_PROFILE_LIMITS = {
    "summary": 64 * 1024,
    "standard": 512 * 1024,
    "extended": 2 * 1024 * 1024,
    "crash": 512 * 1024,
}
_REMOVAL_FIELDS = frozenset(
    {
        "crashesTruncated",
        "eventsTruncated",
        "forbiddenField",
        "invalidValue",
        "optionalCategoryRemoved",
    }
)


class SupportBundleIngestError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class SupportBundleIngestResult:
    upload_id: str
    status: str
    object_name: str | None
    failure_code: str | None


Decryptor = Callable[[Mapping[str, Any]], bytes]


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def process_queued_support_bundle(
    session,
    *,
    upload_id: str,
    quarantine_root: Path,
    accepted_root: Path,
    decryptor: Decryptor,
    now: datetime | None = None,
) -> SupportBundleIngestResult:
    """Validate one queued upload and make its encrypted object durable."""

    row = (
        session.query(SupportBundleUpload)
        .filter(SupportBundleUpload.upload_id == str(upload_id))
        .first()
    )
    if row is None:
        raise SupportBundleIngestError("upload_not_found")
    if row.status == "validated":
        return _result(row)
    if row.status == "rejected":
        return _result(row)
    if row.status != "queued":
        raise SupportBundleIngestError("upload_not_queued")

    current = now or utcnow()
    try:
        encrypted = _assemble_encrypted_bundle(
            session,
            row=row,
            quarantine_root=quarantine_root,
        )
        envelope = parse_encrypted_envelope(encrypted)
        if envelope["diagnostic_id"] != row.bundle_id:
            raise SupportBundleIngestError("bundle_id_mismatch")
        try:
            plaintext = bytes(decryptor(envelope))
        except SupportBundleIngestError:
            raise
        except Exception:
            raise SupportBundleIngestError("decryption_failed") from None
        payload = validate_decrypted_payload(plaintext, envelope=envelope)
        _capture_operator_summary(row, payload)
        object_name = f"{row.upload_id}.pokrov-support"
        _persist_encrypted_object(
            encrypted,
            root=accepted_root,
            object_name=object_name,
            expected_sha256=row.expected_sha256,
        )
        row.status = "validated"
        row.object_name = object_name
        row.failure_code = None
        row.validated_at = current
        row.updated_at = current
        session.flush()
        try:
            _remove_owned_chunks(session, row=row, root=quarantine_root)
        except (OSError, SupportBundleIngestError):
            # The accepted object is already durable and remains encrypted.
            # Stale encrypted chunks are removed by bounded retention cleanup.
            pass
        return _result(row)
    except SupportBundleIngestError as error:
        row.status = "rejected"
        row.failure_code = error.code
        row.validated_at = current
        row.updated_at = current
        session.flush()
        return _result(row)
    except OSError:
        row.status = "rejected"
        row.failure_code = "storage_io_failed"
        row.validated_at = current
        row.updated_at = current
        session.flush()
        return _result(row)


def _capture_operator_summary(row: SupportBundleUpload, payload: Mapping[str, Any]) -> None:
    """Persist only the closed scalar facts needed by the L1 read model."""

    manifest = _mapping(payload.get("manifest"), code="manifest_invalid")
    build = _mapping(manifest.get("build"), code="build_invalid")
    row.diagnostic_profile = _text(manifest.get("profile"), 16)
    row.app_version = _text(build.get("app_version"), 64)
    row.build_number = _text(build.get("build_id"), 80)
    row.platform = _text(build.get("platform"), 16)

    file_bytes: dict[str, bytes] = {}
    for entry in payload.get("files", []):
        item = _mapping(entry, code="file_entry_invalid")
        path = _text(item.get("path"), 64)
        file_bytes[path] = _decode_base64url(
            item.get("content_b64"),
            maximum_bytes=MAX_PLAINTEXT_BYTES,
            code="file_content_invalid",
        )

    system_raw = file_bytes.get("system/summary.json")
    if system_raw is not None:
        system = _parse_json_object(system_raw, code="system_invalid")
        row.architecture = _text(system.get("architecture"), 16)

    network = _parse_json_object(
        file_bytes["network/summary.json"],
        code="network_invalid",
    )
    proof_state = _text(network.get("egress_state"), 16)
    row.proof_outcome = {
        "healthy": "succeeded",
        "failed": "failed",
        "pending": "started",
        "unavailable": "unavailable",
        "unknown": "unknown",
    }[proof_state]
    row.last_phase = None
    row.last_error_code = None
    # Reduced support events have no attempt identity or authoritative counter.
    # Stage starts and a non-disconnected snapshot cannot supply a denominator.
    row.observed_attempts = None

    events_raw = file_bytes.get("events/recent.jsonl")
    if events_raw:
        records = [
            _parse_json_object(line, code="event_record_invalid")
            for line in events_raw.splitlines()
            if line
        ]
        if records:
            last = records[-1]
            row.last_phase = _text(last.get("stage"), 32)
            error_code = last.get("error_code")
            row.last_error_code = (
                _text(error_code, 32) if error_code is not None else None
            )


def parse_encrypted_envelope(raw: bytes) -> dict[str, Any]:
    if not raw or len(raw) > MAX_BUNDLE_BYTES:
        raise SupportBundleIngestError("encrypted_size_invalid")
    value = _parse_json_object(raw, code="envelope_invalid")
    _expect_keys(value, ENVELOPE_FIELDS, code="envelope_invalid")
    if value.get("schema_version") != 1 or value.get("algorithm") != ALGORITHM:
        raise SupportBundleIngestError("envelope_invalid")
    if _DIAGNOSTIC_ID.fullmatch(_text(value.get("diagnostic_id"), 29)) is None:
        raise SupportBundleIngestError("envelope_invalid")
    if _KEY_ID.fullmatch(_text(value.get("recipient_key_id"), 64)) is None:
        raise SupportBundleIngestError("envelope_invalid")
    for field in ("bundle_sha256", "manifest_sha256"):
        if _SHA256.fullmatch(_text(value.get(field), 64)) is None:
            raise SupportBundleIngestError("envelope_invalid")
    _decode_base64url(
        value.get("ephemeral_public_key_b64"),
        exact_bytes=32,
        code="envelope_invalid",
    )
    _decode_base64url(value.get("mac_b64"), exact_bytes=16, code="envelope_invalid")
    _decode_base64url(value.get("nonce_b64"), exact_bytes=12, code="envelope_invalid")
    _decode_base64url(
        value.get("ciphertext_b64"),
        maximum_bytes=MAX_PLAINTEXT_BYTES,
        code="envelope_invalid",
    )
    if raw != _canonical_json(value):
        raise SupportBundleIngestError("envelope_not_canonical")
    return value


def validate_decrypted_payload(
    raw: bytes,
    *,
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    if not raw or len(raw) > MAX_PLAINTEXT_BYTES:
        raise SupportBundleIngestError("plaintext_size_invalid")
    if not hmac.compare_digest(
        hashlib.sha256(raw).hexdigest(), envelope["bundle_sha256"]
    ):
        raise SupportBundleIngestError("plaintext_checksum_mismatch")
    payload = _parse_json_object(raw, code="payload_invalid")
    _expect_keys(payload, PAYLOAD_FIELDS, code="payload_invalid")
    if payload.get("schema_version") != 1:
        raise SupportBundleIngestError("payload_invalid")
    if raw != _canonical_json(payload):
        raise SupportBundleIngestError("payload_not_canonical")

    manifest = _mapping(payload.get("manifest"), code="manifest_invalid")
    _expect_keys(manifest, MANIFEST_FIELDS, code="manifest_invalid")
    if manifest.get("schema_version") != 1:
        raise SupportBundleIngestError("manifest_invalid")
    profile = _text(manifest.get("profile"), 16)
    limit = _PROFILE_LIMITS.get(profile)
    if limit is None or len(raw) > limit:
        raise SupportBundleIngestError("profile_budget_exceeded")
    diagnostic_id = _text(manifest.get("diagnostic_id"), 29)
    if diagnostic_id != envelope["diagnostic_id"]:
        raise SupportBundleIngestError("diagnostic_id_mismatch")

    manifest_core = dict(manifest)
    manifest_core.pop("diagnostic_id", None)
    expected_diagnostic_id = (
        f"diag-{hashlib.sha256(_canonical_json(manifest_core)).hexdigest()[:24]}"
    )
    if not hmac.compare_digest(diagnostic_id, expected_diagnostic_id):
        raise SupportBundleIngestError("diagnostic_id_mismatch")
    if not hmac.compare_digest(
        hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        str(envelope["manifest_sha256"]),
    ):
        raise SupportBundleIngestError("manifest_checksum_mismatch")

    build = _validate_build(manifest.get("build"))
    redaction = _validate_redaction(manifest.get("redaction"))
    descriptors = _validate_descriptors(manifest.get("files"))
    files = _validate_files(
        payload.get("files"),
        descriptors=descriptors,
        build=build,
        redaction=redaction,
    )
    paths = frozenset(files)
    if not _CORE_PATHS.issubset(paths):
        raise SupportBundleIngestError("required_file_missing")
    if profile == "summary" and paths != _CORE_PATHS:
        raise SupportBundleIngestError("profile_file_mismatch")
    if profile == "standard" and "crash/index.jsonl" in paths:
        raise SupportBundleIngestError("profile_file_mismatch")
    return payload


def _assemble_encrypted_bundle(session, *, row, quarantine_root: Path) -> bytes:
    if row.content_type != SUPPORT_BUNDLE_CONTENT_TYPE:
        raise SupportBundleIngestError("mime_mismatch")
    root = _private_root(quarantine_root, code="quarantine_unavailable", create=False)
    chunks = (
        session.query(SupportBundleChunk)
        .filter(SupportBundleChunk.upload_id == int(row.id))
        .order_by(SupportBundleChunk.offset_bytes.asc())
        .all()
    )
    if not chunks or len(chunks) > MAX_CHUNKS:
        raise SupportBundleIngestError("chunk_count_invalid")
    assembled = bytearray()
    cursor = 0
    for chunk in chunks:
        offset = int(chunk.offset_bytes)
        if offset != cursor:
            raise SupportBundleIngestError("chunk_layout_invalid")
        expected_name = f"{row.upload_id}.{offset:010d}.{str(chunk.sha256)[:16]}.chunk"
        if (
            chunk.stored_name != expected_name
            or _CHUNK_NAME.fullmatch(expected_name) is None
        ):
            raise SupportBundleIngestError("chunk_name_invalid")
        path = _owned_file(root, expected_name, code="chunk_path_invalid")
        if path.is_symlink() or not path.is_file():
            raise SupportBundleIngestError("chunk_missing")
        data = path.read_bytes()
        if len(data) != int(chunk.size_bytes) or not hmac.compare_digest(
            hashlib.sha256(data).hexdigest(),
            str(chunk.sha256),
        ):
            raise SupportBundleIngestError("chunk_checksum_mismatch")
        assembled.extend(data)
        if len(assembled) > MAX_BUNDLE_BYTES:
            raise SupportBundleIngestError("encrypted_size_invalid")
        cursor += len(data)
    raw = bytes(assembled)
    if cursor != int(row.expected_size_bytes) or cursor != int(row.received_size_bytes):
        raise SupportBundleIngestError("chunk_layout_invalid")
    if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), row.expected_sha256):
        raise SupportBundleIngestError("encrypted_checksum_mismatch")
    return raw


def _validate_descriptors(raw: object) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_FILES:
        raise SupportBundleIngestError("file_count_invalid")
    result: dict[str, dict[str, Any]] = {}
    ordered_paths: list[str] = []
    for item in raw:
        descriptor = _mapping(item, code="file_descriptor_invalid")
        _expect_keys(descriptor, FILE_DESCRIPTOR_FIELDS, code="file_descriptor_invalid")
        path = _virtual_path(descriptor.get("path"))
        category = _text(descriptor.get("category"), 16)
        if _PATH_CATEGORY.get(path) != category or path in result:
            raise SupportBundleIngestError("file_descriptor_invalid")
        digest = _text(descriptor.get("sha256"), 64)
        if _SHA256.fullmatch(digest) is None:
            raise SupportBundleIngestError("file_descriptor_invalid")
        size = descriptor.get("size")
        if type(size) is not int or size < 0 or size > MAX_PLAINTEXT_BYTES:
            raise SupportBundleIngestError("file_descriptor_invalid")
        result[path] = descriptor
        ordered_paths.append(path)
    if ordered_paths != sorted(ordered_paths):
        raise SupportBundleIngestError("file_order_invalid")
    return result


def _validate_files(
    raw: object,
    *,
    descriptors: Mapping[str, Mapping[str, Any]],
    build: Mapping[str, Any],
    redaction: Mapping[str, Any],
) -> dict[str, bytes]:
    if not isinstance(raw, list) or len(raw) != len(descriptors):
        raise SupportBundleIngestError("file_count_invalid")
    result: dict[str, bytes] = {}
    ordered_paths: list[str] = []
    for item in raw:
        entry = _mapping(item, code="file_entry_invalid")
        _expect_keys(entry, FILE_ENTRY_FIELDS, code="file_entry_invalid")
        path = _virtual_path(entry.get("path"))
        if path in result or path not in descriptors:
            raise SupportBundleIngestError("file_entry_invalid")
        descriptor = descriptors[path]
        content = _decode_base64url(
            entry.get("content_b64"),
            maximum_bytes=int(descriptor["size"]),
            code="file_content_invalid",
            allow_empty=True,
        )
        if len(content) != int(descriptor["size"]) or not hmac.compare_digest(
            hashlib.sha256(content).hexdigest(),
            str(descriptor["sha256"]),
        ):
            raise SupportBundleIngestError("file_checksum_mismatch")
        _scan_content(content)
        _validate_file_schema(path, content, build=build, redaction=redaction)
        result[path] = content
        ordered_paths.append(path)
    if ordered_paths != list(descriptors):
        raise SupportBundleIngestError("file_order_invalid")
    return result


def _validate_file_schema(
    path: str,
    raw: bytes,
    *,
    build: Mapping[str, Any],
    redaction: Mapping[str, Any],
) -> None:
    if path.endswith(".jsonl"):
        lines = raw.splitlines()
        maximum = 100 if path.startswith("crash/") else 2000
        if len(lines) > maximum:
            raise SupportBundleIngestError("record_count_invalid")
        for line in lines:
            if not line:
                raise SupportBundleIngestError("jsonl_invalid")
            value = _parse_json_object(line, code="jsonl_invalid")
            if path.startswith("crash/"):
                _validate_crash_record(value)
            else:
                _validate_event_record(value)
        if raw and not raw.endswith(b"\n"):
            raise SupportBundleIngestError("jsonl_invalid")
        return
    value = _parse_json_object(raw, code="file_json_invalid")
    if path == "build/identity.json" and value != build:
        raise SupportBundleIngestError("build_mismatch")
    if path == "redaction/report.json":
        expected = {"removed": redaction["removed"], "schema_version": 1}
        if value != expected:
            raise SupportBundleIngestError("redaction_mismatch")
    elif path == "network/summary.json":
        _validate_network(value)
    elif path == "system/summary.json":
        _validate_system(value)


def _validate_network(value: Mapping[str, Any]) -> None:
    expected = frozenset(
        {
            "connection_state",
            "dns_state",
            "egress_state",
            "host_health",
            "route_mode",
            "warp_state",
        }
    )
    _expect_keys(value, expected, code="network_invalid")
    tokens = {
        "connection_state": {
            "blocked",
            "connecting",
            "degraded",
            "disconnected",
            "verified",
        },
        "dns_state": {"failed", "healthy", "pending", "unavailable", "unknown"},
        "egress_state": {"failed", "healthy", "pending", "unavailable", "unknown"},
        "host_health": {"failed", "healthy", "pending", "unavailable", "unknown"},
        "route_mode": {
            "all_except_ru",
            "excluded_apps",
            "full_tunnel",
            "selected_apps",
        },
        "warp_state": {"disabled", "enabled", "fallback", "unavailable"},
    }
    if any(value.get(field) not in allowed for field, allowed in tokens.items()):
        raise SupportBundleIngestError("network_invalid")


def _validate_system(value: Mapping[str, Any]) -> None:
    _expect_keys(
        value,
        frozenset({"architecture", "locale", "os_family", "os_version"}),
        code="system_invalid",
    )
    patterns = {
        "architecture": r"^(arm64|arm|x64|x86)$",
        "locale": r"^[a-z]{2}(?:-[A-Z]{2})?$",
        "os_family": r"^(android|windows)$",
        "os_version": r"^[0-9A-Za-z ._()-]{1,80}$",
    }
    if any(
        re.fullmatch(pattern, _text(value.get(field), 80)) is None
        for field, pattern in patterns.items()
    ):
        raise SupportBundleIngestError("system_invalid")


def _validate_event_record(value: Mapping[str, Any]) -> None:
    required = frozenset({"occurred_at", "outcome", "stage", "subsystem"})
    allowed = required | {"duration_ms", "error_code"}
    if not required.issubset(value) or not set(value).issubset(allowed):
        raise SupportBundleIngestError("event_record_invalid")
    _validate_occurred_at(value.get("occurred_at"), code="event_record_invalid")
    if (
        re.fullmatch(r"^[a-z][a-z0-9_]{0,31}$", _text(value.get("subsystem"), 32))
        is None
    ):
        raise SupportBundleIngestError("event_record_invalid")
    if re.fullmatch(r"^[a-z][a-z0-9_]{0,31}$", _text(value.get("stage"), 32)) is None:
        raise SupportBundleIngestError("event_record_invalid")
    if value.get("outcome") not in {
        "cancelled",
        "crashed",
        "failed",
        "observed",
        "started",
        "succeeded",
        "superseded",
        "timeout",
    }:
        raise SupportBundleIngestError("event_record_invalid")
    duration = value.get("duration_ms")
    if duration is not None and (
        type(duration) is not int or not 0 <= duration <= 86_400_000
    ):
        raise SupportBundleIngestError("event_record_invalid")
    error_code = value.get("error_code")
    if (
        error_code is not None
        and re.fullmatch(
            r"^[A-Z][A-Z0-9_-]{2,31}$",
            _text(error_code, 32),
        )
        is None
    ):
        raise SupportBundleIngestError("event_record_invalid")


def _validate_crash_record(value: Mapping[str, Any]) -> None:
    _expect_keys(
        value,
        frozenset({"error_code", "occurred_at", "signature"}),
        code="crash_record_invalid",
    )
    _validate_occurred_at(value.get("occurred_at"), code="crash_record_invalid")
    if (
        re.fullmatch(r"^CRASH-[A-Z0-9_-]{1,25}$", _text(value.get("error_code"), 32))
        is None
    ):
        raise SupportBundleIngestError("crash_record_invalid")
    if re.fullmatch(r"^[a-f0-9]{16,64}$", _text(value.get("signature"), 64)) is None:
        raise SupportBundleIngestError("crash_record_invalid")


def _validate_occurred_at(raw: object, *, code: str) -> None:
    value = _text(raw, 40)
    if re.fullmatch(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+Z$", value) is None:
        raise SupportBundleIngestError(code)
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        raise SupportBundleIngestError(code) from None


def _validate_build(raw: object) -> dict[str, Any]:
    value = _mapping(raw, code="build_invalid")
    _expect_keys(
        value,
        frozenset({"app_version", "build_id", "channel", "platform"}),
        code="build_invalid",
    )
    patterns = {
        "app_version": r"^[0-9A-Za-z.+-]{1,48}$",
        "build_id": r"^[0-9A-Za-z._-]{1,80}$",
        "channel": r"^(direct|store|stable)$",
        "platform": r"^(android|windows)$",
    }
    if any(
        re.fullmatch(pattern, _text(value.get(field), 80)) is None
        for field, pattern in patterns.items()
    ):
        raise SupportBundleIngestError("build_invalid")
    return value


def _validate_redaction(raw: object) -> dict[str, Any]:
    value = _mapping(raw, code="redaction_invalid")
    _expect_keys(value, frozenset({"removed"}), code="redaction_invalid")
    removed = _mapping(value.get("removed"), code="redaction_invalid")
    _expect_keys(removed, _REMOVAL_FIELDS, code="redaction_invalid")
    if any(
        type(count) is not int or count < 0 or count > 1_000_000
        for count in removed.values()
    ):
        raise SupportBundleIngestError("redaction_invalid")
    return value


def _scan_content(raw: bytes) -> None:
    try:
        content = raw.decode("utf-8", errors="strict")
    except UnicodeError:
        raise SupportBundleIngestError("file_not_utf8") from None
    lowered = content.lower()
    if (
        any(fragment in lowered for fragment in _FORBIDDEN_CONTENT)
        or any(marker in lowered for marker in _MALWARE_MARKERS)
        or _IPV4.search(content) is not None
        or _HOSTNAME.search(content) is not None
        or _EMAIL.search(content) is not None
    ):
        raise SupportBundleIngestError("forbidden_content")


def _persist_encrypted_object(
    raw: bytes,
    *,
    root: Path,
    object_name: str,
    expected_sha256: str,
) -> None:
    storage = _private_root(root, code="accepted_storage_unavailable", create=True)
    if re.fullmatch(r"[0-9a-f-]{36}\.pokrov-support", object_name) is None:
        raise SupportBundleIngestError("object_name_invalid")
    target = _owned_file(
        storage, object_name, code="object_path_invalid", must_exist=False
    )
    if target.exists():
        if target.is_symlink() or not target.is_file():
            raise SupportBundleIngestError("object_storage_conflict")
        existing = target.read_bytes()
        if not hmac.compare_digest(
            hashlib.sha256(existing).hexdigest(), expected_sha256
        ):
            raise SupportBundleIngestError("object_storage_conflict")
        return
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        # The accepted directory's service group may read ciphertext for the
        # audited API download; recipient private keys use separate storage.
        descriptor = os.open(target, flags, 0o640)
    except FileExistsError:
        raise SupportBundleIngestError("object_storage_conflict") from None
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        target.unlink(missing_ok=True)
        raise


def _remove_owned_chunks(session, *, row, root: Path) -> None:
    storage = _private_root(root, code="quarantine_unavailable", create=False)
    chunks = (
        session.query(SupportBundleChunk)
        .filter(SupportBundleChunk.upload_id == int(row.id))
        .all()
    )
    for chunk in chunks:
        match = _CHUNK_NAME.fullmatch(str(chunk.stored_name))
        if match is None or match.group("upload") != row.upload_id:
            continue
        path = _owned_file(
            storage, chunk.stored_name, code="chunk_path_invalid", must_exist=False
        )
        if path.parent == storage and not path.is_symlink():
            path.unlink(missing_ok=True)


def _private_root(path: Path, *, code: str, create: bool) -> Path:
    root = Path(path)
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if not root.exists() or not root.is_dir() or root.is_symlink():
        raise SupportBundleIngestError(code)
    if callable(getattr(root, "is_junction", None)) and root.is_junction():
        raise SupportBundleIngestError(code)
    return root.resolve(strict=True)


def _owned_file(
    root: Path,
    name: str,
    *,
    code: str,
    must_exist: bool = True,
) -> Path:
    try:
        target = (root / name).resolve(strict=must_exist)
    except OSError:
        raise SupportBundleIngestError(code) from None
    if target.parent != root:
        raise SupportBundleIngestError(code)
    return target


def _virtual_path(raw: object) -> str:
    value = _text(raw, 96)
    if (
        value not in _PATH_CATEGORY
        or ".." in value
        or "\\" in value
        or value.startswith("/")
    ):
        raise SupportBundleIngestError("unsafe_virtual_path")
    return value


def _parse_json_object(raw: bytes, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeError, ValueError, RecursionError):
        raise SupportBundleIngestError(code) from None
    if not isinstance(value, dict):
        raise SupportBundleIngestError(code)
    return value


def _mapping(raw: object, *, code: str) -> dict[str, Any]:
    if not isinstance(raw, dict) or any(not isinstance(key, str) for key in raw):
        raise SupportBundleIngestError(code)
    return raw


def _expect_keys(
    value: Mapping[str, Any], expected: frozenset[str], *, code: str
) -> None:
    if set(value) != expected:
        raise SupportBundleIngestError(code)


def _text(raw: object, maximum: int) -> str:
    if not isinstance(raw, str) or raw.strip() != raw or not raw or len(raw) > maximum:
        raise SupportBundleIngestError("text_invalid")
    return raw


def _decode_base64url(
    raw: object,
    *,
    code: str,
    exact_bytes: int | None = None,
    maximum_bytes: int | None = None,
    allow_empty: bool = False,
) -> bytes:
    if not isinstance(raw, str) or raw.strip() != raw:
        raise SupportBundleIngestError(code)
    if not raw and not allow_empty:
        raise SupportBundleIngestError(code)
    limit = maximum_bytes if maximum_bytes is not None else exact_bytes
    if limit is None:
        raise SupportBundleIngestError(code)
    if len(raw) > ((limit + 2) // 3) * 4 or (
        raw and re.fullmatch(r"[A-Za-z0-9_-]+", raw) is None
    ):
        raise SupportBundleIngestError(code)
    try:
        decoded = base64.urlsafe_b64decode(raw + ("=" * ((4 - len(raw) % 4) % 4)))
    except ValueError:
        raise SupportBundleIngestError(code) from None
    if exact_bytes is not None and len(decoded) != exact_bytes:
        raise SupportBundleIngestError(code)
    if maximum_bytes is not None and len(decoded) > maximum_bytes:
        raise SupportBundleIngestError(code)
    return decoded


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value


def _result(row: SupportBundleUpload) -> SupportBundleIngestResult:
    return SupportBundleIngestResult(
        upload_id=row.upload_id,
        status=row.status,
        object_name=row.object_name,
        failure_code=row.failure_code,
    )
