from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest


GIB = 1024**3


def _node(role: str, inbound_id: int = 41):
    return SimpleNamespace(
        code=f"nl-{role.replace('_', '-')}",
        access_role=role,
        inbound_id=inbound_id,
        flow="xtls-rprx-vision",
        panel_base_url="https://nl-free.test:8444",
        panel_path="panel",
        panel_user="user",
        panel_pass="pass",
        transport_profiles_json=None,
    )


@pytest.mark.parametrize(
    ("role", "expected_total", "expected_limit_ip"),
    [
        ("free_standard", 5 * GIB, 1),
        ("free_soft", 0, 1),
        ("paid", 0, 5),
        ("operator_lab", 0, 5),
    ],
)
def test_role_policy_payload_limits_are_explicit_and_free_quota_is_not_env_overridable(
    monkeypatch,
    role: str,
    expected_total: int,
    expected_limit_ip: int,
) -> None:
    from panel_client import PanelClient

    monkeypatch.setenv("FREE_TOTAL_GB", "99")
    monkeypatch.setenv("FREE_LIMIT_IP", "9")
    client = PanelClient(_node(role))
    assert client._total_bytes_policy() == expected_total
    assert client._limit_ip_policy() == expected_limit_ip


def test_explicit_ensure_targets_one_inbound_without_cross_inbound_cleanup() -> None:
    from panel_client import PanelClient

    client = PanelClient(_node("free_soft", inbound_id=42))
    calls: list[tuple[str, dict]] = []

    async def find_clients_by_identity(**_kwargs):
        return []

    async def add_client(**kwargs):
        calls.append(("add", kwargs))
        return True

    async def cleanup(**_kwargs):
        calls.append(("cleanup", {}))
        return True

    client.find_clients_by_identity = find_clients_by_identity
    client.add_client = add_client
    client._cleanup_cross_inbound_conflicts = cleanup

    ok = asyncio.run(
        client.ensure_client_explicit(
            tg_id=4001,
            client_uuid="00000000-0000-4000-8000-000000004001",
            email="user-4001@example.test",
            sub_id="sub-4001",
            enable=True,
            inbound_id=42,
            total_bytes=0,
            limit_ip=1,
        )
    )
    assert ok is True
    assert [name for name, _payload in calls] == ["add"]
    assert calls[0][1]["inbound_id"] == 42
    assert calls[0][1]["total_bytes_override"] == 0
    assert calls[0][1]["limit_ip_override"] == 1


def test_explicit_confirmation_requires_exact_inbound_limit_and_enabled_state() -> None:
    from panel_client import PanelClient

    client = PanelClient(_node("free_standard", inbound_id=41))

    async def exact(**_kwargs):
        return [
            (
                41,
                {
                    "id": "uuid-4002",
                    "email": "user-4002@example.test",
                    "tgId": "4002",
                    "enable": True,
                    "totalGB": 5 * GIB,
                    "limitIp": 1,
                },
            )
        ]

    client.find_clients_by_identity = exact
    assert asyncio.run(
        client.confirm_client_profile(
            tg_id=4002,
            client_uuid="uuid-4002",
            email="user-4002@example.test",
            inbound_id=41,
            total_bytes=5 * GIB,
            limit_ip=1,
            enabled=True,
        )
    )

    async def wrong_paid_inbound(**_kwargs):
        return [(43, {"id": "uuid-4002", "tgId": "4002", "enable": True, "totalGB": 0, "limitIp": 5})]

    client.find_clients_by_identity = wrong_paid_inbound
    assert not asyncio.run(
        client.confirm_client_profile(
            tg_id=4002,
            client_uuid="uuid-4002",
            email="user-4002@example.test",
            inbound_id=41,
            total_bytes=5 * GIB,
            limit_ip=1,
            enabled=True,
        )
    )


def test_uuid_rotation_addresses_old_client_but_sends_new_uuid() -> None:
    from panel_client import PanelClient

    calls: list[tuple[str, dict]] = []

    class Response:
        status = 200

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def json(self, **_kwargs):
            return {"success": True}

    class Session:
        def post(self, url, **kwargs):
            calls.append((url, kwargs))
            return Response()

    client = PanelClient(_node("free_standard", inbound_id=41))
    client.cookies = {"session": "test"}
    client.session = Session()

    async def ensure_session():
        return None

    async def csrf_headers():
        return {}

    client.ensure_session = ensure_session
    client._csrf_headers = csrf_headers

    old_uuid = "00000000-0000-4000-8000-000000004003"
    new_uuid = "00000000-0000-4000-8000-000000004004"
    ok = asyncio.run(
        client.update_client_enable(
            {
                "id": new_uuid,
                "email": "user-4003@example.test",
                "tgId": "4003",
                "enable": True,
            },
            True,
            inbound_id=41,
            total_bytes_override=5 * GIB,
            limit_ip_override=1,
            lookup_client_uuid=old_uuid,
        )
    )

    assert ok is True
    assert calls[0][0].endswith(f"/panel/api/inbounds/updateClient/{old_uuid}")
    payload = calls[0][1]["json"]
    assert payload["id"] == 41
    assert new_uuid in payload["settings"]
    assert old_uuid not in payload["settings"]


def test_paid_source_disable_updates_every_managed_inbound() -> None:
    from control_panel import ControlPanel

    node = _node("paid", inbound_id=43)
    node.code = "nl-paid"
    calls: list[tuple[int, bool]] = []

    class Client:
        async def find_clients_by_tgid(self, tg_id: int, *, include_disabled: bool = False):
            assert tg_id == 4005
            assert include_disabled is True
            return [
                (43, {"id": "uuid-4005", "tgId": "4005", "_panel_inbound_id": 43}),
                (44, {"id": "uuid-4005", "tgId": "4005", "_panel_inbound_id": 44}),
            ]

        async def update_client_enable(self, client, enable, **kwargs):
            calls.append((kwargs["inbound_id"], bool(enable)))
            return True

    panel = ControlPanel()

    async def resolve(node_code: str, expected_access_role: str):
        assert node_code == "nl-paid"
        assert expected_access_role == "paid"
        return node

    panel._resolve_exact_role_node = resolve
    panel._clients = {"nl-paid": Client()}

    ok = asyncio.run(
        panel.set_user_profile_enabled_on_node(
            tg_id=4005,
            node_code="nl-paid",
            expected_access_role="paid",
            enable=False,
            sub_id="sub-4005",
        )
    )

    assert ok is True
    assert calls == [(43, False), (44, False)]


def test_paid_source_restore_never_enables_operator_lab_transport() -> None:
    from control_panel import ControlPanel

    node = _node("paid", inbound_id=43)
    node.code = "nl-paid"
    calls: list[tuple[int, bool]] = []

    class Client:
        async def find_clients_by_tgid(self, tg_id: int, *, include_disabled: bool = False):
            assert tg_id == 4006
            assert include_disabled is True
            return [
                (
                    43,
                    {
                        "id": "uuid-4006",
                        "tgId": "4006",
                        "_panel_inbound_id": 43,
                        "_transport_profile": "grpc_443_primary",
                    },
                ),
                (
                    44,
                    {
                        "id": "uuid-4006",
                        "tgId": "4006",
                        "_panel_inbound_id": 44,
                        "_transport_profile": "operator_lab",
                    },
                ),
            ]

        async def update_client_enable(self, client, enable, **kwargs):
            calls.append((kwargs["inbound_id"], bool(enable)))
            return True

    panel = ControlPanel()

    async def resolve(node_code: str, expected_access_role: str):
        assert node_code == "nl-paid"
        assert expected_access_role == "paid"
        return node

    panel._resolve_exact_role_node = resolve
    panel._clients = {"nl-paid": Client()}

    ok = asyncio.run(
        panel.set_user_profile_enabled_on_node(
            tg_id=4006,
            node_code="nl-paid",
            expected_access_role="paid",
            enable=True,
            sub_id="sub-4006",
        )
    )

    assert ok is True
    assert calls == [(43, True)]


def test_control_panel_legacy_free_resolution_uses_persisted_soft_role() -> None:
    from control_panel import ControlPanel

    nodes = [
        _node("free_standard", inbound_id=41),
        _node("free_soft", inbound_id=42),
    ]
    nodes[0].code = "nl-free-standard"
    nodes[1].code = "nl-free-soft"
    user = SimpleNamespace(
        sub_type="FREE",
        current_plan_code="free_monthly",
        free_profile_state="soft_active",
        free_profile_active_role="free_soft",
    )

    assert ControlPanel._free_node_codes(nodes, user=user) == ["nl-free-soft"]
