from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


os.environ.setdefault("WEBAPP_SESSION_SECRET", "pairing-test-secret-at-least-32-chars")

PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import device_pairing_service
from models import Account, AccountDevice, AuthSession, Base, DevicePairingCode, User


@pytest.fixture()
def pairing_session(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'pairing.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        yield session
        session.rollback()
    engine.dispose()


def _seed_owner(session, *, now: datetime) -> User:
    account = Account(
        id="00000000-0000-4000-8000-000000000501",
        status="active",
        created_source="test",
        created_at=now,
        updated_at=now,
    )
    user = User(
        tg_id=7501,
        account_id=account.id,
        uuid="00000000-0000-4000-8000-000000007501",
        sub_type="PAID",
        current_plan_code="month",
        expiry_at=now + timedelta(days=30),
        is_active=True,
        app_install_id="android-owner-0001",
    )
    device = AccountDevice(
        id="00000000-0000-4000-8000-000000000502",
        account_id=account.id,
        install_id="android-owner-0001",
        label="Owner phone",
        platform="android",
        state="active",
        first_seen_at=now,
        last_seen_at=now,
        created_at=now,
        updated_at=now,
    )
    session.add_all([account, user, device])
    session.flush()
    return user


def test_pairing_code_is_hmac_only_short_lived_and_claims_once(pairing_session) -> None:
    now = datetime(2026, 7, 23, 12, 0, 0)
    owner = _seed_owner(pairing_session, now=now)

    issued = device_pairing_service.issue_pairing_code(
        pairing_session,
        account_id=str(owner.account_id),
        issued_by_session_id=None,
        now=now,
    )

    assert issued.code.count("-") == 1
    assert issued.code.replace("-", "") not in issued.row.code_hmac
    assert issued.row.code_hint == issued.code[-4:]
    assert issued.row.expires_at == now + timedelta(minutes=10)

    claimed = device_pairing_service.claim_pairing_code(
        pairing_session,
        code=issued.code.lower(),
        install_id="android-tv-living-room-0001",
        device_name="Android TV",
        platform="android_tv",
        os_version="14",
        app_version="1.0.0-beta.4",
        locale="ru_RU",
        time_zone="Europe/Moscow",
        device_limit_resolver=lambda _user: 5,
        now=now + timedelta(minutes=1),
    )

    assert claimed.row.status == "claimed"
    assert claimed.session.account_id == owner.account_id
    assert claimed.session.access_token
    assert pairing_session.query(AuthSession).count() == 1
    assert pairing_session.query(AccountDevice).count() == 2
    assert pairing_session.query(DevicePairingCode).one().code_hmac != issued.code

    with pytest.raises(device_pairing_service.DevicePairingError) as repeat:
        device_pairing_service.claim_pairing_code(
            pairing_session,
            code=issued.code,
            install_id="android-tv-bedroom-0002",
            device_name="Second TV",
            platform="android_tv",
            os_version=None,
            app_version=None,
            locale=None,
            time_zone=None,
            device_limit_resolver=lambda _user: 5,
            now=now + timedelta(minutes=2),
        )
    assert repeat.value.code == "pairing_code_used"


def test_pairing_enforces_expiry_and_device_limit(pairing_session) -> None:
    now = datetime(2026, 7, 23, 12, 0, 0)
    owner = _seed_owner(pairing_session, now=now)
    issued = device_pairing_service.issue_pairing_code(
        pairing_session,
        account_id=str(owner.account_id),
        issued_by_session_id=None,
        now=now,
        ttl_seconds=120,
    )

    with pytest.raises(device_pairing_service.DevicePairingError) as limited:
        device_pairing_service.claim_pairing_code(
            pairing_session,
            code=issued.code,
            install_id="windows-second-device-0001",
            device_name="PC",
            platform="windows",
            os_version=None,
            app_version=None,
            locale=None,
            time_zone=None,
            device_limit_resolver=lambda _user: 1,
            now=now + timedelta(seconds=30),
        )
    assert limited.value.code == "device_limit_reached"

    with pytest.raises(device_pairing_service.DevicePairingError) as expired:
        device_pairing_service.claim_pairing_code(
            pairing_session,
            code=issued.code,
            install_id="windows-second-device-0001",
            device_name="PC",
            platform="windows",
            os_version=None,
            app_version=None,
            locale=None,
            time_zone=None,
            device_limit_resolver=lambda _user: 5,
            now=now + timedelta(minutes=3),
        )
    assert expired.value.code == "pairing_code_expired"
