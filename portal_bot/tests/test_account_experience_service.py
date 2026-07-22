from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

from account_experience_service import (  # noqa: E402
    build_experience_snapshot,
    reconcile_account_merge,
    record_first_connection_reported,
    set_onboarding_status,
)
from models import AccountExperienceState, Base, ConnectionEvidence  # noqa: E402


NOW = datetime(2026, 7, 22, 12, 0, 0)


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_snapshot_separates_client_report_from_observer_verification() -> None:
    session = _session()
    try:
        before = build_experience_snapshot(session, account_id="account-a", app_identity_known=True)
        assert before["onboarding"]["should_show"] is True
        assert before["first_connection"]["state"] == "none"
        assert before["next_step"] == "connect"

        record_first_connection_reported(session, account_id="account-a", reported_at=NOW)
        reported = build_experience_snapshot(session, account_id="account-a", app_identity_known=True)
        assert reported["first_connection"] == {
            "state": "reported",
            "reported_at": NOW.isoformat(),
            "verified_at": None,
        }

        verified_at = NOW + timedelta(minutes=2)
        session.add(
            ConnectionEvidence(
                id="evidence-a",
                account_id="account-a",
                device_id=None,
                node_id=1,
                evidence_kind="observer_connection",
                observed_at=verified_at,
                evidence_key="observer:test:account-a",
                created_at=verified_at,
            )
        )
        session.flush()
        verified = build_experience_snapshot(session, account_id="account-a", app_identity_known=True)
        assert verified["first_connection"]["state"] == "verified"
        assert verified["first_connection"]["reported_at"] == NOW.isoformat()
        assert verified["first_connection"]["verified_at"] == verified_at.isoformat()
        assert verified["onboarding"]["should_show"] is False
        assert verified["next_step"] == "complete"
    finally:
        session.close()


def test_account_merge_keeps_strongest_onboarding_and_earliest_connection() -> None:
    session = _session()
    try:
        set_onboarding_status(session, account_id="target", status="skipped", now=NOW)
        set_onboarding_status(
            session,
            account_id="source",
            status="completed",
            now=NOW + timedelta(minutes=4),
        )
        record_first_connection_reported(
            session,
            account_id="target",
            reported_at=NOW + timedelta(minutes=3),
        )
        record_first_connection_reported(
            session,
            account_id="source",
            reported_at=NOW + timedelta(minutes=1),
        )

        reconcile_account_merge(
            session,
            source_account_id="source",
            target_account_id="target",
            now=NOW + timedelta(minutes=10),
        )

        row = session.query(AccountExperienceState).filter_by(account_id="target").one()
        assert row.onboarding_status == "completed"
        assert row.onboarding_updated_at == NOW + timedelta(minutes=4)
        assert row.first_connection_reported_at == NOW + timedelta(minutes=1)
        assert session.query(AccountExperienceState).filter_by(account_id="source").first() is None
    finally:
        session.close()
