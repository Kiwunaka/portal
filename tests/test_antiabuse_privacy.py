from __future__ import annotations

import hashlib
import hmac
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


from antiabuse_privacy_service import (  # noqa: E402
    AntiAbusePolicyError,
    RETENTION_SWEEP_MAX_SECONDS,
    cleanup_antiabuse_retention,
    drain_antiabuse_retention,
    install_hmac_candidates,
    ip_hmac_candidates,
    record_antiabuse_event,
    retention_backlog_counts,
    set_operator_hard_lock,
)
from models import (  # noqa: E402
    AntiAbuseAction,
    AntiAbuseCase,
    AntiAbuseEvent,
    Base,
    SecurityEvent,
    User,
)


NOW = datetime(2026, 7, 12, 9, 30, 0)


def _session_for(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'antiabuse-privacy.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _expected_hmac(*, secret: str, purpose: str, version: int, value: str) -> str:
    payload = f"pokrov-antiabuse:{purpose}:v{version}:{value}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def test_record_event_normalizes_ipv6_and_domain_separates_hmacs(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "antiabuse-test-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "3")
    engine, session = _session_for(tmp_path)
    try:
        row = record_antiabuse_event(
            session,
            event_kind="trial_reserved",
            source="client_api",
            occurred_at=NOW,
            account_id="account-1",
            device_id="device-1",
            session_id="session-1",
            install_id="install-123",
            raw_ip=" 2001:0db8:0000:0000:0000:0000:0000:0001 ",
            reasons=["first_install"],
            metadata={"platform": "android", "refresh_token": "must-not-survive"},
        )
        session.flush()

        assert row.raw_ip == "2001:db8::1"
        assert row.raw_ip_expires_at == NOW + timedelta(hours=72, seconds=-RETENTION_SWEEP_MAX_SECONDS)
        assert row.hmac_version == 3
        assert row.ip_full_hmac == _expected_hmac(
            secret="antiabuse-test-secret",
            purpose="ip-full",
            version=3,
            value="2001:db8::1",
        )
        assert row.ip_prefix_hmac == _expected_hmac(
            secret="antiabuse-test-secret",
            purpose="ip-prefix",
            version=3,
            value="2001:db8::/64",
        )
        assert row.install_hmac == _expected_hmac(
            secret="antiabuse-test-secret",
            purpose="install-id",
            version=3,
            value="install-123",
        )
        assert len({row.ip_full_hmac, row.ip_prefix_hmac, row.install_hmac}) == 3
        assert "must-not-survive" not in str(row.metadata_json)
        assert "[redacted]" in str(row.metadata_json)
    finally:
        session.close()
        engine.dispose()


def test_record_event_metadata_remains_valid_bounded_json(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "antiabuse-test-secret")
    engine, session = _session_for(tmp_path)
    try:
        row = record_antiabuse_event(
            session,
            event_kind="metadata_test",
            source="test",
            occurred_at=NOW,
            metadata={f"field_{index}": "x" * 500 for index in range(100)},
        )
        session.flush()

        parsed = json.loads(str(row.metadata_json))
        assert len(parsed) == 20
        assert all(len(value) == 240 for value in parsed.values())
    finally:
        session.close()
        engine.dispose()


def test_record_event_uses_ipv4_24_prefix(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "antiabuse-test-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "4")
    engine, session = _session_for(tmp_path)
    try:
        row = record_antiabuse_event(
            session,
            event_kind="security_signal",
            source="api_security",
            occurred_at=NOW,
            raw_ip="198.51.100.87",
        )
        session.flush()

        assert row.ip_prefix_hmac == _expected_hmac(
            secret="antiabuse-test-secret",
            purpose="ip-prefix",
            version=4,
            value="198.51.100.0/24",
        )
    finally:
        session.close()
        engine.dispose()


def test_ip_hmac_candidates_cover_current_and_explicit_previous_versions(monkeypatch) -> None:
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "current-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "3")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET_V1", "first-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET_V2", "second-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET_V99", "future-secret-must-not-load")

    candidates = ip_hmac_candidates("198.51.100.87")

    assert [candidate.version for candidate in candidates] == [3, 2, 1]
    assert candidates[0].full_hmac == _expected_hmac(
        secret="current-secret",
        purpose="ip-full",
        version=3,
        value="198.51.100.87",
    )
    assert candidates[1].prefix_hmac == _expected_hmac(
        secret="second-secret",
        purpose="ip-prefix",
        version=2,
        value="198.51.100.0/24",
    )
    assert candidates[2].full_hmac == _expected_hmac(
        secret="first-secret",
        purpose="ip-full",
        version=1,
        value="198.51.100.87",
    )


def test_install_hmac_candidates_cover_current_and_previous_versions(monkeypatch) -> None:
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET", "current-secret")
    monkeypatch.setenv("ANTIABUSE_HMAC_VERSION", "2")
    monkeypatch.setenv("ANTIABUSE_HMAC_SECRET_V1", "first-secret")

    candidates = install_hmac_candidates("install-123")

    assert [candidate.version for candidate in candidates] == [2, 1]
    assert candidates[0].install_hmac == _expected_hmac(
        secret="current-secret",
        purpose="install-id",
        version=2,
        value="install-123",
    )
    assert candidates[1].install_hmac == _expected_hmac(
        secret="first-secret",
        purpose="install-id",
        version=1,
        value="install-123",
    )


def test_record_event_degrades_without_secret(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("ANTIABUSE_HMAC_SECRET", raising=False)
    monkeypatch.delenv("WEBAPP_SESSION_SECRET", raising=False)
    engine, session = _session_for(tmp_path)
    try:
        row = record_antiabuse_event(
            session,
            event_kind="security_signal",
            source="api_security",
            occurred_at=NOW,
            install_id="install-456",
            raw_ip="198.51.100.87",
        )
        session.flush()

        assert row.raw_ip == "198.51.100.87"
        assert row.raw_ip_expires_at == NOW + timedelta(hours=72, seconds=-RETENTION_SWEEP_MAX_SECONDS)
        assert row.ip_full_hmac is None
        assert row.ip_prefix_hmac is None
        assert row.install_hmac is None
        assert row.hmac_version is None
    finally:
        session.close()
        engine.dispose()


def test_cleanup_nulls_expired_ip_fields_without_deleting_audit(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    try:
        rows = [
            AntiAbuseEvent(
                id="raw-expired",
                event_kind="signal",
                source="test",
                occurred_at=NOW - timedelta(days=1),
                raw_ip="198.51.100.1",
                raw_ip_expires_at=NOW,
                ip_full_hmac="full-fresh",
                ip_prefix_hmac="prefix-fresh",
                hmac_version=1,
            ),
            AntiAbuseEvent(
                id="full-expired",
                event_kind="signal",
                source="test",
                occurred_at=NOW - timedelta(days=7),
                ip_full_hmac="full-expired",
                ip_prefix_hmac="prefix-seven-days",
                hmac_version=1,
            ),
            AntiAbuseEvent(
                id="prefix-expired",
                event_kind="signal",
                source="test",
                occurred_at=NOW - timedelta(days=90),
                ip_full_hmac="full-old",
                ip_prefix_hmac="prefix-expired",
                hmac_version=1,
            ),
        ]
        session.add_all(rows)
        session.add_all(
            [
                SecurityEvent(event_type="old", client_ip="203.0.113.1", created_at=NOW - timedelta(hours=72)),
                SecurityEvent(
                    event_type="fresh",
                    client_ip="203.0.113.2",
                    created_at=NOW - timedelta(hours=70, minutes=30),
                ),
                User(
                    tg_id=1001,
                    uuid="00000000-0000-0000-0000-000000001001",
                    email="APP_1001",
                    app_last_ip="192.0.2.1",
                    app_last_seen_at=NOW - timedelta(hours=72),
                ),
                User(
                    tg_id=1002,
                    uuid="00000000-0000-0000-0000-000000001002",
                    email="APP_1002",
                    app_last_ip="192.0.2.2",
                    app_last_seen_at=NOW - timedelta(hours=70, minutes=30),
                ),
            ]
        )
        session.commit()

        counts = cleanup_antiabuse_retention(session, now=NOW, batch_limit=100)
        session.commit()

        assert counts == {
            "antiabuse_raw_ip": 1,
            "antiabuse_full_hmac": 2,
            "antiabuse_prefix_hmac": 1,
            "security_event_ip": 1,
            "user_last_ip": 1,
        }
        assert session.query(AntiAbuseEvent).count() == 3
        assert session.get(AntiAbuseEvent, "raw-expired").raw_ip is None
        assert session.get(AntiAbuseEvent, "raw-expired").ip_full_hmac == "full-fresh"
        assert session.get(AntiAbuseEvent, "full-expired").ip_full_hmac is None
        assert session.get(AntiAbuseEvent, "full-expired").ip_prefix_hmac == "prefix-seven-days"
        assert session.get(AntiAbuseEvent, "prefix-expired").ip_prefix_hmac is None

        security_rows = {row.event_type: row for row in session.query(SecurityEvent).all()}
        assert security_rows["old"].client_ip is None
        assert security_rows["fresh"].client_ip == "203.0.113.2"
        assert session.get(User, 1001).app_last_ip is None
        assert session.get(User, 1002).app_last_ip == "192.0.2.2"
    finally:
        session.close()
        engine.dispose()


def test_cleanup_respects_per_field_batch_limit(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    try:
        for index in range(3):
            session.add(
                AntiAbuseEvent(
                    id=f"expired-{index}",
                    event_kind="signal",
                    source="test",
                    occurred_at=NOW - timedelta(days=100),
                    raw_ip=f"192.0.2.{index + 1}",
                    raw_ip_expires_at=NOW - timedelta(days=1),
                    ip_full_hmac=f"full-{index}",
                    ip_prefix_hmac=f"prefix-{index}",
                    hmac_version=1,
                )
            )
        session.commit()

        counts = cleanup_antiabuse_retention(session, now=NOW, batch_limit=2)
        session.commit()

        assert counts["antiabuse_raw_ip"] == 2
        assert counts["antiabuse_full_hmac"] == 2
        assert counts["antiabuse_prefix_hmac"] == 2
        assert session.query(AntiAbuseEvent).filter(AntiAbuseEvent.raw_ip.is_not(None)).count() == 1
        assert session.query(AntiAbuseEvent).filter(AntiAbuseEvent.ip_full_hmac.is_not(None)).count() == 1
        assert session.query(AntiAbuseEvent).filter(AntiAbuseEvent.ip_prefix_hmac.is_not(None)).count() == 1
    finally:
        session.close()
        engine.dispose()


def test_drain_clears_all_due_batches_and_reports_zero_backlog(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'antiabuse-drain.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        for index in range(5):
            session.add(
                AntiAbuseEvent(
                    id=f"drain-{index}",
                    event_kind="signal",
                    source="test",
                    occurred_at=NOW - timedelta(days=100),
                    raw_ip=f"192.0.2.{index + 1}",
                    raw_ip_expires_at=NOW - timedelta(seconds=1),
                    ip_full_hmac=f"full-{index}",
                    ip_prefix_hmac=f"prefix-{index}",
                    hmac_version=1,
                )
            )
        session.commit()
    finally:
        session.close()

    try:
        before_session = session_factory()
        try:
            assert retention_backlog_counts(before_session, now=NOW)["antiabuse_raw_ip"] == 5
        finally:
            before_session.close()

        report = drain_antiabuse_retention(session_factory, now=NOW, batch_limit=2)

        assert report["status"] == "drained"
        assert report["changed_batches"] == 3
        assert report["cleared"]["antiabuse_raw_ip"] == 5
        assert report["cleared"]["antiabuse_full_hmac"] == 5
        assert report["cleared"]["antiabuse_prefix_hmac"] == 5
        assert all(value == 0 for value in report["remaining"].values())
    finally:
        engine.dispose()


def test_drain_can_bound_one_run_and_report_remaining_backlog(tmp_path: Path) -> None:
    engine = create_engine(f"sqlite:///{(tmp_path / 'antiabuse-bounded-drain.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        for index in range(5):
            session.add(
                AntiAbuseEvent(
                    id=f"bounded-{index}",
                    event_kind="signal",
                    source="test",
                    occurred_at=NOW - timedelta(days=100),
                    raw_ip=f"198.51.100.{index + 1}",
                    raw_ip_expires_at=NOW - timedelta(seconds=1),
                )
            )
        session.commit()
    finally:
        session.close()

    try:
        report = drain_antiabuse_retention(
            session_factory,
            now=NOW,
            batch_limit=2,
            max_batches=2,
        )

        assert report["status"] == "backlog_remaining"
        assert report["changed_batches"] == 2
        assert report["cleared"]["antiabuse_raw_ip"] == 4
        assert report["remaining"]["antiabuse_raw_ip"] == 1
    finally:
        engine.dispose()


def test_hard_lock_requires_explicit_operator_identity(tmp_path: Path) -> None:
    engine, session = _session_for(tmp_path)
    try:
        case = AntiAbuseCase(
            id="case-1",
            account_id="account-1",
            reason_code="trial_farming",
            opened_at=NOW,
            updated_at=NOW,
        )
        session.add(case)
        session.commit()

        with pytest.raises(AntiAbusePolicyError, match="operator identity"):
            set_operator_hard_lock(
                session,
                case_id="case-1",
                locked=True,
                operator_tg_id=0,
                reason="manual review",
                now=NOW,
            )

        action = set_operator_hard_lock(
            session,
            case_id="case-1",
            locked=True,
            operator_tg_id=777,
            reason="manual review",
            now=NOW,
        )
        session.commit()

        assert case.hard_lock is True
        assert case.assigned_operator_tg_id == 777
        assert action.actor_kind == "operator"
        assert action.actor_tg_id == 777
        assert session.query(AntiAbuseAction).count() == 1
    finally:
        session.close()
        engine.dispose()
