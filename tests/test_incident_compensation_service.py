from __future__ import annotations

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

import incident_service
from models import Account, Base, EntitlementGrant, Event, ServiceIncident, User


def _seed_account(session, *, account_id: str, tg_id: int, now: datetime) -> User:
    account = Account(
        id=account_id,
        status="active",
        created_source="test",
        created_at=now - timedelta(days=60),
        updated_at=now,
    )
    user = User(
        tg_id=tg_id,
        account_id=account_id,
        uuid=f"00000000-0000-4000-8000-{tg_id:012d}",
        sub_type="PAID",
        current_plan_code="month",
        expiry_at=now + timedelta(days=10),
        is_active=True,
    )
    grant = EntitlementGrant(
        id=f"10000000-0000-4000-8000-{tg_id:012d}",
        account_id=account_id,
        legacy_tg_id=tg_id,
        idempotency_key=f"provider-payment:{account_id}",
        source="provider_payment",
        status="active",
        grant_kind="paid_access",
        plan_code="month",
        starts_at=now - timedelta(days=20),
        expires_at=now + timedelta(days=10),
        activated_at=now - timedelta(days=20),
        duration_days=30,
        provider="test",
        created_at=now - timedelta(days=20),
        updated_at=now,
    )
    session.add_all([account, user, grant])
    session.flush()
    return user


def _runtime_event(
    *,
    tg_id: int,
    created_at: datetime,
    node_code: str,
    connected: bool = True,
) -> Event:
    return Event(
        tg_id=tg_id,
        event_name="client_runtime_stats",
        source="app",
        meta_json=json.dumps(
            {"connected": connected, "selected_node_code": node_code},
            separators=(",", ":"),
        ),
        created_at=created_at,
    )


@pytest.fixture()
def incident_session(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'incident.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        yield session
        session.rollback()
    engine.dispose()


def test_incident_compensation_requires_connected_event_in_exact_window_and_node(
    incident_session,
) -> None:
    now = datetime(2026, 7, 23, 12, 0, 0)
    affected = _seed_account(
        incident_session,
        account_id="00000000-0000-4000-8000-000000000101",
        tg_id=7101,
        now=now,
    )
    other_node = _seed_account(
        incident_session,
        account_id="00000000-0000-4000-8000-000000000102",
        tg_id=7102,
        now=now,
    )
    complaint_only = _seed_account(
        incident_session,
        account_id="00000000-0000-4000-8000-000000000103",
        tg_id=7103,
        now=now,
    )
    incident_session.add_all(
        [
            _runtime_event(
                tg_id=affected.tg_id,
                created_at=now - timedelta(minutes=35),
                node_code="nl-ams-01",
            ),
            _runtime_event(
                tg_id=other_node.tg_id,
                created_at=now - timedelta(minutes=35),
                node_code="de-fra-01",
            ),
            Event(
                tg_id=complaint_only.tg_id,
                event_name="support_ticket_created",
                source="app",
                meta_json=json.dumps({"message": "VPN failed"}),
                created_at=now - timedelta(minutes=30),
            ),
        ]
    )
    incident = ServiceIncident(
        id="20000000-0000-4000-8000-000000000001",
        incident_key="inc-2026-07-23-nl",
        title="NL route outage",
        summary="Connections to the NL route were degraded.",
        severity="major",
        status="resolved",
        started_at=now - timedelta(hours=1),
        ended_at=now - timedelta(minutes=10),
        affected_node_codes_json='["nl-ams-01"]',
        compensation_days=3,
        confirmed_by=1,
        confirmed_at=now - timedelta(hours=1),
        resolved_by=1,
        resolved_at=now - timedelta(minutes=9),
        created_at=now - timedelta(hours=1),
        updated_at=now,
    )
    incident_session.add(incident)
    incident_session.flush()

    preview = incident_service.preview_incident_compensation(
        incident_session,
        incident=incident,
    )
    assert preview.impacted_account_ids == (affected.account_id,)

    first = incident_service.apply_incident_compensation(
        incident_session,
        incident_id=incident.id,
        now=now,
    )
    second = incident_service.apply_incident_compensation(
        incident_session,
        incident_id=incident.id,
        now=now + timedelta(minutes=1),
    )

    grants = (
        incident_session.query(EntitlementGrant)
        .filter(EntitlementGrant.source == "incident_compensation")
        .all()
    )
    assert first.impacted_accounts == 1
    assert first.granted_accounts == 1
    assert second.existing_grants == 1
    assert len(grants) == 1
    assert grants[0].account_id == affected.account_id
    assert grants[0].duration_days == 3
    assert "connected_runtime_event_in_incident_window" in grants[0].metadata_json
    assert incident.compensation_completed_at == now
    assert incident.impacted_accounts_count == 1
    assert incident.granted_accounts_count == 1


def test_pending_processor_is_idempotent_and_rejects_unresolved_incident(
    incident_session,
) -> None:
    now = datetime(2026, 7, 23, 12, 0, 0)
    user = _seed_account(
        incident_session,
        account_id="00000000-0000-4000-8000-000000000201",
        tg_id=7201,
        now=now,
    )
    incident_session.add(
        _runtime_event(
            tg_id=user.tg_id,
            created_at=now - timedelta(minutes=20),
            node_code="nl-ams-01",
        )
    )
    resolved = ServiceIncident(
        id="20000000-0000-4000-8000-000000000002",
        incident_key="inc-resolved",
        title="Resolved incident",
        summary="Confirmed and resolved.",
        severity="degraded",
        status="resolved",
        started_at=now - timedelta(hours=1),
        ended_at=now - timedelta(minutes=5),
        affected_node_codes_json="[]",
        compensation_days=1,
        confirmed_by=1,
        confirmed_at=now - timedelta(hours=1),
        resolved_by=1,
        resolved_at=now - timedelta(minutes=4),
        created_at=now - timedelta(hours=1),
        updated_at=now,
    )
    unresolved = ServiceIncident(
        id="20000000-0000-4000-8000-000000000003",
        incident_key="inc-open",
        title="Open incident",
        summary="Still being investigated.",
        severity="degraded",
        status="confirmed",
        started_at=now - timedelta(minutes=10),
        affected_node_codes_json="[]",
        compensation_days=1,
        confirmed_by=1,
        confirmed_at=now - timedelta(minutes=10),
        created_at=now - timedelta(minutes=10),
        updated_at=now,
    )
    incident_session.add_all([resolved, unresolved])
    incident_session.flush()

    first = incident_service.process_pending_incident_compensations(
        incident_session,
        now=now,
    )
    second = incident_service.process_pending_incident_compensations(
        incident_session,
        now=now + timedelta(minutes=1),
    )

    assert first == {
        "processed": 1,
        "impacted_accounts": 1,
        "granted_accounts": 1,
    }
    assert second == {
        "processed": 0,
        "impacted_accounts": 0,
        "granted_accounts": 0,
    }
    with pytest.raises(ValueError, match="incident_not_resolved"):
        incident_service.preview_incident_compensation(
            incident_session,
            incident=unresolved,
        )
