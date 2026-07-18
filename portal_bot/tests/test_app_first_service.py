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


def _rollout_client_policy(
    transport_profile: str,
    *,
    ip_version_preference: str = "ipv4_only",
) -> dict[str, object]:
    transport_kind = "reality"
    engine_hint = "singbox"
    if transport_profile == "grpc_443_primary":
        transport_kind = "grpc"
    elif transport_profile == "operator_lab":
        transport_kind = "xhttp"
        engine_hint = "xray"
    return {
        "routing_mode_default": "all_except_ru",
        "transport_profile": transport_profile,
        "transport_kind": transport_kind,
        "engine_hint": engine_hint,
        "profile_revision": f"2026-04-13:{transport_profile}",
        "dns_policy": "ru_direct_split",
        "package_catalog_version": "2026-04-13",
        "ruleset_version": "2026-04-13",
        "support_context": {
            "transport": transport_profile,
            "routing_mode": "all_except_ru",
            "ip_version_preference": ip_version_preference,
        },
        "support_recovery_order": ["app", "web", "telegram"],
    }


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
        assert user.expiry_at == now + timedelta(days=7)
        assert user.account_id

        from models import AccountDevice, EntitlementGrant

        device = session.query(AccountDevice).filter_by(install_id="install-123").one()
        assert device.account_id == user.account_id
        assert device.label == "Surface Laptop"
        grants = session.query(EntitlementGrant).filter_by(account_id=user.account_id).all()
        assert {grant.source for grant in grants} == {"legacy_snapshot", "premium_trial"}

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
        assert updated_user.expiry_at == now + timedelta(days=7)
        session.refresh(device)
        assert device.label == "Surface Laptop 2"
        assert session.query(EntitlementGrant).filter_by(account_id=user.account_id).count() == 2
    finally:
        session.close()


def test_upsert_app_trial_user_defers_create_and_update_flush_until_projection_locks(
    monkeypatch,
    tmp_path,
):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    import account_foundation_service as account_foundation_module
    import app_first_service as service
    from models import Base

    engine = create_engine(f"sqlite:///{(tmp_path / 'app-first-lock-order.db').as_posix()}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    events: list[tuple[str, str] | tuple[str]] = []

    def _capture_flush(*_args) -> None:
        events.append(("flush",))

    def _capture_lock(_session, lock_key: str, *, shared: bool = False) -> None:
        events.append(("lock", str(lock_key)))

    event.listen(session, "before_flush", _capture_flush)
    monkeypatch.setattr(
        account_foundation_module,
        "_acquire_postgres_advisory_lock",
        _capture_lock,
    )
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)
    payload = SimpleNamespace(
        install_id="install-lock-order",
        device_name="Lock order device",
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
        )
        assert created is True
        assert events[:2] == [
            ("lock", f"pokrov_account_foundation_user:{int(user.tg_id)}"),
            ("lock", "pokrov_account_foundation_backfill"),
        ]
        assert ("flush",) in events
        session.commit()

        events.clear()
        updated_payload = SimpleNamespace(**{**payload.__dict__, "device_name": "Updated lock order device"})
        updated_user, created = service.upsert_app_trial_user(
            s=session,
            payload=updated_payload,
            now=now + timedelta(minutes=1),
            trial_days=5,
        )
        assert created is False
        assert events[:2] == [
            ("lock", f"pokrov_account_foundation_user:{int(updated_user.tg_id)}"),
            ("lock", "pokrov_account_foundation_backfill"),
        ]
        assert ("flush",) in events
    finally:
        session.rollback()
        session.close()
        engine.dispose()


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

        client_policy = _rollout_client_policy("legacy_reality_fallback")
        session_token = api.create_web_session_token(tg_id=int(user.tg_id), username=str(user.username))
        parts = service.build_start_trial_response_parts(
            user=user,
            session_token=session_token,
            now=now,
            sync_ok=True,
            build_access_policy=api._build_access_policy,
            trial_days=5,
            channel_bonus_days=10,
            client_policy=client_policy,
        )

        assert parts["subscription_url"] == api.build_subscription_url(str(user.sub_token or ""))
        assert parts["session"]["token"] == session_token
        assert parts["session"]["session_token"] == session_token
        assert parts["session"]["account_id"] == str(user.tg_id)
        assert parts["client_policy"]["routing_mode_default"] == "all_except_ru"
        assert parts["client_policy"]["transport_profile"] == "legacy_reality_fallback"
        assert parts["client_policy"]["transport_kind"] == "reality"
        assert parts["client_policy"]["engine_hint"] == "singbox"
        assert parts["client_policy"]["profile_revision"] == "2026-04-13:legacy_reality_fallback"
        assert parts["client_policy"]["dns_policy"] == "ru_direct_split"
        assert parts["client_policy"]["package_catalog_version"]
        assert parts["client_policy"]["support_context"]["transport"] == "legacy_reality_fallback"
        assert parts["access"]["trial_days"] == 5
        assert parts["access"]["bonus_days"] == 10
        assert parts["access"]["subscription_url"] == parts["subscription_url"]
        assert parts["provisioning"]["status"] == "ready"
        assert parts["provisioning"]["sync_ok"] is True
    finally:
        session.close()


def test_build_client_policy_respects_rollout_config_carrier_and_cohort_overrides(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    session = api.SessionLocal()

    try:
        rollout_config = {
            "version": "2026-04-13",
            "defaults": {
                "routing_mode_default": "all_except_ru",
                "transport_profile": "legacy_reality_fallback",
                "dns_policy": "ru_direct_split",
                "ip_version_preference": "ipv4_only",
            },
            "carrier_overrides": {
                "carrier-x": {
                    "transport_profile": "grpc_443_primary",
                    "dns_policy": "ru_direct_split",
                    "routing_mode_default": "all_except_ru",
                    "ip_version_preference": "ipv6_preferred",
                }
            },
            "cohort_overrides": {
                "ru-risk-canary": {
                    "install_ids": ["install-response-grpc"],
                    "transport_profile": "grpc_443_primary",
                },
                "operator-lab": {
                    "install_ids": ["install-operator"],
                    "transport_profile": "operator_lab",
                }
            },
            "operator_lab": {
                "enabled": True,
                "allowlist_install_ids": ["install-operator"],
                "allowlist_tg_ids": [],
                "allowlist_node_codes": [],
                "expires_at": None,
            },
            "package_catalog_feed": {"version": "2026-04-13"},
            "routing_rules_feed": {"version": "2026-04-13"},
            "support_recovery_order": ["app", "web", "telegram"],
        }

        default_policy = service.build_client_policy(
            session=session,
            install_id="install-default",
            rollout_config=rollout_config,
        )
        carrier_policy = service.build_client_policy(
            session=session,
            install_id="install-default",
            carrier="carrier-x",
            rollout_config=rollout_config,
        )
        cohort_policy = service.build_client_policy(
            session=session,
            install_id="install-response-grpc",
            rollout_config=rollout_config,
        )
        operator_policy = service.build_client_policy(
            session=session,
            install_id="install-operator",
            rollout_config=rollout_config,
        )

        assert default_policy["transport_profile"] == "legacy_reality_fallback"
        assert default_policy["transport_kind"] == "reality"
        assert default_policy["engine_hint"] == "singbox"
        assert default_policy["profile_revision"] == "2026-04-13:legacy_reality_fallback"
        assert default_policy["support_context"]["ip_version_preference"] == "ipv4_only"
        assert carrier_policy["transport_profile"] == "grpc_443_primary"
        assert carrier_policy["transport_kind"] == "grpc"
        assert carrier_policy["engine_hint"] == "singbox"
        assert carrier_policy["profile_revision"] == "2026-04-13:grpc_443_primary"
        assert carrier_policy["support_context"]["ip_version_preference"] == "ipv6_preferred"
        assert cohort_policy["transport_profile"] == "grpc_443_primary"
        assert cohort_policy["transport_kind"] == "grpc"
        assert cohort_policy["engine_hint"] == "singbox"
        assert cohort_policy["profile_revision"] == "2026-04-13:grpc_443_primary"
        assert cohort_policy["support_context"]["transport"] == "grpc_443_primary"
        assert operator_policy["transport_profile"] == "operator_lab"
        assert operator_policy["transport_kind"] == "xhttp"
        assert operator_policy["engine_hint"] == "xray"
        assert operator_policy["profile_revision"] == "2026-04-13:operator_lab"
    finally:
        session.close()


def test_build_client_policy_includes_persisted_route_policy(monkeypatch, tmp_path):
    api, service = _load_api_and_service(monkeypatch, tmp_path)
    session = api.SessionLocal()
    now = datetime(2026, 4, 13, tzinfo=timezone.utc).replace(tzinfo=None)
    payload = SimpleNamespace(
        install_id="install-route-policy",
        device_name="Windows PC",
        platform="windows",
        os_version="11",
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
            request_client_ip="203.0.113.44",
        )
        user.route_mode = "selected_apps"
        user.route_selected_apps_json = '["chrome.exe","telegram.exe"]'
        user.route_requires_elevated_privileges = True
        session.commit()
        session.refresh(user)

        policy = service.build_client_policy(
            session=session,
            user=user,
            install_id=str(user.app_install_id),
        )

        assert policy["route_mode"] == "selected_apps"
        assert policy["selected_apps"] == ["chrome.exe", "telegram.exe"]
        assert policy["requires_elevated_privileges"] is True
        assert policy["route_policy"]["mode"] == "selected_apps"
        assert policy["route_policy"]["selected_apps"] == ["chrome.exe", "telegram.exe"]
    finally:
        session.close()
