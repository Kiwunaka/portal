from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1]
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


def _load_api_and_devices(monkeypatch, tmp_path: Path):
    db_path = tmp_path / "portal-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("WEBAPP_SESSION_SECRET", "portal-test-secret")
    monkeypatch.setenv("PUBLIC_API_BASE_URL", "https://api.pokrov.test")
    monkeypatch.setenv("PUBLIC_WEB_DOMAIN", "pokrov.test")

    for name in [
        "api",
        "config",
        "db",
        "device_service",
        "migrations",
        "models",
        "public_urls",
    ]:
        sys.modules.pop(name, None)

    api = importlib.import_module("api")
    devices = importlib.import_module("device_service")
    return api, devices


def _user(api, tg_id: int, *, sub_type: str = "FREE", current_plan_code: str = "free_monthly"):
    now = datetime(2026, 4, 24, tzinfo=timezone.utc).replace(tzinfo=None)
    return api.User(
        tg_id=tg_id,
        username=f"user_{tg_id}",
        uuid=f"uuid-{tg_id}",
        email=f"user_{tg_id}@example.test",
        sub_type=sub_type,
        current_plan_code=current_plan_code,
        created_at=now,
        expiry_at=now + timedelta(days=30),
        is_active=True,
        sub_token=f"sub-token-{tg_id}",
        is_app_user=True,
    )


def _payload(
    install_id: str,
    *,
    device_name: str = "Pixel 10",
    platform: str = "android",
    os_version: str = "15",
    app_version: str = "1.0.0",
    route_mode: str | None = None,
    selected_apps: list[str] | None = None,
):
    return SimpleNamespace(
        install_id=install_id,
        device_name=device_name,
        platform=platform,
        model="Retail model",
        os_version=os_version,
        app_version=app_version,
        route_mode=route_mode,
        selected_apps=selected_apps,
        requires_elevated_privileges=None,
    )


def test_device_service_tracks_multiple_devices_and_safe_current_marker(monkeypatch, tmp_path):
    api, devices = _load_api_and_devices(monkeypatch, tmp_path)
    s = api.SessionLocal()
    now = datetime(2026, 4, 24, 12, 0, 0)
    try:
        user = _user(api, 910001, sub_type="PAID", current_plan_code="monthly")
        s.add(user)
        s.commit()

        devices.upsert_current_device(
            s,
            user=user,
            payload=_payload("install-phone", device_name="Pixel 10", platform="android"),
            now=now,
            request_client_ip="198.51.100.10",
        )
        devices.upsert_current_device(
            s,
            user=user,
            payload=_payload("install-laptop", device_name="Surface Laptop", platform="windows"),
            now=now + timedelta(minutes=5),
            request_client_ip="198.51.100.11",
        )
        s.commit()

        rows = devices.list_user_devices(s, user=user, current_install_id="install-laptop")

        assert [row["id"] for row in rows] == ["install-laptop", "install-phone"]
        current = rows[0]
        assert current["is_current"] is True
        assert current["platform"] == "windows"
        assert current["name"] == "Surface Laptop"
        assert current["display_name"] == "Surface Laptop"
        assert current["route_mode"] == "all_traffic"
        assert current["selected_apps"] == []
        assert current["revoked"] is False
        assert "tg_id" not in current
        assert "db_id" not in current
        assert "last_ip" not in current
        assert "sub_token" not in current
    finally:
        s.close()


def test_device_service_rename_and_revoke_are_account_scoped(monkeypatch, tmp_path):
    api, devices = _load_api_and_devices(monkeypatch, tmp_path)
    s = api.SessionLocal()
    now = datetime(2026, 4, 24, 12, 0, 0)
    try:
        user = _user(api, 910002, sub_type="PAID", current_plan_code="monthly")
        other = _user(api, 910003, sub_type="PAID", current_plan_code="monthly")
        s.add_all([user, other])
        s.commit()

        devices.upsert_current_device(
            s,
            user=user,
            payload=_payload("install-phone", device_name="Pixel 10"),
            now=now,
            request_client_ip="198.51.100.20",
        )
        devices.upsert_current_device(
            s,
            user=other,
            payload=_payload("install-other", device_name="Other phone"),
            now=now,
            request_client_ip="198.51.100.21",
        )
        s.commit()

        renamed = devices.rename_device(
            s,
            user=user,
            install_id="install-phone",
            display_name="Travel phone",
            now=now + timedelta(minutes=1),
        )
        assert renamed.display_name == "Travel phone"
        assert renamed.device_name == "Pixel 10"

        revoked = devices.revoke_device(
            s,
            user=user,
            install_id="install-phone",
            now=now + timedelta(minutes=2),
        )
        assert revoked.revoked_at == now + timedelta(minutes=2)
        s.commit()

        assert devices.list_user_devices(s, user=user) == []
        revoked_rows = devices.list_user_devices(s, user=user, include_revoked=True)
        assert revoked_rows[0]["name"] == "Travel phone"
        assert revoked_rows[0]["revoked"] is True

        assert devices.rename_device(
            s,
            user=user,
            install_id="install-other",
            display_name="Should not cross accounts",
            now=now,
        ) is None
    finally:
        s.close()


def test_device_service_reports_limit_truth_from_plan_and_existing_devices(monkeypatch, tmp_path):
    api, devices = _load_api_and_devices(monkeypatch, tmp_path)
    s = api.SessionLocal()
    now = datetime(2026, 4, 24, 12, 0, 0)
    try:
        paid_plan = api.PlanCatalog(
            code="family",
            label="Family",
            amount_rub=990,
            amount_stars=0,
            days=30,
            device_limit=3,
            node_policy="paid_pool",
            is_active=True,
            sort_order=1,
            created_at=now,
            updated_at=now,
        )
        free_user = _user(api, 910004, sub_type="FREE", current_plan_code="free_monthly")
        paid_user = _user(api, 910005, sub_type="PAID", current_plan_code="family")
        s.add_all([paid_plan, free_user, paid_user])
        s.commit()

        devices.upsert_current_device(
            s,
            user=free_user,
            payload=_payload("free-one"),
            now=now,
            request_client_ip="203.0.113.1",
        )
        devices.upsert_current_device(
            s,
            user=paid_user,
            payload=_payload("paid-one"),
            now=now,
            request_client_ip="203.0.113.2",
        )
        s.commit()

        assert devices.resolve_device_limit(s, user=free_user) == 1
        assert devices.resolve_device_limit(s, user=paid_user) == 3

        free_status = devices.device_limit_status(s, user=free_user, candidate_install_id="free-two")
        assert free_status == {
            "allowed": False,
            "limit": 1,
            "active_count": 1,
            "remaining": 0,
            "reason": "device_limit_reached",
        }

        same_device_status = devices.device_limit_status(s, user=free_user, candidate_install_id="free-one")
        assert same_device_status["allowed"] is True
        assert same_device_status["reason"] == "existing_device"
    finally:
        s.close()


def test_device_migration_backfills_legacy_user_row(monkeypatch, tmp_path):
    api, devices = _load_api_and_devices(monkeypatch, tmp_path)
    s = api.SessionLocal()
    legacy_seen = datetime(2026, 4, 23, 8, 30, 0)
    try:
        user = _user(api, 910006, sub_type="FREE", current_plan_code="trial")
        user.app_install_id = "legacy-install"
        user.app_device_name = "Legacy phone"
        user.app_platform = "android"
        user.app_os_version = "14"
        user.app_version = "0.9.0"
        user.app_last_seen_at = legacy_seen
        user.app_last_ip = "198.51.100.77"
        user.route_mode = "selected_apps"
        user.route_selected_apps_json = '["org.telegram.messenger"]'
        user.route_requires_elevated_privileges = False
        s.add(user)
        s.commit()

        importlib.import_module("migrations").run_migrations(importlib.import_module("db").engine)

        rows = devices.list_user_devices(s, user=user, current_install_id="legacy-install")
        assert len(rows) == 1
        assert rows[0]["id"] == "legacy-install"
        assert rows[0]["name"] == "Legacy phone"
        assert rows[0]["platform"] == "android"
        assert rows[0]["os_version"] == "14"
        assert rows[0]["app_version"] == "0.9.0"
        assert rows[0]["last_seen_at"].startswith("2026-04-23T08:30:00")
        assert rows[0]["route_mode"] == "selected_apps"
        assert rows[0]["selected_apps"] == ["org.telegram.messenger"]
        assert rows[0]["is_current"] is True
    finally:
        s.close()
