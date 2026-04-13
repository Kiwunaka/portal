from __future__ import annotations

import asyncio
import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_api_and_service(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")
    monkeypatch.setenv("PUBLIC_CHANNEL", "pokrov_vpn")
    monkeypatch.setenv("BOT_USERNAME", "pokrov_vpnbot")
    monkeypatch.setenv("SUPPORT_BOT_USERNAME", "pokrov_supportbot")

    for name in [
        "api",
        "app_first_service",
        "config",
        "db",
        "migrations",
        "models",
        "web_auth_service",
        "control_panel",
        "nodes_repo",
        "tickets_repo",
        "events_service",
        "offers_service",
        "pay_attempts_service",
        "points_service",
        "free_cycle_service",
        "gift_cards_service",
        "payment_providers",
        "public_urls",
        "shared_surface_facts",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")
    service = importlib.import_module("app_first_service")
    return api, service


def test_upsert_app_trial_user_uses_canonical_trial_days(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    session = api.SessionLocal()
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)
    payload = SimpleNamespace(
        install_id="install-123",
        device_name="Surface Laptop",
        platform="windows",
        os_version="11",
        app_version="1.0.0",
        locale="ru",
        time_zone="Europe/Moscow",
    )

    try:
        user, created = service.upsert_app_trial_user(
            s=session,
            payload=payload,
            now=now,
            trial_days=5,
            request_client_ip="203.0.113.10",
        )
        session.commit()

        assert created is True
        assert user.is_app_user is True
        assert user.app_install_id == "install-123"
        assert user.app_device_name == "Surface Laptop"
        assert user.app_last_ip == "203.0.113.10"
        assert user.expiry_at == now + timedelta(days=5)

        updated_payload = SimpleNamespace(
            install_id="install-123",
            device_name="Surface Laptop 2",
            platform="windows",
            os_version="11",
            app_version="1.0.1",
            locale="ru",
            time_zone="Europe/Moscow",
        )
        updated_user, updated = service.upsert_app_trial_user(
            s=session,
            payload=updated_payload,
            now=now + timedelta(hours=1),
            trial_days=5,
            request_client_ip="203.0.113.11",
        )
        session.commit()

        assert updated is False
        assert updated_user.tg_id == user.tg_id
        assert updated_user.app_device_name == "Surface Laptop 2"
        assert updated_user.app_version == "1.0.1"
        assert updated_user.app_last_ip == "203.0.113.11"
        assert updated_user.expiry_at == now + timedelta(days=5)
    finally:
        session.close()


def test_build_start_trial_response_parts_preserves_public_shape(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    session = api.SessionLocal()
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)
    payload = SimpleNamespace(
        install_id="install-response",
        device_name="Pixel 10",
        platform="android",
        os_version="15",
        app_version="1.0.0",
        locale="ru",
        time_zone="Europe/Moscow",
    )

    try:
        user, _created = service.upsert_app_trial_user(
            s=session,
            payload=payload,
            now=now,
            trial_days=5,
            request_client_ip="203.0.113.20",
        )
        session.commit()
        session.refresh(user)

        session_token = api.create_web_session_token(tg_id=int(user.tg_id), username=str(user.username))
        parts = service.build_start_trial_response_parts(
            user=user,
            session_token=session_token,
            now=now,
            sync_ok=True,
            build_access_policy=api._build_access_policy,
            trial_days=5,
            channel_bonus_days=10,
        )

        assert parts["subscription_url"] == api.build_subscription_url(str(user.sub_token or ""))
        assert parts["session"]["token"] == session_token
        assert parts["session"]["session_token"] == session_token
        assert parts["session"]["account_id"] == str(user.tg_id)
        assert parts["client_policy"]["routing_mode_default"] == "all_except_ru"
        assert parts["client_policy"]["transport_profile"] == "grpc_443_primary"
        assert parts["client_policy"]["dns_policy"] == "ru_direct_split"
        assert parts["client_policy"]["package_catalog_version"]
        assert parts["client_policy"]["support_context"]["transport"] == "grpc_443_primary"
        assert parts["access"]["trial_days"] == 5
        assert parts["access"]["bonus_days"] == 10
        assert parts["access"]["subscription_url"] == parts["subscription_url"]
        assert parts["provisioning"]["status"] == "ready"
        assert parts["provisioning"]["sync_ok"] is True
    finally:
        session.close()
