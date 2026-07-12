from __future__ import annotations

import hashlib
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


import account_recovery_service as recovery_service  # noqa: E402
from account_recovery_service import (  # noqa: E402
    AccountRecoveryError,
    complete_access_reissue,
    exchange_recovery_code,
    rotate_recovery_code,
)
from auth_session_service import (  # noqa: E402
    issue_authenticated_device_session,
    issue_device_session,
    mark_session_fresh,
    rotate_device_session,
)
from email_auth_service import consume_login_otp, issue_login_otp  # noqa: E402
from models import (  # noqa: E402
    AccessKey,
    Account,
    AccountDevice,
    AntiAbuseEvent,
    AuthSession,
    Base,
    NodeProvisioningJob,
    RecoveryCode,
    User,
    WebEmailIdentity,
    WebEmailToken,
)
from web_auth_service import inspect_web_session_token  # noqa: E402


NOW = datetime(2026, 7, 12, 15, 0, 0)
ACCOUNT_ID = "11111111-1111-1111-1111-111111111111"


def _session_for(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'account-recovery.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _seed_account(session) -> tuple[User, Account, AccountDevice, WebEmailIdentity]:
    account = Account(
        id=ACCOUNT_ID,
        status="active",
        created_source="test",
        auth_epoch=2,
        created_at=NOW,
        updated_at=NOW,
    )
    device = AccountDevice(
        id="22222222-2222-2222-2222-222222222222",
        account_id=ACCOUNT_ID,
        install_id="install-original",
        label="Original phone",
        platform="android",
        state="active",
        credential_version=1,
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    user = User(
        tg_id=9_000_000_000_321,
        username="app_000321",
        uuid="33333333-3333-3333-3333-333333333333",
        email="APP_9000000000321",
        sub_type="PAID",
        current_plan_code="1_month",
        expiry_at=NOW + timedelta(days=25),
        account_id=ACCOUNT_ID,
        is_active=True,
        is_app_user=True,
        app_install_id=device.install_id,
        sub_token="old-subscription-token",
        created_at=NOW,
    )
    identity = WebEmailIdentity(
        email="owner@pokrov.test",
        email_norm="owner@pokrov.test",
        password_hash="compatibility-only",
        linked_tg_id=user.tg_id,
        is_verified=True,
        verified_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    session.add_all([account, device, user, identity])
    session.commit()
    return user, account, device, identity


def test_email_login_otp_is_six_digits_hashed_and_single_use(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    engine, session = _session_for(tmp_path)
    _user, _account, _device, identity = _seed_account(session)

    resolved, code = issue_login_otp(session, email="OWNER@pokrov.test", now=NOW)
    session.commit()

    assert resolved is not None and resolved.id == identity.id
    assert code is not None and len(code) == 6 and code.isdigit()
    stored = session.query(WebEmailToken).filter_by(token_kind="login_otp").one()
    assert stored.token_hash != code
    assert code not in stored.token_hash
    assert stored.expires_at == NOW + timedelta(minutes=5)

    consumed = consume_login_otp(
        session,
        email="owner@pokrov.test",
        code=code,
        now=NOW + timedelta(minutes=1),
    )
    session.commit()
    assert consumed.id == identity.id
    assert session.query(WebEmailToken).filter_by(id=stored.id).one().used_at == NOW + timedelta(minutes=1)

    with pytest.raises(AccountRecoveryError, match="email_otp_invalid"):
        consume_login_otp(
            session,
            email="owner@pokrov.test",
            code=code,
            now=NOW + timedelta(minutes=2),
        )

    session.close()
    engine.dispose()


def test_email_login_otp_fails_closed_without_backend_secret(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EMAIL_AUTH_TOKEN_SECRET", raising=False)
    monkeypatch.delenv("WEBAPP_SESSION_SECRET", raising=False)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    engine, session = _session_for(tmp_path)
    _seed_account(session)

    with pytest.raises(AccountRecoveryError, match="email_otp_not_configured"):
        issue_login_otp(session, email="owner@pokrov.test", now=NOW)

    assert session.query(WebEmailToken).filter_by(token_kind="login_otp").count() == 0
    session.close()
    engine.dispose()


def test_email_otp_can_freshen_existing_device_session(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device, _identity = _seed_account(session)
    issued = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()

    marked = mark_session_fresh(
        session,
        account_id=account.id,
        session_id=issued.session_id,
        now=NOW + timedelta(minutes=2),
    )
    session.commit()

    assert marked.fresh_auth_at == NOW + timedelta(minutes=2)

    session.close()
    engine.dispose()


def test_recovery_code_rotation_requires_fresh_auth_and_stores_only_hmac(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET", "recovery-code-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device, _identity = _seed_account(session)
    issued = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()

    with pytest.raises(AccountRecoveryError, match="fresh_auth_required"):
        rotate_recovery_code(
            session,
            account_id=account.id,
            actor_session_id=issued.session_id,
            now=NOW + timedelta(minutes=1),
        )

    mark_session_fresh(
        session,
        account_id=account.id,
        session_id=issued.session_id,
        now=NOW + timedelta(minutes=2),
    )
    rotated = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=issued.session_id,
        now=NOW + timedelta(minutes=2),
    )
    session.commit()

    assert rotated.code.startswith("PKR-")
    assert len(rotated.code.split("-")) == 4
    assert all(len(part) == 4 for part in rotated.code.split("-")[1:])
    stored = session.query(RecoveryCode).filter_by(id=rotated.code_id).one()
    assert stored.code_hmac != rotated.code
    assert rotated.code not in stored.code_hmac
    assert len(stored.code_hmac) == 64
    assert stored.code_hint.endswith(rotated.code[-4:])

    second = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=issued.session_id,
        now=NOW + timedelta(minutes=3),
    )
    session.commit()
    replaced = session.query(RecoveryCode).filter_by(id=rotated.code_id).one()
    assert replaced.status == "revoked"
    assert replaced.replaced_by_code_id == second.code_id

    session.close()
    engine.dispose()


def test_recovery_code_hmac_version_can_validate_previous_key(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "session-fallback-not-used")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET_V1", "recovery-v1-secret")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET_V2", "recovery-v2-secret")
    monkeypatch.setattr(recovery_service, "RECOVERY_CODE_HMAC_VERSION", 1)
    engine, session = _session_for(tmp_path)
    user, account, device, _identity = _seed_account(session)
    issued = issue_device_session(
        session,
        user=user,
        install_id=device.install_id,
        now=NOW,
        fresh_auth_at=NOW,
    )
    old_code = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=issued.session_id,
        now=NOW,
    )
    session.commit()

    monkeypatch.setattr(recovery_service, "RECOVERY_CODE_HMAC_VERSION", 2)
    exchange = exchange_recovery_code(
        session,
        code=old_code.code,
        install_id="install-after-hmac-rotation",
        device_name="Rotated key device",
        platform="windows",
        now=NOW + timedelta(minutes=1),
    )
    session.commit()

    assert exchange.session.account_id == account.id
    assert session.query(RecoveryCode).filter_by(id=old_code.code_id).one().status == "used"

    session.close()
    engine.dispose()


def test_recovery_exchange_registers_device_and_returns_limited_one_time_session(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET", "recovery-code-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device, _identity = _seed_account(session)
    original = issue_device_session(
        session,
        user=user,
        install_id=device.install_id,
        now=NOW,
        fresh_auth_at=NOW,
    )
    rotated = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=original.session_id,
        now=NOW,
    )
    session.commit()

    exchange = exchange_recovery_code(
        session,
        code=rotated.code,
        install_id="install-recovered-windows",
        device_name="Recovered PC",
        platform="windows",
        os_version="11",
        app_version="1.0.0-rc.1",
        locale="ru",
        time_zone="Europe/Moscow",
        now=NOW + timedelta(minutes=1),
    )
    session.commit()

    code_row = session.query(RecoveryCode).filter_by(id=rotated.code_id).one()
    session_row = session.query(AuthSession).filter_by(id=exchange.session.session_id).one()
    assert code_row.status == "used"
    assert code_row.used_at == NOW + timedelta(minutes=1)
    assert session_row.scope == "recovery"
    assert session_row.access_expires_at == NOW + timedelta(minutes=16)
    assert session_row.refresh_expires_at == NOW + timedelta(minutes=16)
    assert session_row.fresh_auth_at == NOW + timedelta(minutes=1)
    assert exchange.session.refresh_token not in session_row.refresh_token_hash
    recovered_device = session.query(AccountDevice).filter_by(install_id="install-recovered-windows").one()
    assert recovered_device.account_id == account.id
    assert recovered_device.state == "recovery"

    refreshed = rotate_device_session(
        session,
        refresh_token=exchange.session.refresh_token,
        now=NOW + timedelta(minutes=5),
    )
    session.commit()
    refreshed_row = session.query(AuthSession).filter_by(id=refreshed.session_id).one()
    assert refreshed_row.scope == "recovery"
    assert refreshed_row.access_expires_at == NOW + timedelta(minutes=16)
    assert refreshed_row.refresh_expires_at == NOW + timedelta(minutes=16)

    with pytest.raises(AccountRecoveryError, match="recovery_code_invalid"):
        exchange_recovery_code(
            session,
            code=rotated.code,
            install_id="install-replay",
            device_name="Replay",
            platform="android",
            now=NOW + timedelta(minutes=2),
        )

    session.close()
    engine.dispose()


def test_vpn_reissue_rotates_subscription_material_queues_keys_and_preserves_entitlement(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET", "recovery-code-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device, _identity = _seed_account(session)
    session.add(
        AccessKey(
            tg_id=user.tg_id,
            key_uuid="44444444-4444-4444-4444-444444444444",
            panel_email="recovery-key@pokrov.test",
            node_code="nl",
            pool_code="premium_pool",
            state="active",
            source="test",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    original = issue_device_session(
        session,
        user=user,
        install_id=device.install_id,
        now=NOW,
        fresh_auth_at=NOW,
    )
    code = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=original.session_id,
        now=NOW,
    )
    session.commit()
    exchange = exchange_recovery_code(
        session,
        code=code.code,
        install_id="install-new-phone",
        device_name="New phone",
        platform="android",
        now=NOW + timedelta(minutes=1),
    )
    session.commit()

    old_expiry = user.expiry_at
    lock_statements: list[str] = []

    def _capture_lock(orm_execute_state) -> None:
        statement = orm_execute_state.statement
        if getattr(statement, "_for_update_arg", None) is not None:
            lock_statements.append(str(statement))

    event.listen(session, "do_orm_execute", _capture_lock)

    result = complete_access_reissue(
        session,
        account_id=account.id,
        recovery_session_id=exchange.session.session_id,
        mode="vpn_credentials",
        device_limit=5,
        now=NOW + timedelta(minutes=2),
    )
    session.commit()

    session.refresh(user)
    assert user.sub_token != "old-subscription-token"
    assert user.expiry_at == old_expiry
    assert "users" in lock_statements[0]
    assert "accounts" in lock_statements[1]
    assert "account_devices" in lock_statements[2]
    key = session.query(AccessKey).one()
    assert key.state == "rotation_requested"
    job = session.query(NodeProvisioningJob).one()
    assert job.job_type == "rotate_access_key"
    assert result.provisioning_status == "pending"
    assert result.session.account_id == account.id
    assert session.query(AuthSession).filter_by(id=exchange.session.session_id).one().revoked_at is not None
    new_payload, reason = inspect_web_session_token(result.session.access_token)
    assert reason is None
    assert new_payload is not None and new_payload["scope"] == "client"
    audit = session.query(AntiAbuseEvent).filter_by(event_kind="access_reissue").one()
    assert audit.account_id == account.id
    assert "old-subscription-token" not in str(audit.metadata_json or "")
    assert hashlib.sha256(result.session.refresh_token.encode("utf-8")).hexdigest() == (
        session.query(AuthSession).filter_by(id=result.session.session_id).one().refresh_token_hash
    )

    with pytest.raises(AccountRecoveryError, match="recovery_session_invalid"):
        complete_access_reissue(
            session,
            account_id=account.id,
            recovery_session_id=exchange.session.session_id,
            mode="vpn_credentials",
            device_limit=5,
            now=NOW + timedelta(minutes=3),
        )

    session.close()
    engine.dispose()


def test_account_lockdown_revokes_other_devices_and_increments_epoch(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET", "recovery-code-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, original_device, _identity = _seed_account(session)
    original = issue_device_session(
        session,
        user=user,
        install_id=original_device.install_id,
        now=NOW,
        fresh_auth_at=NOW,
    )
    code = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=original.session_id,
        now=NOW,
    )
    session.commit()
    exchange = exchange_recovery_code(
        session,
        code=code.code,
        install_id="install-lockdown-device",
        device_name="Safe device",
        platform="windows",
        now=NOW + timedelta(minutes=1),
    )
    session.commit()

    result = complete_access_reissue(
        session,
        account_id=account.id,
        recovery_session_id=exchange.session.session_id,
        mode="account_lockdown",
        device_limit=1,
        now=NOW + timedelta(minutes=2),
    )
    session.commit()

    session.refresh(account)
    session.refresh(original_device)
    assert account.auth_epoch == 3
    assert original_device.state == "revoked"
    assert original_device.revoked_at == NOW + timedelta(minutes=2)
    safe_device = session.query(AccountDevice).filter_by(install_id="install-lockdown-device").one()
    assert safe_device.state == "active"
    assert result.revoked_devices == 1
    assert session.query(AuthSession).filter_by(id=result.session.session_id).one().revoked_at is None

    session.close()
    engine.dispose()


def test_vpn_reissue_cannot_leave_account_over_device_limit(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "account-recovery-test-secret")
    monkeypatch.setenv("RECOVERY_CODE_HMAC_SECRET", "recovery-code-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, original_device, _identity = _seed_account(session)
    user.sub_type = "FREE"
    user.current_plan_code = "free_monthly"
    original = issue_device_session(
        session,
        user=user,
        install_id=original_device.install_id,
        now=NOW,
        fresh_auth_at=NOW,
    )
    code = rotate_recovery_code(
        session,
        account_id=account.id,
        actor_session_id=original.session_id,
        now=NOW,
    )
    session.commit()
    exchange = exchange_recovery_code(
        session,
        code=code.code,
        install_id="install-over-limit-recovery",
        device_name="Replacement phone",
        platform="android",
        now=NOW + timedelta(minutes=1),
    )
    session.commit()

    assert session.query(AccountDevice).filter_by(install_id="install-over-limit-recovery").one().state == "recovery"
    assert (
        session.query(AccountDevice)
        .filter(
            AccountDevice.account_id == account.id,
            AccountDevice.state == "active",
            AccountDevice.revoked_at.is_(None),
        )
        .count()
        == 1
    )

    with pytest.raises(AccountRecoveryError, match="device_limit_reached"):
        complete_access_reissue(
            session,
            account_id=account.id,
            recovery_session_id=exchange.session.session_id,
            mode="vpn_credentials",
            device_limit=1,
            now=NOW + timedelta(minutes=2),
        )
    session.rollback()

    lockdown = complete_access_reissue(
        session,
        account_id=account.id,
        recovery_session_id=exchange.session.session_id,
        mode="account_lockdown",
        device_limit=1,
        now=NOW + timedelta(minutes=3),
    )
    session.commit()

    active_devices = (
        session.query(AccountDevice)
        .filter(
            AccountDevice.account_id == account.id,
            AccountDevice.state == "active",
            AccountDevice.revoked_at.is_(None),
        )
        .count()
    )
    assert active_devices == 1
    assert lockdown.revoked_devices == 1

    session.close()
    engine.dispose()
