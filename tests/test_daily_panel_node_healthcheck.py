from __future__ import annotations

import sys
from pathlib import Path


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


from daily_panel_node_healthcheck import _panel_managed_identity, run  # noqa: E402


def test_panel_managed_identity_matches_tg_id() -> None:
    assert _panel_managed_identity({"tgId": "123", "id": "uuid-a"}, {}) == 123


def test_panel_managed_identity_matches_legacy_user_email() -> None:
    assert _panel_managed_identity({"email": "User_456", "id": "uuid-b"}, {}) == 456


def test_panel_managed_identity_matches_expected_uuid_without_tg_id() -> None:
    assert _panel_managed_identity({"email": "legacy", "id": "uuid-c"}, {"uuid-c": 789}) == 789


def test_daily_health_does_not_warn_on_retained_user_node_mappings(monkeypatch, tmp_path) -> None:
    report_dir = tmp_path / "reports"
    monkeypatch.setattr("daily_panel_node_healthcheck.REPORT_DIR", report_dir)
    monkeypatch.setattr("daily_panel_node_healthcheck._api_health", lambda: {"ok": True})
    monkeypatch.setattr("daily_panel_node_healthcheck._systemctl_is_active", lambda _unit: "active")
    monkeypatch.setattr("daily_panel_node_healthcheck._send_telegram_report", lambda _text: None)
    monkeypatch.setattr(
        "daily_panel_node_healthcheck._expected_node_sets",
        lambda _now: (
            {"de": {1}},
            {"de": {"uuid-1": 1}},
            [
                {
                    "code": "de",
                    "is_healthy": True,
                    "health_score": 90.0,
                    "panel_latency_ms": 100,
                    "active_clients": 2,
                    "last_health_at": "2026-07-07T16:00:00",
                    "stale": False,
                    "mapped_users": 2,
                    "expected_users": 1,
                }
            ],
        ),
    )

    async def fake_panel_rows(_expected_by_node, _expected_uuid_by_node):
        return [
            {
                "node": "de",
                "panel_clients_total": 2,
                "managed_actual": 1,
                "expected": 1,
                "missing": 0,
                "managed_unexpected": 0,
                "unknown_rows": 1,
            }
        ]

    monkeypatch.setattr("daily_panel_node_healthcheck._panel_rows", fake_panel_rows)

    assert __import__("asyncio").run(run()) == 0
    report = next(report_dir.glob("panel_node_health_*.json")).read_text(encoding="utf-8")
    assert "node_de_mapping_2_expected_1" not in report
