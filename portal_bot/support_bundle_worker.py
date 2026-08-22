"""Isolated queue runner and mounted-key decryptor for support bundles."""

from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

try:
    from .models import SupportBundleUpload
    from .support_bundle_ingest_service import process_queued_support_bundle
except ImportError:
    from models import SupportBundleUpload
    from support_bundle_ingest_service import process_queued_support_bundle


_KEY_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")


class SupportBundleWorkerConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class SupportBundleWorkerReport:
    selected: int
    validated: int
    rejected: int
    failed: int


class MountedX25519SupportDecryptor:
    """Decrypt with an app-private key file mounted only into the worker."""

    def __init__(self, private_keys: Mapping[str, bytes]) -> None:
        if not private_keys or len(private_keys) > 8:
            raise SupportBundleWorkerConfigError("support_recipient_keys_invalid")
        copied: dict[str, bytes] = {}
        for key_id, private_bytes in private_keys.items():
            normalized_id = str(key_id)
            material = bytes(private_bytes)
            if _KEY_ID.fullmatch(normalized_id) is None or len(material) != 32:
                raise SupportBundleWorkerConfigError("support_recipient_keys_invalid")
            x25519.X25519PrivateKey.from_private_bytes(material)
            copied[normalized_id] = material
        self._private_keys = copied

    def __call__(self, envelope: Mapping[str, Any]) -> bytes:
        key_id = str(envelope.get("recipient_key_id") or "")
        private_bytes = self._private_keys.get(key_id)
        if private_bytes is None:
            raise ValueError("recipient_key_unavailable")
        private_key = x25519.X25519PrivateKey.from_private_bytes(private_bytes)
        peer = x25519.X25519PublicKey.from_public_bytes(
            _decode_base64url(envelope.get("ephemeral_public_key_b64"), exact_bytes=32)
        )
        shared = private_key.exchange(peer)
        diagnostic_id = str(envelope.get("diagnostic_id") or "")
        manifest_sha256 = str(envelope.get("manifest_sha256") or "")
        key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=diagnostic_id.encode("utf-8"),
            info=b"pokrov-support-bundle-v1",
        ).derive(shared)
        ciphertext = _decode_base64url(
            envelope.get("ciphertext_b64"),
            maximum_bytes=2 * 1024 * 1024,
        )
        mac = _decode_base64url(envelope.get("mac_b64"), exact_bytes=16)
        nonce = _decode_base64url(envelope.get("nonce_b64"), exact_bytes=12)
        return AESGCM(key).decrypt(
            nonce,
            ciphertext + mac,
            manifest_sha256.encode("utf-8"),
        )


def load_mounted_support_decryptor(path: Path) -> MountedX25519SupportDecryptor:
    source = Path(path)
    if (
        not source.is_absolute()
        or not source.is_file()
        or source.is_symlink()
        or (callable(getattr(source, "is_junction", None)) and source.is_junction())
        or source.stat().st_size > 16 * 1024
    ):
        raise SupportBundleWorkerConfigError("support_recipient_key_file_unavailable")
    try:
        value = json.loads(
            source.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (OSError, UnicodeError, ValueError):
        raise SupportBundleWorkerConfigError(
            "support_recipient_key_file_invalid"
        ) from None
    if not isinstance(value, dict) or set(value) != {"keys", "schema_version"}:
        raise SupportBundleWorkerConfigError("support_recipient_key_file_invalid")
    if value.get("schema_version") != 1:
        raise SupportBundleWorkerConfigError("support_recipient_key_file_invalid")
    raw_keys = value.get("keys")
    if not isinstance(raw_keys, list) or not 1 <= len(raw_keys) <= 8:
        raise SupportBundleWorkerConfigError("support_recipient_key_file_invalid")
    keys: dict[str, bytes] = {}
    for raw in raw_keys:
        if not isinstance(raw, dict) or set(raw) != {"key_id", "private_key_b64"}:
            raise SupportBundleWorkerConfigError("support_recipient_key_file_invalid")
        key_id = str(raw.get("key_id") or "")
        if key_id in keys:
            raise SupportBundleWorkerConfigError("support_recipient_key_file_invalid")
        try:
            keys[key_id] = _decode_base64url(raw.get("private_key_b64"), exact_bytes=32)
        except ValueError:
            raise SupportBundleWorkerConfigError(
                "support_recipient_key_file_invalid"
            ) from None
    return MountedX25519SupportDecryptor(keys)


def load_configured_support_decryptor() -> MountedX25519SupportDecryptor:
    raw_path = str(os.getenv("POKROV_SUPPORT_RECIPIENT_KEYS_FILE") or "").strip()
    if not raw_path:
        raise SupportBundleWorkerConfigError("support_recipient_key_file_unavailable")
    return load_mounted_support_decryptor(Path(raw_path))


def run_support_bundle_ingest_once(
    session_factory,
    *,
    decryptor,
    quarantine_root: Path,
    accepted_root: Path,
    limit: int = 5,
) -> SupportBundleWorkerReport:
    bounded_limit = max(1, min(int(limit), 20))
    session = session_factory()
    selected = validated = rejected = failed = 0
    try:
        rows = (
            session.query(SupportBundleUpload)
            .filter(SupportBundleUpload.status == "queued")
            .order_by(
                SupportBundleUpload.completed_at.asc(), SupportBundleUpload.id.asc()
            )
            .with_for_update(skip_locked=True)
            .limit(bounded_limit)
            .all()
        )
        selected = len(rows)
        for row in rows:
            try:
                result = process_queued_support_bundle(
                    session,
                    upload_id=row.upload_id,
                    quarantine_root=quarantine_root,
                    accepted_root=accepted_root,
                    decryptor=decryptor,
                )
                session.commit()
                if result.status == "validated":
                    validated += 1
                elif result.status == "rejected":
                    rejected += 1
            except Exception:
                session.rollback()
                failed += 1
        return SupportBundleWorkerReport(
            selected=selected,
            validated=validated,
            rejected=rejected,
            failed=failed,
        )
    finally:
        session.close()


def _decode_base64url(
    raw: object,
    *,
    exact_bytes: int | None = None,
    maximum_bytes: int | None = None,
) -> bytes:
    if (
        not isinstance(raw, str)
        or not raw
        or re.fullmatch(r"[A-Za-z0-9_-]+", raw) is None
    ):
        raise ValueError("invalid base64url")
    limit = exact_bytes if exact_bytes is not None else maximum_bytes
    if limit is None or len(raw) > ((limit + 2) // 3) * 4:
        raise ValueError("invalid base64url")
    decoded = base64.urlsafe_b64decode(raw + ("=" * ((4 - len(raw) % 4) % 4)))
    if exact_bytes is not None and len(decoded) != exact_bytes:
        raise ValueError("invalid base64url")
    if maximum_bytes is not None and len(decoded) > maximum_bytes:
        raise ValueError("invalid base64url")
    return decoded


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate key")
        value[key] = item
    return value
