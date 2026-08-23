from __future__ import annotations

import base64
import json
from datetime import date, datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from portal_bot.models import Base, SupportTicket
from portal_bot import support_mode_service as service


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


@pytest.fixture()
def configured(monkeypatch):
    private = Ed25519PrivateKey.generate()
    raw = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    monkeypatch.setenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", "support-root-test")
    monkeypatch.setenv("POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64", _b64(raw))
    monkeypatch.setenv("POKROV_SUPPORT_MODE_CODE_SECRET", "s" * 48)
    return private


@pytest.fixture()
def session(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'support-mode.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    db = factory()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _ticket(session) -> SupportTicket:
    row = SupportTicket(
        user_tg_id=1001,
        account_id="11111111-1111-4111-8111-111111111111",
        environment="production",
        status="open",
        subject="Support mode",
        version=1,
    )
    session.add(row)
    session.flush()
    return row


def _spec() -> service.SupportModeIssueSpec:
    return service.normalize_issue_spec(
        {
            "allowed_categories": ["build", "events", "network", "redaction"],
            "allowed_collectors": [
                "build_summary",
                "network_summary",
                "operational_events",
                "redaction_report",
            ],
            "app_version": "1.2.0+30",
            "build_number": "candidate-local-30",
            "maximum_bundle_bytes": 1024 * 1024,
            "maximum_bundles": 2,
            "maximum_total_bytes": 1536 * 1024,
            "platform": "windows",
            "ttl_minutes": 20,
        }
    )


def _payload(envelope: dict[str, object]) -> dict[str, object]:
    raw = str(envelope["payload_b64"])
    decoded = base64.urlsafe_b64decode(raw + "=" * ((4 - len(raw) % 4) % 4))
    return json.loads(decoded)


def test_issue_and_one_time_redeem_are_case_owner_and_audience_bound(
    configured, session
) -> None:
    now = datetime(2026, 8, 22, 12, tzinfo=timezone.utc)
    ticket = _ticket(session)
    issued = service.issue_support_mode(
        session,
        ticket=ticket,
        spec=_spec(),
        actor_tg_id=9999,
        now=now,
    )
    session.commit()

    assert issued.activation_code.startswith("PSM1-")
    assert issued.activation_code not in issued.row.activation_code_hash
    with pytest.raises(service.SupportModeError) as mismatch:
        service.redeem_support_mode(
            session,
            activation_code=issued.activation_code,
            owner_tg_id=1001,
            owner_account_id=ticket.account_id,
            platform="android",
            app_version="1.2.0+30",
            build_number="candidate-local-30",
            now=now + timedelta(minutes=1),
        )
    assert mismatch.value.code == "support_mode_audience_mismatch"
    session.rollback()

    redeemed = service.redeem_support_mode(
        session,
        activation_code=issued.activation_code.lower().replace("-", " "),
        owner_tg_id=1001,
        owner_account_id=ticket.account_id,
        platform="windows",
        app_version="1.2.0+30",
        build_number="candidate-local-30",
        now=now + timedelta(minutes=1),
    )
    session.commit()
    payload = _payload(redeemed.signed_policy)
    assert payload["schema_version"] == 2
    assert payload["audience"] == {
        "app_version": "1.2.0+30",
        "build_number": "candidate-local-30",
        "platform": "windows",
    }
    assert payload["maximum_bundles"] == 2
    assert payload["maximum_total_bytes"] == 1536 * 1024
    assert set(payload) == {
        "allowed_categories",
        "allowed_collectors",
        "audience",
        "expires_at",
        "issued_at",
        "maximum_bundle_bytes",
        "maximum_bundles",
        "maximum_total_bytes",
        "nonce",
        "policy_id",
        "profile",
        "schema_version",
        "type",
    }
    signature = base64.urlsafe_b64decode(
        str(redeemed.signed_policy["signature_b64"]) + "=="
    )
    payload_bytes = base64.urlsafe_b64decode(
        str(redeemed.signed_policy["payload_b64"]) + "="
    )
    configured.public_key().verify(signature, payload_bytes)

    with pytest.raises(service.SupportModeError) as replay:
        service.redeem_support_mode(
            session,
            activation_code=issued.activation_code,
            owner_tg_id=1001,
            owner_account_id=ticket.account_id,
            platform="windows",
            app_version="1.2.0+30",
            build_number="candidate-local-30",
            now=now + timedelta(minutes=2),
        )
    assert replay.value.code == "support_mode_code_consumed"


def test_policy_shape_rejects_remote_control_fields_and_collector_drift() -> None:
    raw = {
        "allowed_categories": ["events"],
        "allowed_collectors": ["operational_events"],
        "app_version": "1.2.0+30",
        "build_number": "30",
        "maximum_bundle_bytes": 65536,
        "maximum_bundles": 1,
        "maximum_total_bytes": 65536,
        "platform": "android",
        "ttl_minutes": 30,
    }
    with pytest.raises(service.SupportModeError) as remote:
        service.normalize_issue_spec({**raw, "command": "shell"})
    assert remote.value.code == "support_mode_issue_shape_invalid"
    with pytest.raises(service.SupportModeError) as drift:
        service.normalize_issue_spec(
            {**raw, "allowed_collectors": ["network_summary"]}
        )
    assert drift.value.code == "support_mode_collectors_invalid"


def test_signing_key_rejects_noncanonical_base64(monkeypatch) -> None:
    monkeypatch.setenv("POKROV_SUPPORT_MODE_SIGNING_KEY_ID", "support-root-test")
    monkeypatch.setenv(
        "POKROV_SUPPORT_MODE_SIGNING_PRIVATE_KEY_B64",
        f"{_b64(b'k' * 32)}!ignored",
    )

    with pytest.raises(service.SupportModeError) as rejected:
        service.SupportModeSigner.from_environment()

    assert rejected.value.code == "support_mode_signing_unavailable"


def _diagnostic_fixture_code() -> str:
    facts = (1 << 5) | (2 << 3) | 3  # windows, selected_apps, degraded
    issued_days = (date(2026, 8, 22) - date(2020, 1, 1)).days
    raw = bytes([facts]) + issued_days.to_bytes(2, "big") + bytes([1, 2, 0, 30, 0xAB, 0xCD])
    packed = raw + bytes([service._crc8(raw)])
    value = int.from_bytes(packed, "big")
    body = service._crockford_from_int(value, 16)
    return f"PSD1-{body[:4]}-{body[4:8]}-{body[8:12]}-{body[12:]}"


def test_versioned_diagnostic_code_decodes_without_bundle_or_identity() -> None:
    code = _diagnostic_fixture_code()
    decoded = service.decode_diagnostic_code(code.lower(), today=date(2026, 8, 23))

    assert code == "PSD1-6C4Q-J082-00FA-QK8B"
    assert decoded == {
        "schema_version": 1,
        "platform": "windows",
        "route_mode": "selected_apps",
        "connection_state": "degraded",
        "app_version": "1.2.0",
        "build_number": 30,
        "diagnostic_hash_prefix": "abcd",
        "issued_on": "2026-08-22",
        "expires_on": "2026-09-05",
        "expired": False,
        "contains_identity": False,
    }
