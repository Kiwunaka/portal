from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from remote_set_owned_awg31_variant import (  # noqa: E402
    VariantError,
    _material_is_randomized,
    _material_with_randomized_variant,
    _replace_server_variant,
    _server_is_minimal,
    _server_is_randomized,
)


MINIMAL_CONFIG = b"""[Interface]
PrivateKey = redacted
ListenPort = 3478
S1 = 16
S2 = 16
S3 = 16
S4 = 16
H1 = 1100001-1100099
H2 = 1200001-1200099
H3 = 1300001-1300099
H4 = 1400001-1400099
HeaderProtectionKey = redacted

[Peer]
PublicKey = redacted
"""


def endpoint() -> dict[str, object]:
    return {
        "contract_id": "pokrov.awg31.endpoint.v1",
        "private_key": "redacted",
        "s1": 16,
        "s2": 16,
        "s3": 16,
        "s4": 16,
        "header_protection_key": "redacted",
        "content_padding_addition": "0",
        "random_trailers": False,
        "peers": [{"port": 3478}],
    }


def test_server_variant_transform_is_bounded_and_idempotent() -> None:
    assert _server_is_minimal(MINIMAL_CONFIG)
    transformed = _replace_server_variant(MINIMAL_CONFIG)
    assert _server_is_randomized(transformed)
    assert _replace_server_variant(transformed) == transformed
    assert b"ContentPaddingAddition = 0" in transformed
    assert b"RandomTrailers = true" in transformed
    assert _server_is_randomized(transformed.replace(b"true", b"on"))
    assert _server_is_randomized(
        transformed.replace(b"ContentPaddingAddition = 0\n", b"")
    )


def test_server_variant_rejects_unexpected_existing_value() -> None:
    unexpected = MINIMAL_CONFIG.replace(
        b"HeaderProtectionKey = redacted",
        b"HeaderProtectionKey = redacted\nContentPaddingAddition = 1-2",
    )
    with pytest.raises(VariantError, match="precondition"):
        _replace_server_variant(unexpected)


def test_material_variant_transform_is_bounded_and_idempotent() -> None:
    transformed = _material_with_randomized_variant(json.dumps(endpoint()).encode())
    assert _material_is_randomized(transformed)
    assert transformed["content_padding_addition"] == "0"
    assert transformed["random_trailers"] is True
    assert _material_with_randomized_variant(json.dumps(transformed).encode()) == transformed


def test_legacy_randomized_variant_migrates_to_mobile_safe_padding() -> None:
    legacy_config = _replace_server_variant(MINIMAL_CONFIG).replace(
        b"ContentPaddingAddition = 0",
        b"ContentPaddingAddition = 64-512",
    )
    legacy_endpoint = endpoint()
    legacy_endpoint["content_padding_addition"] = "64-512"
    legacy_endpoint["random_trailers"] = True

    transformed_config = _replace_server_variant(legacy_config)
    transformed_endpoint = _material_with_randomized_variant(
        json.dumps(legacy_endpoint).encode()
    )

    assert _server_is_randomized(transformed_config)
    assert b"ContentPaddingAddition = 0" in transformed_config
    assert transformed_endpoint["content_padding_addition"] == "0"
    assert transformed_endpoint["random_trailers"] is True


def test_material_variant_rejects_unknown_contract() -> None:
    value = endpoint()
    value["contract_id"] = "unknown"
    with pytest.raises(VariantError, match="precondition"):
        _material_with_randomized_variant(json.dumps(value).encode())
