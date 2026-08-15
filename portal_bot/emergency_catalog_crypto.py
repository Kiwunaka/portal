"""Encryption and Ed25519 signing for server-owned emergency catalogs."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


_KEY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class EmergencyCatalogCryptoError(RuntimeError):
    """Fixed-code crypto failure that never contains key or catalog material."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_catalog_bytes(payload: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(payload),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EmergencyCatalogCryptoError("catalog_not_canonicalizable") from exc


def catalog_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_catalog_bytes(payload)).hexdigest()


def _b64url_no_padding(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode_b64url(value: str, *, expected_bytes: int, code: str) -> bytes:
    raw = str(value or "").strip()
    try:
        decoded = base64.urlsafe_b64decode(raw + "=" * ((4 - len(raw) % 4) % 4))
    except Exception as exc:
        raise EmergencyCatalogCryptoError(code) from exc
    if len(decoded) != expected_bytes:
        raise EmergencyCatalogCryptoError(code)
    return decoded


@dataclass(frozen=True, slots=True)
class EmergencyCatalogCrypto:
    key_id: str
    _fernet: Fernet
    _private_key: Ed25519PrivateKey
    _public_key: Ed25519PublicKey

    @classmethod
    def from_raw_keys(
        cls,
        *,
        key_id: str,
        material_key: bytes,
        signing_private_key: bytes,
    ) -> "EmergencyCatalogCrypto":
        normalized_key_id = str(key_id or "").strip().lower()
        if _KEY_ID_RE.fullmatch(normalized_key_id) is None:
            raise EmergencyCatalogCryptoError("invalid_signing_key_id")
        if len(material_key) != 32:
            raise EmergencyCatalogCryptoError("invalid_material_key")
        if len(signing_private_key) != 32:
            raise EmergencyCatalogCryptoError("invalid_signing_private_key")
        private_key = Ed25519PrivateKey.from_private_bytes(signing_private_key)
        return cls(
            key_id=normalized_key_id,
            _fernet=Fernet(base64.urlsafe_b64encode(material_key)),
            _private_key=private_key,
            _public_key=private_key.public_key(),
        )

    @classmethod
    def from_environment(cls) -> "EmergencyCatalogCrypto":
        key_id = os.getenv("EMERGENCY_CATALOG_SIGNING_KEY_ID", "").strip()
        material_key = _decode_b64url(
            os.getenv("EMERGENCY_CATALOG_MATERIAL_KEY_B64", ""),
            expected_bytes=32,
            code="material_key_missing_or_invalid",
        )
        signing_key = _decode_b64url(
            os.getenv("EMERGENCY_CATALOG_SIGNING_PRIVATE_KEY_B64", ""),
            expected_bytes=32,
            code="signing_key_missing_or_invalid",
        )
        return cls.from_raw_keys(
            key_id=key_id,
            material_key=material_key,
            signing_private_key=signing_key,
        )

    @classmethod
    def generate_for_tests(cls, *, key_id: str = "test-emergency-v1") -> "EmergencyCatalogCrypto":
        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return cls.from_raw_keys(
            key_id=key_id,
            material_key=os.urandom(32),
            signing_private_key=private_bytes,
        )

    @property
    def public_key_b64(self) -> str:
        value = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return _b64url_no_padding(value)

    def encrypt_json(self, payload: Mapping[str, Any]) -> str:
        return self._fernet.encrypt(canonical_catalog_bytes(payload)).decode("ascii")

    def decrypt_json(self, ciphertext: str) -> dict[str, Any]:
        try:
            plaintext = self._fernet.decrypt(str(ciphertext or "").encode("ascii"))
            decoded = json.loads(plaintext)
        except (InvalidToken, UnicodeError, ValueError, TypeError) as exc:
            raise EmergencyCatalogCryptoError("invalid_catalog_ciphertext") from exc
        if not isinstance(decoded, dict):
            raise EmergencyCatalogCryptoError("invalid_catalog_plaintext")
        return decoded

    def sign(self, payload: Mapping[str, Any]) -> str:
        return self.sign_bytes(canonical_catalog_bytes(payload))

    def sign_bytes(self, payload: bytes) -> str:
        if not isinstance(payload, bytes) or not payload:
            raise EmergencyCatalogCryptoError("invalid_signing_payload")
        return _b64url_no_padding(self._private_key.sign(payload))

    def verify(self, payload: Mapping[str, Any], signature_b64: str) -> None:
        self.verify_bytes(canonical_catalog_bytes(payload), signature_b64)

    def verify_bytes(self, payload: bytes, signature_b64: str) -> None:
        if not isinstance(payload, bytes) or not payload:
            raise EmergencyCatalogCryptoError("invalid_signing_payload")
        signature = _decode_b64url(
            signature_b64,
            expected_bytes=64,
            code="invalid_catalog_signature_encoding",
        )
        try:
            self._public_key.verify(signature, payload)
        except InvalidSignature as exc:
            raise EmergencyCatalogCryptoError("invalid_catalog_signature") from exc

    def signed_envelope(self, payload: Mapping[str, Any]) -> dict[str, str | int]:
        """Sign exact payload bytes so clients never need JSON canonicalization."""

        payload_bytes = canonical_catalog_bytes(payload)
        return {
            "schema_version": 1,
            "algorithm": "Ed25519",
            "key_id": self.key_id,
            "payload_b64": _b64url_no_padding(payload_bytes),
            "signature_b64": self.sign_bytes(payload_bytes),
        }
