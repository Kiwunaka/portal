from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))

import migrations  # noqa: E402
import models  # noqa: E402
from emergency_catalog_crypto import (  # noqa: E402
    EmergencyCatalogCrypto,
    EmergencyCatalogCryptoError,
)
from emergency_catalog_service import (  # noqa: E402
    disable_active_catalog,
    EmergencyCatalogServiceError,
    EndpointProbeResult,
    promote_snapshot,
    read_serving_catalog,
    read_serving_endpoint_material,
    rollback_candidates,
    rollback_to_snapshot,
    safe_promotion_delta,
    stage_snapshot,
)
from emergency_catalog_source import parse_emergency_source  # noqa: E402
from emergency_eligibility_service import (  # noqa: E402
    record_trusted_country,
    resolve_emergency_eligibility,
)


EXPECTED_PAYLOAD_SHA256 = hashlib.sha256(b"pokrov-emergency-probe-v1").hexdigest()
NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def session(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'emergency.db').as_posix()}")
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as value:
        yield value
    engine.dispose()


@pytest.fixture()
def crypto() -> EmergencyCatalogCrypto:
    return EmergencyCatalogCrypto.generate_for_tests()


def _material(index: int, *, host_slot: int | None = None):
    token = f"{index:08x}"
    host = host_slot if host_slot is not None else index
    key_char = chr(ord("A") + (index % 20))
    line = (
        f"vless://{index:08x}-1111-4111-8111-{index:012x}"
        f"@reserve-{host}.example.com:443?type=tcp&security=reality"
        f"&pbk={key_char * 43}&sid={token[:8]}&sni=cover-{index}.example.com"
        "&fp=chrome&flow=xtls-rprx-vision&encryption=none"
    )
    result = parse_emergency_source(line)
    assert not result.rejected
    return result.accepted[0]


def _probe(material, *, country: str = "FR", at: datetime = NOW, ok: bool = True):
    return EndpointProbeResult(
        authenticated=ok,
        payload_ok=ok,
        payload_sha256=EXPECTED_PAYLOAD_SHA256,
        exit_country=country,
        latency_ms=20 + int(material.stable_id[-2:], 16) % 200,
        verified_at=at,
    )


def _stage(
    session,
    crypto,
    materials,
    *,
    digest_char: str,
    now: datetime = NOW,
    probes=None,
):
    values = list(materials)
    probe_map = probes or {item.stable_id: _probe(item, at=now) for item in values}
    return stage_snapshot(
        session,
        materials=values,
        source_revision=digest_char * 40,
        source_digest=digest_char * 64,
        crypto=crypto,
        probes=probe_map,
        expected_payload_sha256=EXPECTED_PAYLOAD_SHA256,
        now=now,
    ).snapshot


def test_crypto_encrypts_and_signs_with_tamper_rejection(crypto) -> None:
    payload = {"schema": "test", "nested": {"value": 1}}
    ciphertext = crypto.encrypt_json(payload)
    signature = crypto.sign(payload)

    assert crypto.decrypt_json(ciphertext) == payload
    crypto.verify(payload, signature)
    with pytest.raises(EmergencyCatalogCryptoError, match="invalid_catalog_signature"):
        crypto.verify({"schema": "tampered"}, signature)
    with pytest.raises(EmergencyCatalogCryptoError, match="invalid_catalog_ciphertext"):
        crypto.decrypt_json(ciphertext[:-2] + "xx")


def test_staging_stores_only_encrypted_material_and_is_recently_idempotent(session, crypto) -> None:
    materials = [_material(index) for index in range(1, 5)]

    first = _stage(session, crypto, materials, digest_char="a")
    second = stage_snapshot(
        session,
        materials=materials,
        source_revision="a" * 40,
        source_digest="a" * 64,
        crypto=crypto,
        probes={},
        expected_payload_sha256=EXPECTED_PAYLOAD_SHA256,
        now=NOW + timedelta(minutes=10),
    )
    rows = session.query(models.EmergencyCatalogEndpoint).filter_by(snapshot_id=first.id).all()

    assert second.created is False
    assert second.snapshot.id == first.id
    assert first.healthy_count == 4
    assert len(rows) == 4
    assert all("reserve-" not in row.material_ciphertext for row in rows)
    assert all(row.material_hash not in row.material_ciphertext for row in rows)


def test_promotion_requires_four_unique_fresh_authenticated_non_ru_hosts(session, crypto) -> None:
    duplicate_host = [_material(index, host_slot=1) for index in range(1, 5)]
    snapshot = _stage(session, crypto, duplicate_host, digest_char="b")

    with pytest.raises(EmergencyCatalogServiceError, match="insufficient_healthy_endpoints"):
        promote_snapshot(session, snapshot_id=snapshot.id, crypto=crypto, now=NOW)

    assert snapshot.status == "staging"
    assert snapshot.rejection_code == "insufficient_healthy_endpoints"


def test_promoted_catalog_is_signed_bounded_and_served(session, crypto) -> None:
    materials = [_material(index) for index in range(1, 7)]
    snapshot = _stage(session, crypto, materials, digest_char="c")

    promoted = promote_snapshot(session, snapshot_id=snapshot.id, crypto=crypto, now=NOW)
    served = read_serving_catalog(session, crypto=crypto, now=NOW + timedelta(hours=1))

    assert promoted.snapshot.status == "active"
    assert promoted.snapshot.active_endpoint_count == 6
    assert len(promoted.selected_stable_ids) == 6
    assert served["catalog_version"] == snapshot.catalog_version
    assert len(served["endpoints"]) == 6
    assert all(item["supported_chain_modes"] == [
        "reserve_direct",
        "reserve_foreign",
        "reserve_ru_foreign",
    ] for item in served["endpoints"])


def test_profile_material_rejects_stale_probe_before_catalog_expiry(session, crypto) -> None:
    staged = _stage(
        session,
        crypto,
        [_material(index) for index in range(1, 5)],
        digest_char="f",
    )
    promoted = promote_snapshot(session, snapshot_id=staged.id, crypto=crypto, now=NOW)

    with pytest.raises(EmergencyCatalogServiceError, match="serving_endpoint_stale"):
        read_serving_endpoint_material(
            session,
            stable_id=promoted.selected_stable_ids[0],
            crypto=crypto,
            now=NOW + timedelta(hours=25),
        )


def test_operator_disable_stops_distribution_and_requires_explicit_reactivation(session, crypto) -> None:
    first = _stage(session, crypto, [_material(index) for index in range(1, 5)], digest_char="8")
    promote_snapshot(session, snapshot_id=first.id, crypto=crypto, now=NOW)
    second = _stage(
        session,
        crypto,
        [_material(index) for index in (1, 2, 5, 6)],
        digest_char="9",
        now=NOW + timedelta(hours=1),
    )

    delta = safe_promotion_delta(
        session,
        snapshot_id=second.id,
        crypto=crypto,
        now=NOW + timedelta(hours=1),
    )
    disabled = disable_active_catalog(
        session,
        snapshot_id=first.id,
        now=NOW + timedelta(hours=1, minutes=1),
    )

    assert delta == {
        "distribution_state": "active",
        "current_count": 4,
        "next_count": 4,
        "retained_count": 2,
        "removed_count": 2,
        "added_count": 2,
        "replacement_percent": 50.0,
        "automatic_limit_exceeded": False,
    }
    assert disabled.status == "disabled"
    with pytest.raises(EmergencyCatalogServiceError, match="catalog_distribution_disabled"):
        read_serving_catalog(session, crypto=crypto, now=NOW + timedelta(hours=1, minutes=2))
    with pytest.raises(EmergencyCatalogServiceError, match="catalog_distribution_disabled"):
        promote_snapshot(
            session,
            snapshot_id=second.id,
            crypto=crypto,
            now=NOW + timedelta(hours=1, minutes=2),
        )

    promoted = promote_snapshot(
        session,
        snapshot_id=second.id,
        crypto=crypto,
        operator_approved=True,
        now=NOW + timedelta(hours=1, minutes=3),
    )
    assert promoted.snapshot.status == "active"
    assert first.status == "superseded"


def test_automatic_churn_over_half_is_blocked_without_replacing_active(session, crypto) -> None:
    first_materials = [_material(index) for index in range(1, 5)]
    first = _stage(session, crypto, first_materials, digest_char="d")
    promote_snapshot(session, snapshot_id=first.id, crypto=crypto, now=NOW)
    next_materials = [_material(index) for index in (1, 5, 6, 7)]
    second = _stage(
        session,
        crypto,
        next_materials,
        digest_char="e",
        now=NOW + timedelta(hours=1),
    )

    with pytest.raises(EmergencyCatalogServiceError, match="automatic_churn_limit"):
        promote_snapshot(
            session,
            snapshot_id=second.id,
            crypto=crypto,
            now=NOW + timedelta(hours=1),
        )

    assert first.status == "active"
    assert second.status == "staging"
    assert second.rejection_code == "automatic_churn_limit"


def test_operator_can_promote_large_churn_and_lkg_survives_active_tamper(session, crypto) -> None:
    first = _stage(session, crypto, [_material(index) for index in range(1, 5)], digest_char="f")
    promote_snapshot(session, snapshot_id=first.id, crypto=crypto, now=NOW)
    second = _stage(
        session,
        crypto,
        [_material(index) for index in range(5, 9)],
        digest_char="1",
        now=NOW + timedelta(hours=1),
    )
    promote_snapshot(
        session,
        snapshot_id=second.id,
        crypto=crypto,
        operator_approved=True,
        now=NOW + timedelta(hours=1),
    )
    second.signature_b64 = "A" * 86
    session.flush()

    served = read_serving_catalog(session, crypto=crypto, now=NOW + timedelta(hours=2))

    assert first.status == "superseded"
    assert second.status == "active"
    assert served["catalog_version"] == first.catalog_version


def test_one_step_rollback_reissues_retained_snapshot_as_new_version(session, crypto) -> None:
    first = _stage(session, crypto, [_material(index) for index in range(1, 5)], digest_char="2")
    promote_snapshot(session, snapshot_id=first.id, crypto=crypto, now=NOW)
    second = _stage(
        session,
        crypto,
        [_material(index) for index in (1, 2, 5, 6)],
        digest_char="3",
        now=NOW + timedelta(hours=1),
    )
    promote_snapshot(session, snapshot_id=second.id, crypto=crypto, now=NOW + timedelta(hours=1))

    assert [item["snapshot_id"] for item in rollback_candidates(session)] == [first.id]
    rolled_back = rollback_to_snapshot(
        session,
        target_snapshot_id=first.id,
        crypto=crypto,
        now=NOW + timedelta(hours=2),
    )
    served = read_serving_catalog(session, crypto=crypto, now=NOW + timedelta(hours=2))

    assert rolled_back.snapshot.status == "active"
    assert rolled_back.snapshot.rollback_of_snapshot_id == first.id
    assert rolled_back.snapshot.catalog_version not in {first.catalog_version, second.catalog_version}
    assert {item["stable_id"] for item in served["endpoints"]} == {
        item.stable_id for item in [_material(index) for index in range(1, 5)]
    }


def test_rollback_reissues_only_the_endpoints_signed_into_the_target(session, crypto) -> None:
    materials = [_material(index) for index in range(1, 14)]
    first = _stage(session, crypto, materials, digest_char="4")
    promoted = promote_snapshot(session, snapshot_id=first.id, crypto=crypto, now=NOW)
    retained_ids = set(promoted.selected_stable_ids)
    omitted_id = next(item.stable_id for item in materials if item.stable_id not in retained_ids)
    omitted = (
        session.query(models.EmergencyCatalogEndpoint)
        .filter_by(snapshot_id=first.id, stable_id=omitted_id)
        .one()
    )
    omitted.latency_ms = 0

    second = _stage(
        session,
        crypto,
        [_material(index) for index in range(1, 5)],
        digest_char="5",
        now=NOW + timedelta(hours=1),
    )
    promote_snapshot(
        session,
        snapshot_id=second.id,
        crypto=crypto,
        operator_approved=True,
        now=NOW + timedelta(hours=1),
    )
    rollback_to_snapshot(
        session,
        target_snapshot_id=first.id,
        crypto=crypto,
        now=NOW + timedelta(hours=2),
    )
    served = read_serving_catalog(session, crypto=crypto, now=NOW + timedelta(hours=2))

    assert {item["stable_id"] for item in served["endpoints"]} == retained_ids
    assert omitted_id not in retained_ids


def test_legacy_sqlite_migration_creates_emergency_tables_idempotently(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    legacy_tables = [
        table
        for table in models.Base.metadata.sorted_tables
        if table.name not in {
            "emergency_catalog_snapshots",
            "emergency_catalog_endpoints",
            "emergency_eligibility_cache",
        }
    ]
    models.Base.metadata.create_all(engine, tables=legacy_tables)

    migrations.run_migrations(engine)
    migrations.run_migrations(engine)
    schema = inspect(engine)

    assert {
        "emergency_catalog_snapshots",
        "emergency_catalog_endpoints",
        "emergency_eligibility_cache",
    }.issubset(
        schema.get_table_names()
    )
    assert {column["name"] for column in schema.get_columns("emergency_catalog_snapshots")} >= {
        "catalog_ciphertext",
        "signature_b64",
        "rollback_of_snapshot_id",
        "expires_at",
    }
    assert {column["name"] for column in schema.get_columns("emergency_catalog_endpoints")} >= {
        "material_ciphertext",
        "endpoint_host_hash",
        "authenticated",
        "payload_ok",
        "verified_at",
    }
    engine.dispose()


def test_eligibility_is_only_trial_paid_plus_cached_ru_or_explicit_manual(session) -> None:
    denied = resolve_emergency_eligibility(
        session,
        account_id="account-1",
        install_id="install-12345678",
        access_state="bonus_premium",
        manual_limited_network=True,
        now=NOW,
    )
    unknown = resolve_emergency_eligibility(
        session,
        account_id="account-1",
        install_id="install-12345678",
        access_state="trial_premium",
        manual_limited_network=False,
        now=NOW,
    )
    manual = resolve_emergency_eligibility(
        session,
        account_id="account-1",
        install_id="install-12345678",
        access_state="paid_unlimited",
        manual_limited_network=True,
        now=NOW,
    )
    record_trusted_country(
        session,
        account_id="account-1",
        install_id="install-12345678",
        country_code="RU",
        source="owned_geoip",
        now=NOW,
    )
    cached = resolve_emergency_eligibility(
        session,
        account_id="account-1",
        install_id="install-12345678",
        access_state="trial_premium",
        manual_limited_network=False,
        now=NOW + timedelta(hours=1),
    )

    assert denied.source == "access_denied" and denied.eligible is False
    assert unknown.source == "country_unknown" and unknown.eligible is False
    assert manual.source == "manual_limited_network" and manual.eligible is True
    assert cached.source == "cached_server_country" and cached.eligible is True
