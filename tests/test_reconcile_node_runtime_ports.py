from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


@pytest.fixture()
def service():
    spec = importlib.util.spec_from_file_location("reconcile_node_runtime_ports", REPO_ROOT / "scripts" / "reconcile_node_runtime_ports.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(spec.name, None)


def _node(Node, *, code: str, port: int = 443):
    return Node(
        code=code,
        host="example.test",
        enabled=True,
        inbound_id=1,
        vless_port=port,
        reality_sni="example.com",
        reality_sid="sid",
        reality_pbk="public-key",
        transport_profiles_json=json.dumps(
            [{"name": "legacy_reality_fallback", "enabled": True, "kind": "reality", "inbound_id": 1, "port": port, "tls_server_name": "example.com", "reality_short_id": "sid", "reality_public_key": "public-key", "flow": "xtls-rprx-vision"}]
        ),
    )


def _runtime(*, port: int):
    return {
        "inbound_id": 1,
        "enable": True,
        "port": port,
        "protocol": "vless",
        "network": "tcp",
        "security": "reality",
        "dest": "example.com:443",
        "server_names": ["example.com"],
        "short_ids": ["sid"],
        "public_key": "public-key",
    }


def test_dry_run_plan_is_port_only_and_does_not_mutate_node(service):
    from models import Node

    node = _node(Node, code="ru")
    before = node.transport_profiles_json
    row = service.plan_node_port_repair(node, _runtime(port=8443), profile_name="legacy_reality_fallback")

    assert row["status"] == "topology_unattested"
    assert row["mismatches"] == ["port"]
    assert row["current_port"] == 443
    assert row["runtime_port"] == 8443
    assert node.transport_profiles_json == before
    assert node.vless_port == 443


def test_apply_guards_require_exact_allowlist_and_confirmations(service):
    plan = [{"code": "ru", "status": "topology_unattested", "current_port": 443, "runtime_port": 8443}]
    confirmation = service.parse_confirmations(["ru:443:8443"])
    attestation = service.parse_direct_listener_attestations(["ru:8443"])

    assert service.validate_apply_plan(
        plan,
        only=["ru"],
        confirmations=confirmation,
        direct_listener_attestations=attestation,
    ) == plan
    with pytest.raises(service.RepairGuardError):
        service.validate_apply_plan(
            plan,
            only=["ru", "ru_spb"],
            confirmations=confirmation,
            direct_listener_attestations=attestation,
        )
    with pytest.raises(service.RepairGuardError):
        service.validate_apply_plan(
            [{**plan[0], "status": "blocked"}],
            only=["ru"],
            confirmations=confirmation,
            direct_listener_attestations=attestation,
        )
    with pytest.raises(service.RepairGuardError):
        service.validate_apply_plan(
            plan,
            only=["ru"],
            confirmations=confirmation,
            direct_listener_attestations={},
        )
    with pytest.raises(service.RepairGuardError):
        service.validate_apply_plan(
            plan,
            only=["ru"],
            confirmations=confirmation,
            direct_listener_attestations=service.parse_direct_listener_attestations(["ru:9443"]),
        )


def test_plan_blocks_any_non_port_inbound_drift(service):
    from models import Node

    node = _node(Node, code="ru")
    node.inbound_id = 100_000
    profiles = json.loads(node.transport_profiles_json)
    profiles[0]["inbound_id"] = 100_000
    node.transport_profiles_json = json.dumps(profiles)
    runtime = _runtime(port=8443)
    runtime["inbound_id"] = 100_000
    runtime["public_key"] = "different-public-key"

    row = service.plan_node_port_repair(node, runtime, profile_name="legacy_reality_fallback")

    assert row["status"] == "blocked"
    assert row["mismatches"] == ["port", "public_key"]


def test_apply_cas_updates_all_or_rolls_back_on_concurrent_change(service):
    from models import Base, Node

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        first, second = _node(Node, code="ru"), _node(Node, code="ru_spb")
        session.add_all([first, second])
        session.commit()
        plan = [
            service.plan_node_port_repair(first, _runtime(port=8443), profile_name="legacy_reality_fallback"),
            service.plan_node_port_repair(second, _runtime(port=8443), profile_name="legacy_reality_fallback"),
        ]

        changed = json.loads(second.transport_profiles_json)
        changed[0]["port"] = 9443
        second.transport_profiles_json = json.dumps(changed)
        session.commit()

        with pytest.raises(service.RepairGuardError):
            service.apply_port_repairs(session, plan)
        session.expire_all()
        assert session.query(Node).filter_by(code="ru").one().vless_port == 443

        fresh_second = session.query(Node).filter_by(code="ru_spb").one()
        fresh_second.transport_profiles_json = plan[1]["profiles_before"]
        session.commit()
        read_back = service.apply_port_repairs(session, plan)
        assert [row["status"] for row in read_back] == ["applied", "applied"]
        assert session.query(Node).filter_by(code="ru").one().vless_port == 8443
    finally:
        session.close()
        engine.dispose()


def test_apply_cas_rejects_concurrent_inherited_profile_source_change(service):
    from models import Base, Node

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        node = _node(Node, code="ru")
        profiles = json.loads(node.transport_profiles_json)
        profiles[0].pop("reality_public_key")
        node.transport_profiles_json = json.dumps(profiles)
        session.add(node)
        session.commit()

        plan = [service.plan_node_port_repair(node, _runtime(port=8443), profile_name="legacy_reality_fallback")]
        assert plan[0]["status"] == "topology_unattested"

        node.reality_pbk = "changed-public-key"
        session.commit()

        with pytest.raises(service.RepairGuardError):
            service.apply_port_repairs(session, plan)

        session.expire_all()
        restored = session.query(Node).filter_by(code="ru").one()
        assert restored.vless_port == 443
        assert restored.reality_pbk == "changed-public-key"
    finally:
        session.close()
        engine.dispose()


def test_apply_readback_mismatch_compensates_with_guarded_preimage(service, monkeypatch):
    from models import Base, Node

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        node = _node(Node, code="ru")
        session.add(node)
        session.commit()
        plan = [service.plan_node_port_repair(node, _runtime(port=8443), profile_name="legacy_reality_fallback")]

        monkeypatch.setattr(
            service,
            "_readback_port_repairs",
            lambda _session, _rows: [
                {
                    "code": "ru",
                    "current_port": 8443,
                    "runtime_port": 8443,
                    "status": "readback_mismatch",
                    "mismatches": ["readback_port"],
                }
            ],
        )

        result = service.apply_port_repairs(session, plan)

        assert result[0]["status"] == "readback_mismatch"
        assert result[0]["rollback_status"] == "rolled_back"
        session.expire_all()
        assert session.query(Node).filter_by(code="ru").one().vless_port == 443
    finally:
        session.close()
        engine.dispose()


def test_apply_readback_exception_compensates_with_guarded_preimage(service, monkeypatch):
    from models import Base, Node

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        node = _node(Node, code="ru")
        session.add(node)
        session.commit()
        plan = [service.plan_node_port_repair(node, _runtime(port=8443), profile_name="legacy_reality_fallback")]

        def fail_readback(_session, _rows):
            raise RuntimeError("synthetic readback failure with must-not-print")

        monkeypatch.setattr(service, "_readback_port_repairs", fail_readback)

        result = service.apply_port_repairs(session, plan)

        assert result == [
            {
                "code": "ru",
                "current_port": 443,
                "runtime_port": 8443,
                "status": "readback_error",
                "mismatches": ["readback"],
                "rollback_status": "rolled_back",
            }
        ]
        session.expire_all()
        assert session.query(Node).filter_by(code="ru").one().vless_port == 443
    finally:
        session.close()
        engine.dispose()


def test_apply_rebuilds_fresh_plan_before_confirmation_and_does_not_mutate_on_change(service, monkeypatch):
    initial = [
        {
            "code": "ru",
            "status": "topology_unattested",
            "current_port": 443,
            "runtime_port": 8443,
        }
    ]
    fresh = [{**initial[0], "runtime_port": 9443}]
    plans = iter((initial, fresh))
    applied = MagicMock()
    monkeypatch.setattr(
        service,
        "_parse_args",
        lambda: SimpleNamespace(
            only="ru",
            profile="legacy_reality_fallback",
            apply=True,
            confirm=["ru:443:8443"],
            attest_direct_listener=["ru:8443"],
        ),
    )

    async def collect_plan(**_kwargs):
        return next(plans)

    monkeypatch.setattr(service, "collect_plan", collect_plan)
    monkeypatch.setattr(service, "apply_port_repairs", applied)

    assert service.main() == 2

    assert applied.call_count == 0


def test_main_returns_nonzero_with_redacted_rollback_evidence(service, monkeypatch, capsys):
    plan = [
        {
            "code": "ru",
            "status": "topology_unattested",
            "current_port": 443,
            "runtime_port": 8443,
        }
    ]
    session = MagicMock()
    monkeypatch.setattr(
        service,
        "_parse_args",
        lambda: SimpleNamespace(
            only="ru",
            profile="legacy_reality_fallback",
            apply=True,
            confirm=["ru:443:8443"],
            attest_direct_listener=["ru:8443"],
        ),
    )

    async def collect_plan(**_kwargs):
        return plan

    monkeypatch.setattr(service, "collect_plan", collect_plan)
    monkeypatch.setattr(service, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        service,
        "apply_port_repairs",
        lambda _session, _plan: [
            {
                "code": "ru",
                "current_port": 8443,
                "runtime_port": 8443,
                "status": "readback_mismatch",
                "mismatches": ["readback_port"],
                "rollback_status": "rolled_back",
                "profile_source_before": {"reality_pbk": "must-not-print"},
            }
        ],
    )

    assert service.main() == 3

    output = capsys.readouterr().out
    assert "rollback_status" in output
    assert "profile_source_before" not in output
    assert "must-not-print" not in output
    session.close.assert_called_once()


def test_main_returns_redacted_block_for_malformed_attestation(service, monkeypatch, capsys):
    plan = [
        {
            "code": "ru",
            "status": "topology_unattested",
            "current_port": 443,
            "runtime_port": 8443,
        }
    ]
    monkeypatch.setattr(
        service,
        "_parse_args",
        lambda: SimpleNamespace(
            only="ru",
            profile="legacy_reality_fallback",
            apply=True,
            confirm=["ru:443:8443"],
            attest_direct_listener=["malformed:8443:must-not-print"],
        ),
    )

    async def collect_plan(**_kwargs):
        return plan

    monkeypatch.setattr(service, "collect_plan", collect_plan)

    assert service.main() == 2
    output = capsys.readouterr().out
    assert '"status": "blocked"' in output
    assert "must-not-print" not in output


def test_collect_plan_rejects_unknown_or_disabled_allowlist(service, monkeypatch):
    session = MagicMock()
    session.query.return_value = MagicMock()
    monkeypatch.setattr(service, "SessionLocal", lambda: session)
    monkeypatch.setattr(
        service,
        "enabled_nodes",
        lambda _session: [SimpleNamespace(code="ru")],
    )

    with pytest.raises(service.RepairGuardError):
        import asyncio

        asyncio.run(
            service.collect_plan(
                only=["ru", "ru_spb"],
                profile_name="legacy_reality_fallback",
            )
        )

    session.close.assert_called_once()
