from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest


PORTAL_BOT_DIR = Path(__file__).resolve().parents[1] / "portal_bot"
if str(PORTAL_BOT_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_BOT_DIR))


import daily_panel_node_healthcheck as healthcheck  # noqa: E402
from daily_panel_node_healthcheck import (  # noqa: E402
    PolicyIdentityScope,
    _expected_codes_for_user,
    _panel_client_enabled,
    _panel_managed_identity,
    run,
)


NOW = datetime(2026, 8, 1, 10, 0, 0)


def _node(code: str, access_role: str, inbound_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        code=code,
        access_role=access_role,
        inbound_id=inbound_id,
        enabled=True,
        accepting_new_clients=True,
        is_draining=False,
    )


def _user(**overrides) -> SimpleNamespace:
    values = {
        "tg_id": 123,
        "uuid": "user-uuid",
        "sub_type": "FREE",
        "current_plan_code": "free_monthly",
        "is_active": True,
        "expiry_at": NOW + timedelta(days=30),
        "free_profile_state": "standard",
        "free_profile_active_role": "free_standard",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


POLICY_NODES = [
    _node("nl-free-standard", "free_standard", 41),
    _node("nl-free-soft", "free_soft", 42),
    _node("de-paid", "paid", 51),
]


def test_panel_managed_identity_matches_tg_id() -> None:
    assert _panel_managed_identity({"tgId": "123", "id": "uuid-a"}, {}) == 123


def test_panel_managed_identity_matches_legacy_user_email() -> None:
    assert _panel_managed_identity({"email": "User_456", "id": "uuid-b"}, {}) == 456


def test_panel_managed_identity_matches_expected_uuid_without_tg_id() -> None:
    assert _panel_managed_identity({"email": "legacy", "id": "uuid-c"}, {"uuid-c": 789}) == 789


def test_panel_client_enabled_understands_panel_boolean_formats() -> None:
    assert _panel_client_enabled({}) is True
    assert _panel_client_enabled({"enable": True}) is True
    assert _panel_client_enabled({"enable": "1"}) is True
    assert _panel_client_enabled({"enable": False}) is False
    assert _panel_client_enabled({"enable": "false"}) is False
    assert _panel_client_enabled({"enable": 0}) is False


def test_panel_rows_separates_actionable_manual_unresolved_and_unknown(monkeypatch) -> None:
    unresolved_uuid = "unresolved-uuid"
    inbounds = [
        {
            "settings": json.dumps(
                {
                    "clients": [
                        {"tgId": "1", "id": "expected-uuid", "enable": True},
                        {"tgId": "2", "id": "manual-uuid", "enable": True},
                        {"tgId": "", "id": unresolved_uuid, "email": "legacy", "enable": True},
                        {"tgId": "4", "id": "unexpected-uuid", "enable": True},
                        {"tgId": "", "id": "unknown-uuid", "email": "unknown", "enable": True},
                    ]
                }
            )
        }
    ]

    class FakeClient:
        async def _get_inbounds(self):
            return inbounds

        def _selected_inbounds(self, rows, *, include_disabled=False):
            assert include_disabled is True
            return rows

        @staticmethod
        def _decode_settings(raw):
            return json.loads(raw)

    class FakePanel:
        def __init__(self):
            self._clients = {"de": FakeClient()}

        async def refresh(self):
            return [SimpleNamespace(code="de", enabled=True)]

        async def close(self):
            return None

    monkeypatch.setattr(healthcheck, "ControlPanel", FakePanel)
    scope = PolicyIdentityScope(
        actionable_user_count=1,
        manual_tg_ids=frozenset({2}),
        manual_uuid_to_tg={"manual-uuid": 2},
        unresolved_tg_ids=frozenset({3}),
        unresolved_uuid_to_tg={unresolved_uuid: 3},
        unresolved_reasons={"entitlement_ambiguous": 1},
    )

    rows = __import__("asyncio").run(
        healthcheck._panel_rows(
            {"de": {1}},
            {"de": {"expected-uuid": 1}},
            scope,
        )
    )

    assert rows == [
        {
            "node": "de",
            "panel_clients_total": 5,
            "panel_clients_enabled": 5,
            "panel_clients_disabled": 0,
            "managed_actual": 4,
            "managed_enabled": 4,
            "managed_disabled": 0,
            "expected": 1,
            "missing": 0,
            "managed_unexpected": 1,
            "managed_actionable_unexpected": 1,
            "managed_unexpected_disabled": 0,
            "managed_manual_enabled": 1,
            "managed_manual_disabled": 0,
            "managed_policy_unresolved_enabled": 1,
            "managed_policy_unresolved_disabled": 0,
            "unknown_rows": 1,
            "_unexpected_enabled_identities": [4],
        }
    ]


def test_panel_rows_bounds_parallel_reads_keeps_order_and_isolates_failures(monkeypatch) -> None:
    active_reads = 0
    max_active_reads = 0
    started: list[str] = []

    class FakeClient:
        def __init__(self, code: str, delay: float, *, fails: bool = False) -> None:
            self.code = code
            self.delay = delay
            self.fails = fails

        async def _get_inbounds(self):
            nonlocal active_reads, max_active_reads
            active_reads += 1
            max_active_reads = max(max_active_reads, active_reads)
            started.append(self.code)
            try:
                await asyncio.sleep(self.delay)
                if self.fails:
                    raise RuntimeError("panel https://198.51.100.77:8443/?token=secret unavailable")
                return [
                    {
                        "settings": json.dumps(
                            {"clients": [{"tgId": "1" if self.code == "de" else "9", "enable": True}]}
                        )
                    }
                ]
            finally:
                active_reads -= 1

        def _selected_inbounds(self, rows, *, include_disabled=False):
            assert include_disabled is True
            return rows

        @staticmethod
        def _decode_settings(raw):
            return json.loads(raw)

    class FakePanel:
        def __init__(self) -> None:
            self._clients = {
                "de": FakeClient("de", 0.015),
                "nl": FakeClient("nl", 0.005, fails=True),
                "us": FakeClient("us", 0.10),
                "fi": FakeClient("fi", 0.005),
            }

        async def refresh(self):
            return [SimpleNamespace(code=code, enabled=True) for code in ("de", "nl", "us", "fi")]

        async def close(self):
            return None

    monkeypatch.setattr(healthcheck, "ControlPanel", FakePanel)
    monkeypatch.setattr(healthcheck, "PANEL_HEALTHCHECK_MAX_CONCURRENCY", 2)
    monkeypatch.setattr(healthcheck, "PANEL_HEALTHCHECK_NODE_TIMEOUT_SECONDS", 0.04)

    rows = asyncio.run(healthcheck._panel_rows({"de": {1}, "fi": set()}, {"de": {}, "fi": {}}))

    assert max_active_reads == 2
    assert max_active_reads <= 2
    assert started == ["de", "nl", "us", "fi"]
    assert [row["node"] for row in rows] == ["de", "nl", "us", "fi"]
    assert rows[0]["missing"] == 0
    assert rows[0]["managed_unexpected"] == 0
    assert rows[1] == {"node": "nl", "error": "panel_unavailable"}
    assert rows[2] == {"node": "us", "error": "panel_unavailable"}
    assert rows[3]["managed_unexpected"] == 1
    assert "198.51.100.77" not in json.dumps(rows)
    assert "secret" not in json.dumps(rows)


@pytest.mark.parametrize("state", ["soft_active", "reset_pending", "error"])
def test_expected_policy_never_routes_legacy_free_state(state: str) -> None:
    user = _user(free_profile_state=state, free_profile_active_role="free_soft")

    codes, reason = _expected_codes_for_user(user, POLICY_NODES, now=NOW)

    assert codes == []
    assert reason is None


def test_expected_policy_routes_every_active_trial_to_paid_nodes() -> None:
    bounded = _user(current_plan_code="trial", expiry_at=NOW + timedelta(days=5))
    stale_reservation = _user(current_plan_code="trial", expiry_at=NOW + timedelta(days=8))

    assert _expected_codes_for_user(bounded, POLICY_NODES, now=NOW) == (["de-paid"], None)
    assert _expected_codes_for_user(stale_reservation, POLICY_NODES, now=NOW) == (
        ["de-paid"],
        None,
    )


def test_expected_policy_ignores_inconsistent_legacy_free_role_state() -> None:
    user = _user(free_profile_state="soft_active", free_profile_active_role="free_standard")

    assert _expected_codes_for_user(user, POLICY_NODES, now=NOW) == ([], None)


def test_expected_policy_passes_exact_now_to_pool_authority(monkeypatch) -> None:
    observed: list[datetime] = []

    def fake_effective_status(_user, *, now):
        observed.append(now)
        return "PENDING"

    monkeypatch.setattr(
        healthcheck,
        "effective_user_access_status",
        fake_effective_status,
    )

    assert _expected_codes_for_user(_user(), POLICY_NODES, now=NOW) == ([], None)
    assert observed == [NOW]


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
            PolicyIdentityScope(actionable_user_count=1),
        ),
    )

    async def fake_panel_rows(_expected_by_node, _expected_uuid_by_node, _policy_scope):
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


def test_daily_health_retains_enabled_access_drift_as_non_paging_observation(monkeypatch, tmp_path) -> None:
    report_dir = tmp_path / "reports"
    monkeypatch.setattr("daily_panel_node_healthcheck.REPORT_DIR", report_dir)
    monkeypatch.setattr("daily_panel_node_healthcheck._api_health", lambda: {"ok": True})
    monkeypatch.setattr("daily_panel_node_healthcheck._systemctl_is_active", lambda _unit: "active")
    monkeypatch.setattr("daily_panel_node_healthcheck._send_telegram_report", lambda _text: None)
    monkeypatch.setattr(
        "daily_panel_node_healthcheck._expected_node_sets",
        lambda _now: (
            {"de": set(), "us": set()},
            {"de": {}, "us": {}},
            [
                {
                    "code": code,
                    "is_healthy": True,
                    "stale": False,
                }
                for code in ("de", "us")
            ],
            PolicyIdentityScope(),
        ),
    )

    async def fake_panel_rows(_expected_by_node, _expected_uuid_by_node, _policy_scope):
        return [
            {
                "node": "de",
                "missing": 0,
                "managed_unexpected": 2,
                "managed_unexpected_disabled": 4,
                "_unexpected_enabled_identities": [101, 102],
            },
            {
                "node": "us",
                "missing": 0,
                "managed_unexpected": 1,
                "managed_unexpected_disabled": 3,
                "_unexpected_enabled_identities": [101],
            },
        ]

    monkeypatch.setattr("daily_panel_node_healthcheck._panel_rows", fake_panel_rows)

    assert __import__("asyncio").run(run()) == 0
    report_path = next(report_dir.glob("panel_node_health_*.json"))
    report = __import__("json").loads(report_path.read_text(encoding="utf-8"))
    assert report["issues"] == []
    assert report["observations"] == ["panel_access_drift_enabled_2_identities_3_placements"]
    assert "_unexpected_enabled_identities" not in report_path.read_text(encoding="utf-8")


def test_daily_health_does_not_page_on_disabled_unexpected_entries(monkeypatch, tmp_path) -> None:
    report_dir = tmp_path / "reports"
    monkeypatch.setattr("daily_panel_node_healthcheck.REPORT_DIR", report_dir)
    monkeypatch.setattr("daily_panel_node_healthcheck._api_health", lambda: {"ok": True})
    monkeypatch.setattr("daily_panel_node_healthcheck._systemctl_is_active", lambda _unit: "active")
    monkeypatch.setattr("daily_panel_node_healthcheck._send_telegram_report", lambda _text: None)
    monkeypatch.setattr(
        "daily_panel_node_healthcheck._expected_node_sets",
        lambda _now: (
            {"de": set()},
            {"de": {}},
            [{"code": "de", "is_healthy": True, "stale": False}],
            PolicyIdentityScope(),
        ),
    )

    async def fake_panel_rows(_expected_by_node, _expected_uuid_by_node, _policy_scope):
        return [
            {
                "node": "de",
                "missing": 0,
                "managed_unexpected": 0,
                "managed_unexpected_disabled": 7,
                "_unexpected_enabled_identities": [],
            }
        ]

    monkeypatch.setattr("daily_panel_node_healthcheck._panel_rows", fake_panel_rows)

    assert __import__("asyncio").run(run()) == 0


def test_daily_health_separates_and_redacts_manual_and_unresolved_policy(monkeypatch, tmp_path) -> None:
    report_dir = tmp_path / "reports"
    manual_tg_id = 918_273_645
    unresolved_tg_id = 817_263_544
    manual_uuid = "manual-secret-uuid"
    unresolved_uuid = "unresolved-secret-uuid"
    policy_scope = PolicyIdentityScope(
        actionable_user_count=2,
        manual_tg_ids=frozenset({manual_tg_id}),
        manual_uuid_to_tg={manual_uuid: manual_tg_id},
        unresolved_tg_ids=frozenset({unresolved_tg_id}),
        unresolved_uuid_to_tg={unresolved_uuid: unresolved_tg_id},
        unresolved_reasons={"entitlement_ambiguous": 1},
    )
    monkeypatch.setattr(healthcheck, "REPORT_DIR", report_dir)
    monkeypatch.setattr(healthcheck, "_api_health", lambda: {"ok": True})
    monkeypatch.setattr(healthcheck, "_systemctl_is_active", lambda _unit: "active")
    monkeypatch.setattr(healthcheck, "_send_telegram_report", lambda _text: None)
    monkeypatch.setattr(
        healthcheck,
        "_expected_node_sets",
        lambda _now: (
            {"de": set()},
            {"de": {}},
            [{"code": "de", "is_healthy": True, "stale": False}],
            policy_scope,
        ),
    )

    async def fake_panel_rows(_expected_by_node, _expected_uuid_by_node, received_scope):
        assert received_scope is policy_scope
        return [
            {
                "node": "de",
                "missing": 0,
                "managed_actionable_unexpected": 0,
                "managed_unexpected": 0,
                "managed_manual_enabled": 1,
                "managed_policy_unresolved_enabled": 1,
                "unknown_rows": 0,
                "_unexpected_enabled_identities": [],
            }
        ]

    monkeypatch.setattr(healthcheck, "_panel_rows", fake_panel_rows)

    assert __import__("asyncio").run(run()) == 1
    report_path = next(report_dir.glob("panel_node_health_*.json"))
    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert report["checks"]["access_policy"] == {
        "actionable_users": 2,
        "manual_users": 1,
        "policy_unresolved_users": 1,
        "policy_unresolved_reasons": {"entitlement_ambiguous": 1},
    }
    assert report["issues"] == ["panel_policy_unresolved_1_users"]
    assert str(manual_tg_id) not in report_text
    assert str(unresolved_tg_id) not in report_text
    assert manual_uuid not in report_text
    assert unresolved_uuid not in report_text
