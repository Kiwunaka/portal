from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))

import program_application_service
from models import Account, Base, EntitlementGrant, ProgramApplication, User


@pytest.fixture()
def program_session(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'programs.db').as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as session:
        yield session
        session.rollback()
    engine.dispose()


def _seed_user(session, *, now: datetime) -> User:
    account = Account(
        id="00000000-0000-4000-8000-000000000601",
        status="active",
        created_source="test",
        created_at=now,
        updated_at=now,
    )
    user = User(
        tg_id=7601,
        account_id=account.id,
        uuid="00000000-0000-4000-8000-000000007601",
        sub_type="PAID",
        current_plan_code="month",
        expiry_at=now + timedelta(days=10),
        is_active=True,
    )
    grant = EntitlementGrant(
        id="00000000-0000-4000-8000-000000000602",
        account_id=account.id,
        legacy_tg_id=user.tg_id,
        idempotency_key="provider-payment:program-test",
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


def test_research_reward_requires_operator_review_and_is_idempotent(program_session) -> None:
    now = datetime(2026, 7, 23, 12, 0, 0)
    user = _seed_user(program_session, now=now)
    application = program_application_service.submit_application(
        program_session,
        user=user,
        kind="research",
        source_name=None,
        seats=None,
        summary="Повторяемый сбой после смены сети, приложены точные шаги без ключей.",
        contact="@tester",
        now=now,
    )

    assert application.status == "submitted"
    assert program_session.query(EntitlementGrant).filter(EntitlementGrant.source == "research_reward").count() == 0

    rewarded = program_application_service.review_application(
        program_session,
        application_id=application.id,
        status="approved",
        operator_note="Воспроизведено на Android 14.",
        reward_days=3,
        reviewed_by=1,
        now=now + timedelta(hours=1),
    )
    repeated = program_application_service.review_application(
        program_session,
        application_id=application.id,
        status="approved",
        operator_note="Повтор запроса после потери ответа.",
        reward_days=3,
        reviewed_by=1,
        now=now + timedelta(hours=2),
    )

    grants = program_session.query(EntitlementGrant).filter(EntitlementGrant.source == "research_reward").all()
    assert rewarded.status == "rewarded"
    assert repeated.reward_grant_id == rewarded.reward_grant_id
    assert len(grants) == 1
    assert grants[0].duration_days == 3


def test_program_validation_and_pending_deduplication(program_session) -> None:
    now = datetime(2026, 7, 23, 12, 0, 0)
    user = _seed_user(program_session, now=now)

    with pytest.raises(program_application_service.ProgramApplicationError) as missing_competitor:
        program_application_service.submit_application(
            program_session,
            user=user,
            kind="competitor_switch",
            source_name="",
            seats=None,
            summary="Хочу перейти и проверить подключение на своих устройствах.",
            contact=None,
            now=now,
        )
    assert missing_competitor.value.code == "competitor_required"

    team = program_application_service.submit_application(
        program_session,
        user=user,
        kind="team_pack",
        source_name=None,
        seats=8,
        summary="Нужен единый набор для небольшой команды из восьми устройств.",
        contact="team@example.test",
        now=now,
    )
    assert team.seats == 8

    with pytest.raises(program_application_service.ProgramApplicationError) as duplicate:
        program_application_service.submit_application(
            program_session,
            user=user,
            kind="team_pack",
            source_name=None,
            seats=10,
            summary="Повторная заявка, пока первая ещё находится на проверке.",
            contact="team@example.test",
            now=now + timedelta(minutes=1),
        )
    assert duplicate.value.code == "program_application_pending"
    assert program_session.query(ProgramApplication).count() == 1
