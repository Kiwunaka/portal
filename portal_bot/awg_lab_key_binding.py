"""Keep an AWG server peer key bound to its original lab device."""

from __future__ import annotations

import base64
import hashlib

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from sqlalchemy import text


class AwgDeviceKeyError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _client_public_key(endpoint) -> bytes:
    private = base64.b64decode(endpoint["private_key"], validate=True)
    return X25519PrivateKey.from_private_bytes(private).public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw,
    )


def require_awg_device_key_binding(
    session, *, model, decrypt_endpoint, endpoint, tg_id: int, install_id: str,
    for_update: bool = True,
) -> None:
    public = _client_public_key(endpoint)
    if for_update and session.get_bind().dialect.name == "postgresql":
        # Different devices otherwise lock different rows. Serialize requests
        # for this peer key, including its first insertion, until commit.
        digest = hashlib.sha256(model.__tablename__.encode() + b":" + public).digest()
        session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"),
            {"key": int.from_bytes(digest[:8], "big", signed=True)},
        )
    for row in session.query(model).order_by(model.id).yield_per(100):
        try:
            existing_public = _client_public_key(decrypt_endpoint(row.endpoint_ciphertext))
        except Exception:
            raise AwgDeviceKeyError("material_key_binding_unavailable") from None
        if existing_public != public:
            continue
        if (int(row.tg_id), str(row.install_id)) != (int(tg_id), str(install_id)):
            raise AwgDeviceKeyError("material_key_already_bound")
        if row.state == "revoked":
            raise AwgDeviceKeyError("material_key_revoked")
