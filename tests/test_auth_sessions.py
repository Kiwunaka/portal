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


from auth_session_service import (  # noqa: E402
    AuthSessionError,
    issue_authenticated_device_session,
    issue_device_session,
    revoke_device,
    revoke_session,
    rotate_device_session,
    validate_access_session,
)
from models import (  # noqa: E402
    Account, AccountDevice, AuthSession, Awg2LabMaterial, Awg31LabMaterial,
    Base, Hy2LabMaterial, User,
)
from web_auth_service import inspect_web_session_token  # noqa: E402


NOW = datetime(2026, 7, 12, 12, 0, 0)


def _session_for(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'auth-sessions.db').as_posix()}")
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine)()


def _seed_account(session, *, install_id: str = "install-auth-session") -> tuple[User, Account, AccountDevice]:
    account = Account(
        id="11111111-1111-1111-1111-111111111111",
        status="active",
        created_source="test",
        auth_epoch=3,
        created_at=NOW,
        updated_at=NOW,
    )
    device = AccountDevice(
        id="22222222-2222-2222-2222-222222222222",
        account_id=account.id,
        install_id=install_id,
        label="Test device",
        platform="android",
        state="active",
        credential_version=2,
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    user = User(
        tg_id=9_000_000_000_123,
        username="app_9000000000123",
        uuid="33333333-3333-3333-3333-333333333333",
        email="app-9000000000123@telegram.local",
        sub_type="FREE",
        account_id=account.id,
        is_active=True,
        is_app_user=True,
        app_install_id=install_id,
        app_device_name="Test device",
        app_platform="android",
        created_at=NOW,
    )
    session.add_all([account, device, user])
    session.commit()
    return user, account, device


def test_issue_persists_only_refresh_hash_and_binds_access_claims(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device = _seed_account(session)

    issued = issue_device_session(
        session,
        user=user,
        install_id=device.install_id,
        now=NOW,
        access_ttl_seconds=900,
        refresh_ttl_seconds=30 * 86400,
    )
    session.commit()

    stored = session.query(AuthSession).filter_by(id=issued.session_id).one()
    payload, reason = inspect_web_session_token(issued.access_token)
    response_payload = issued.response_payload(now=NOW)

    assert reason is None
    assert payload is not None
    assert payload["id"] == int(user.tg_id)
    assert payload["account_id"] == account.id
    assert payload["session_id"] == stored.id
    assert payload["device_id"] == device.id
    assert payload["auth_epoch"] == 3
    assert payload["device_credential_version"] == 2
    assert stored.refresh_token_hash == hashlib.sha256(issued.refresh_token.encode("utf-8")).hexdigest()
    assert issued.refresh_token not in stored.refresh_token_hash
    assert stored.refresh_expires_at == NOW + timedelta(days=30)
    assert response_payload["account_id"] == str(user.tg_id)
    assert response_payload["canonical_account_id"] == account.id

    validated = validate_access_session(session, payload=payload, now=NOW + timedelta(minutes=1))
    assert validated["session_id"] == stored.id

    session.close()
    engine.dispose()


def test_second_bootstrap_for_same_device_requires_recovery(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, _account, device = _seed_account(session)
    issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()

    with pytest.raises(AuthSessionError) as exc_info:
        issue_device_session(session, user=user, install_id=device.install_id, now=NOW + timedelta(seconds=1))

    assert exc_info.value.code == "device_recovery_required"
    assert session.query(AuthSession).count() == 1

    session.close()
    engine.dispose()


def test_refresh_rotates_once_and_reuse_revokes_whole_family(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, _account, device = _seed_account(session)
    first = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()

    second = rotate_device_session(session, refresh_token=first.refresh_token, now=NOW + timedelta(minutes=5))
    session.commit()

    original = session.query(AuthSession).filter_by(id=first.session_id).one()
    replacement = session.query(AuthSession).filter_by(id=second.session_id).one()
    assert original.replaced_by_session_id == replacement.id
    assert original.revoked_at is None
    assert replacement.refresh_family_id == original.refresh_family_id
    assert second.refresh_token != first.refresh_token

    with pytest.raises(AuthSessionError) as exc_info:
        rotate_device_session(session, refresh_token=first.refresh_token, now=NOW + timedelta(minutes=6))
    assert exc_info.value.code == "refresh_reuse_detected"
    assert exc_info.value.security_state_changed is True
    session.commit()

    family = session.query(AuthSession).filter_by(refresh_family_id=original.refresh_family_id).all()
    assert len(family) == 2
    assert all(row.revoked_at == NOW + timedelta(minutes=6) for row in family)
    assert all(row.revoke_reason == "refresh_reuse_detected" for row in family)
    assert session.query(AuthSession).filter_by(id=first.session_id).one().reuse_detected_at == NOW + timedelta(minutes=6)

    with pytest.raises(AuthSessionError) as replay_exc:
        rotate_device_session(session, refresh_token=first.refresh_token, now=NOW + timedelta(minutes=8))
    assert replay_exc.value.code == "refresh_reuse_detected"
    session.commit()
    preserved = session.query(AuthSession).filter_by(id=first.session_id).one()
    assert preserved.reuse_detected_at == NOW + timedelta(minutes=6)
    assert preserved.revoked_at == NOW + timedelta(minutes=6)

    second_payload, reason = inspect_web_session_token(second.access_token)
    assert reason is None
    with pytest.raises(AuthSessionError) as access_exc:
        validate_access_session(session, payload=second_payload or {}, now=NOW + timedelta(minutes=7))
    assert access_exc.value.code == "session_revoked"

    session.close()
    engine.dispose()


def test_refresh_uses_account_device_session_lock_order(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, _account, device = _seed_account(session)
    issued = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()
    lock_statements: list[str] = []

    def _capture_lock(orm_execute_state) -> None:
        statement = orm_execute_state.statement
        if getattr(statement, "_for_update_arg", None) is not None:
            lock_statements.append(str(statement))

    event.listen(session, "do_orm_execute", _capture_lock)
    rotate_device_session(session, refresh_token=issued.refresh_token, now=NOW + timedelta(minutes=1))

    assert len(lock_statements) >= 3
    assert "accounts" in lock_statements[0]
    assert "account_devices" in lock_statements[1]
    assert "auth_sessions" in lock_statements[2]

    session.rollback()
    session.close()
    engine.dispose()


def test_device_revoke_requires_fresh_auth_and_invalidates_all_device_sessions(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device = _seed_account(session)
    issued = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()

    with pytest.raises(AuthSessionError) as exc_info:
        revoke_device(
            session,
            account_id=account.id,
            device_id=device.id,
            actor_session_id=issued.session_id,
            now=NOW + timedelta(minutes=1),
        )
    assert exc_info.value.code == "fresh_auth_required"

    actor = session.query(AuthSession).filter_by(id=issued.session_id).one()
    actor.fresh_auth_at = NOW + timedelta(minutes=1)
    session.commit()

    revoked = revoke_device(
        session,
        account_id=account.id,
        device_id=device.id,
        actor_session_id=issued.session_id,
        now=NOW + timedelta(minutes=2),
    )
    session.commit()

    assert revoked.state == "revoked"
    assert revoked.credential_version == 3
    assert revoked.revoked_at == NOW + timedelta(minutes=2)
    assert session.query(AuthSession).filter_by(id=issued.session_id).one().revoke_reason == "device_revoked"

    payload, reason = inspect_web_session_token(issued.access_token)
    assert reason is None
    with pytest.raises(AuthSessionError) as access_exc:
        validate_access_session(session, payload=payload or {}, now=NOW + timedelta(minutes=3))
    assert access_exc.value.code == "session_revoked"

    session.close()
    engine.dispose()


@pytest.mark.parametrize("material_type", [Awg2LabMaterial, Awg31LabMaterial, Hy2LabMaterial])
def test_device_revoke_keeps_old_lab_material_revoked_after_fresh_login(
    monkeypatch, tmp_path: Path, material_type,
) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device = _seed_account(session)
    issued = issue_device_session(
        session, user=user, install_id=device.install_id, now=NOW,
        fresh_auth_at=NOW,
    )
    fields = dict(
        tg_id=user.tg_id, install_id=device.install_id,
        contract_id="fixture-contract", contract_sha256="a" * 64,
        generation="fixture-v1", endpoint_revision="fixture-rev1",
        server_record_id="fixture-server", node_code="fixture-node",
        endpoint_ciphertext="retained-encrypted-fixture", material_hash="b" * 64,
        provisioned_at=NOW, updated_at=NOW,
    )
    target = material_type(**fields, is_active=True, state="ready")
    history = material_type(**fields, is_active=False, state="rotated", revoked_at=NOW)
    other_device = material_type(
        **{**fields, "install_id": "other-install"}, is_active=True, state="ready",
    )
    other_account = material_type(
        **{**fields, "tg_id": user.tg_id + 999}, is_active=True, state="ready",
    )
    session.add_all([target, history, other_device, other_account])
    session.commit()

    revoke_at = NOW + timedelta(minutes=1)
    revoke_device(
        session, account_id=account.id, device_id=device.id,
        actor_session_id=issued.session_id, now=revoke_at,
    )
    session.flush()
    session.refresh(target)
    assert not target.is_active and target.state == "revoked"
    session.rollback()
    session.refresh(target)
    session.refresh(device)
    assert target.is_active and device.state == "active"

    revoke_device(
        session, account_id=account.id, device_id=device.id,
        actor_session_id=issued.session_id, now=revoke_at,
    )
    session.commit()
    fresh = issue_authenticated_device_session(
        session, account_id=account.id, install_id=device.install_id,
        device_name="Reauthenticated device", platform="android",
        now=NOW + timedelta(minutes=2),
    )
    session.commit()
    assert fresh.device_id == device.id and device.state == "active"
    session.refresh(target)
    assert not target.is_active and target.state == "revoked"
    assert target.revoked_at == revoke_at
    assert target.endpoint_ciphertext == fields["endpoint_ciphertext"]
    assert target.material_hash == fields["material_hash"]
    assert history.state == "rotated" and history.revoked_at == NOW
    assert other_device.is_active and other_account.is_active
    assert session.query(material_type).count() == 4
    session.close()
    engine.dispose()


def test_access_rejects_account_epoch_and_device_credential_drift(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device = _seed_account(session)
    issued = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()
    payload, reason = inspect_web_session_token(issued.access_token)
    assert reason is None

    account.auth_epoch += 1
    session.commit()
    with pytest.raises(AuthSessionError) as epoch_exc:
        validate_access_session(session, payload=payload or {}, now=NOW + timedelta(minutes=1))
    assert epoch_exc.value.code == "session_epoch_changed"

    account.auth_epoch -= 1
    device.credential_version += 1
    session.commit()
    with pytest.raises(AuthSessionError) as device_exc:
        validate_access_session(session, payload=payload or {}, now=NOW + timedelta(minutes=1))
    assert device_exc.value.code == "device_credential_changed"

    session.close()
    engine.dispose()


def test_logout_revokes_only_current_session(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    user, account, device = _seed_account(session)
    issued = issue_device_session(session, user=user, install_id=device.install_id, now=NOW)
    session.commit()
    payload, reason = inspect_web_session_token(issued.access_token)
    assert reason is None

    revoked = revoke_session(
        session,
        account_id=account.id,
        session_id=issued.session_id,
        now=NOW + timedelta(minutes=1),
    )
    session.commit()

    assert revoked.revoke_reason == "user_logout"
    with pytest.raises(AuthSessionError) as exc_info:
        validate_access_session(session, payload=payload or {}, now=NOW + timedelta(minutes=2))
    assert exc_info.value.code == "session_revoked"

    session.close()
    engine.dispose()


def test_device_revoke_reconciles_orphan_session_without_rewriting_first_revoke(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "auth-session-test-secret")
    engine, session = _session_for(tmp_path)
    target_user, account, target_device = _seed_account(session)
    target_session = issue_device_session(
        session,
        user=target_user,
        install_id=target_device.install_id,
        now=NOW,
    )

    actor_device = AccountDevice(
        id="44444444-4444-4444-4444-444444444444",
        account_id=account.id,
        install_id="install-revoke-actor",
        label="Recovery device",
        platform="windows",
        state="active",
        credential_version=1,
        first_seen_at=NOW,
        last_seen_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    actor_user = User(
        tg_id=9_000_000_000_124,
        username="app_9000000000124",
        uuid="55555555-5555-5555-5555-555555555555",
        email="app-9000000000124@telegram.local",
        sub_type="FREE",
        account_id=account.id,
        is_active=True,
        is_app_user=True,
        app_install_id=actor_device.install_id,
        app_device_name="Recovery device",
        app_platform="windows",
        created_at=NOW,
    )
    session.add_all([actor_device, actor_user])
    session.flush()
    actor_session = issue_device_session(
        session,
        user=actor_user,
        install_id=actor_device.install_id,
        now=NOW,
        fresh_auth_at=NOW,
    )
    session.commit()

    first_revoke_at = NOW + timedelta(minutes=1)
    target_device.state = "revoked"
    target_device.revoked_at = first_revoke_at
    target_device.revoke_reason = "operator_revoke"
    target_device.credential_version = 3
    session.commit()

    reconciled = revoke_device(
        session,
        account_id=account.id,
        device_id=target_device.id,
        actor_session_id=actor_session.session_id,
        now=NOW + timedelta(minutes=2),
    )
    session.commit()

    orphan = session.query(AuthSession).filter_by(id=target_session.session_id).one()
    assert orphan.revoked_at == NOW + timedelta(minutes=2)
    assert orphan.revoke_reason == "device_revoked"
    assert reconciled.revoked_at == first_revoke_at
    assert reconciled.revoke_reason == "operator_revoke"
    assert reconciled.credential_version == 3

    session.close()
    engine.dispose()
