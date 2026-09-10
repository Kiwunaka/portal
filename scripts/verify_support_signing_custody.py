from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey


KEY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
SEED_KEYS = {
    "schema_version",
    "algorithm",
    "purpose",
    "status",
    "key_id",
    "public_key_b64url",
    "public_key_sha256",
}


class CustodyVerificationError(ValueError):
    pass


def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_b64url(value: object, *, exact_bytes: int, field: str) -> bytes:
    if not isinstance(value, str) or not value or re.fullmatch(r"[A-Za-z0-9_-]+", value) is None:
        raise CustodyVerificationError(f"{field} is not canonical base64url")
    padded = value + ("=" * ((4 - len(value) % 4) % 4))
    try:
        decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
    except (ValueError, TypeError) as exc:
        raise CustodyVerificationError(f"{field} is not canonical base64url") from exc
    if len(decoded) != exact_bytes or _b64url(decoded) != value:
        raise CustodyVerificationError(f"{field} is not canonical {exact_bytes}-byte base64url")
    return decoded


def _load_seed(path: Path) -> tuple[bytes, Mapping[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CustodyVerificationError("client support signing seed is unreadable or invalid") from exc
    if not isinstance(payload, dict) or set(payload) != SEED_KEYS:
        raise CustodyVerificationError("client support signing seed has an invalid closed schema")
    if (
        payload.get("schema_version") != 1
        or payload.get("algorithm") != "Ed25519"
        or payload.get("purpose") != "support-mode-policy-v2"
        or payload.get("status") != "active"
    ):
        raise CustodyVerificationError("client support signing seed identity is invalid")
    key_id = payload.get("key_id")
    if not isinstance(key_id, str) or KEY_ID_RE.fullmatch(key_id) is None:
        raise CustodyVerificationError("client support signing key id is invalid")
    public_key = _decode_b64url(
        payload.get("public_key_b64url"),
        exact_bytes=32,
        field="client public key",
    )
    expected_digest = payload.get("public_key_sha256")
    actual_digest = hashlib.sha256(public_key).hexdigest()
    if not isinstance(expected_digest, str) or not hmac.compare_digest(expected_digest, actual_digest):
        raise CustodyVerificationError("client public key digest is invalid")
    return raw, payload, public_key


def _require_revision(value: str, *, field: str) -> str:
    normalized = str(value or "").strip()
    if REVISION_RE.fullmatch(normalized) is None:
        raise CustodyVerificationError(f"{field} must be an exact lowercase 40-hex revision")
    return normalized


def verify_custody(
    *,
    client_seed_path: Path,
    platform_revision: str,
    client_revision: str,
    key_id: str,
    private_key_b64url: str,
    public_key_b64url: str,
    code_secret: str,
) -> dict[str, Any]:
    platform_revision = _require_revision(platform_revision, field="platform revision")
    client_revision = _require_revision(client_revision, field="client revision")
    seed_bytes, seed, seed_public_key = _load_seed(client_seed_path)

    normalized_key_id = str(key_id or "").strip().lower()
    if KEY_ID_RE.fullmatch(normalized_key_id) is None or not hmac.compare_digest(
        normalized_key_id,
        str(seed["key_id"]),
    ):
        raise CustodyVerificationError("hosted support signing key id does not match the client seed")

    private_key_bytes = _decode_b64url(
        str(private_key_b64url or "").strip(),
        exact_bytes=32,
        field="hosted private key",
    )
    hosted_public_value = str(public_key_b64url or "").strip()
    hosted_public_key = _decode_b64url(
        hosted_public_value,
        exact_bytes=32,
        field="hosted public key",
    )
    if not hmac.compare_digest(hosted_public_key, seed_public_key):
        raise CustodyVerificationError("hosted public key does not match the client seed")

    if len(str(code_secret or "").encode("utf-8")) < 32:
        raise CustodyVerificationError("hosted support-mode code secret is unavailable")

    try:
        private_key = Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        derived_public_key = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
    except ValueError as exc:
        raise CustodyVerificationError("hosted private key is not a valid Ed25519 seed") from exc
    if not hmac.compare_digest(derived_public_key, seed_public_key):
        raise CustodyVerificationError("hosted private key does not match the client public pin")

    challenge = (
        f"POKROV:support-mode-custody:v1:{platform_revision}:{client_revision}"
    ).encode("ascii")
    signature = private_key.sign(challenge)
    try:
        private_key.public_key().verify(signature, challenge)
    except InvalidSignature as exc:
        raise CustodyVerificationError("hosted Ed25519 signing self-check failed") from exc

    public_digest = hashlib.sha256(seed_public_key).hexdigest()
    return {
        "schema": "pokrov.support-mode-signing-custody-receipt.v1",
        "status": "PASS",
        "scope": "hosted_source_control_custody",
        "candidate_created": False,
        "algorithm": "Ed25519",
        "key_id": normalized_key_id,
        "public_key_b64url": hosted_public_value,
        "public_key_sha256": public_digest,
        "client_seed_sha256": hashlib.sha256(seed_bytes).hexdigest(),
        "challenge_sha256": hashlib.sha256(challenge).hexdigest(),
        "platform_revision": platform_revision,
        "client_revision": client_revision,
        "code_secret_contract": "present_minimum_32_utf8_bytes",
        "production_runtime_mutated": False,
    }


def _write_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dict(receipt), ensure_ascii=True, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise CustodyVerificationError("public custody receipt could not be written") from exc


def _sign_recipient_key_set(
    *,
    signing_key_id: str,
    private_key_b64url: str,
    recipient_key_id: str,
    recipient_public_key_b64url: str,
    now: datetime,
) -> dict[str, Any]:
    if KEY_ID_RE.fullmatch(recipient_key_id) is None:
        raise CustodyVerificationError("recipient key id is invalid")
    public_key = _decode_b64url(
        recipient_public_key_b64url, exact_bytes=32, field="recipient public key"
    )
    try:
        X25519PrivateKey.generate().exchange(X25519PublicKey.from_public_bytes(public_key))
    except ValueError as exc:
        raise CustodyVerificationError("recipient public key cannot establish a shared secret") from exc
    expires = now + timedelta(days=30)
    payload = {
        "schema_version": 1,
        "type": "pokrov.support.key_set",
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "keys": [{
            "algorithm": "X25519-HKDF-SHA256-AES-256-GCM",
            "key_id": recipient_key_id,
            "not_after": expires.isoformat(),
            "public_key_b64": recipient_public_key_b64url,
        }],
    }
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    private_key = Ed25519PrivateKey.from_private_bytes(
        _decode_b64url(private_key_b64url, exact_bytes=32, field="hosted private key")
    )
    return {
        "schema_version": 1,
        "algorithm": "Ed25519",
        "key_id": signing_key_id,
        "payload_b64": _b64url(raw),
        "signature_b64": _b64url(private_key.sign(raw)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify hosted support-mode signing custody against the tracked client public pin."
    )
    parser.add_argument("--client-seed", type=Path, required=True)
    parser.add_argument("--platform-revision", required=True)
    parser.add_argument("--client-revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--signed-key-set-output", type=Path)
    args = parser.parse_args(argv)
    try:
        receipt = verify_custody(
            client_seed_path=args.client_seed,
            platform_revision=args.platform_revision,
            client_revision=args.client_revision,
            key_id=os.getenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", ""),
            private_key_b64url=os.getenv("POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64", ""),
            public_key_b64url=os.getenv("POKROV_SUPPORT_MODE_SIGNING_PUBLIC_KEY_B64", ""),
            code_secret=os.getenv("POKROV_SUPPORT_MODE_CODE_SECRET", ""),
        )
        recipient_key_id = os.getenv("POKROV_SUPPORT_RECIPIENT_KEY_ID", "")
        recipient_public_key = os.getenv("POKROV_SUPPORT_RECIPIENT_PUBLIC_KEY_B64", "")
        if recipient_key_id or recipient_public_key:
            if args.signed_key_set_output is None:
                raise CustodyVerificationError("signed public key-set output is required")
            envelope = _sign_recipient_key_set(
                signing_key_id=str(receipt["key_id"]),
                private_key_b64url=os.getenv("POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64", "").strip(),
                recipient_key_id=recipient_key_id,
                recipient_public_key_b64url=recipient_public_key,
                now=datetime.now(timezone.utc),
            )
            _write_receipt(args.signed_key_set_output, envelope)
        _write_receipt(args.output, receipt)
    except CustodyVerificationError as exc:
        print(f"Support signing custody verification failed: {exc}", file=sys.stderr)
        return 1
    print(
        "Support signing custody verified: "
        f"key_id={receipt['key_id']} public_key_sha256={receipt['public_key_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
