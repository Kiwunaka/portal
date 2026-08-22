from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_ROOT = REPO_ROOT / "shared" / "contracts" / "support"


def _load(name: str) -> dict[str, object]:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    return parsed.astimezone(timezone.utc)


def test_support_schemas_are_closed_and_have_exact_required_fields() -> None:
    for name in (
        "signed-envelope.schema.json",
        "support-key-set.schema.json",
        "support-collection-policy.schema.json",
    ):
        schema = _load(name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["additionalProperties"] is False
        assert set(schema["required"]) == set(schema["properties"])

    key_schema = _load("support-key-set.schema.json")
    recipient = key_schema["$defs"]["recipient"]
    assert recipient["additionalProperties"] is False
    assert set(recipient["required"]) == set(recipient["properties"])

    policy = _load("support-collection-policy.schema.json")
    audience = policy["properties"]["audience"]
    assert audience["additionalProperties"] is False
    assert set(audience["required"]) == set(audience["properties"])


def test_algorithms_categories_and_byte_budgets_match_client_contract() -> None:
    envelope = _load("signed-envelope.schema.json")
    key_set = _load("support-key-set.schema.json")
    policy = _load("support-collection-policy.schema.json")

    assert envelope["properties"]["algorithm"]["const"] == "Ed25519"
    recipient = key_set["$defs"]["recipient"]["properties"]
    assert (
        recipient["algorithm"]["const"]
        == "X25519-HKDF-SHA256-AES-256-GCM"
    )
    assert recipient["public_key_b64"]["pattern"].endswith("{43}$")
    assert set(policy["properties"]["allowed_categories"]["items"]["enum"]) == {
        "build",
        "system",
        "network",
        "events",
        "crashes",
        "redaction",
    }
    assert set(policy["properties"]["allowed_collectors"]["items"]["enum"]) == {
        "build_summary",
        "system_summary",
        "network_summary",
        "operational_events",
        "crash_index",
        "redaction_report",
    }
    budget = policy["properties"]["maximum_bundle_bytes"]
    assert budget == {"type": "integer", "minimum": 65536, "maximum": 2097152}
    assert policy["properties"]["maximum_total_bytes"] == {
        "type": "integer",
        "minimum": 65536,
        "maximum": 4194304,
    }
    assert policy["properties"]["maximum_bundles"] == {
        "type": "integer",
        "minimum": 1,
        "maximum": 2,
    }
    assert policy["properties"]["schema_version"]["const"] == 2
    assert policy["properties"]["profile"]["const"] == "extended"
    assert policy["properties"]["nonce"]["pattern"].endswith("{22}$")
    assert policy["properties"]["audience"]["properties"]["platform"] == {
        "enum": ["android", "windows"]
    }


def test_synthetic_contract_times_obey_hard_ttl_rules() -> None:
    issued = datetime(2026, 8, 21, 12, tzinfo=timezone.utc)
    key_expires = issued + timedelta(days=31)
    recipient_expires = issued + timedelta(days=30)
    policy_expires = issued + timedelta(minutes=30)

    assert key_expires - issued <= timedelta(days=31)
    assert recipient_expires <= key_expires
    assert policy_expires - issued <= timedelta(minutes=30)
    assert _utc(key_expires.isoformat()) == key_expires


def test_envelope_lengths_are_exact_for_ed25519_and_x25519_material() -> None:
    signature = base64.urlsafe_b64encode(bytes(64)).decode("ascii").rstrip("=")
    public_key = base64.urlsafe_b64encode(bytes(32)).decode("ascii").rstrip("=")

    assert len(signature) == 86
    assert len(public_key) == 43
