from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "free_soft_inbound_shaper.py"
FIXTURE_PATH = REPO_ROOT / "infra" / "free-soft-inbound.json"


def _load_module():
    assert SCRIPT_PATH.exists(), "free-soft inbound shaper script is missing"
    spec = importlib.util.spec_from_file_location(
        "free_soft_inbound_shaper_under_test",
        SCRIPT_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _default_config(module):
    return module.load_config(FIXTURE_PATH)


def test_setup_plan_builds_symmetric_ipv4_ipv6_two_mbit_policing() -> None:
    module = _load_module()
    config = _default_config(module)

    plan = module.build_plan("setup", config)

    assert [step.name for step in plan.steps] == [
        "validate-ruleset",
        "apply-ruleset",
    ]
    assert plan.steps[0].argv == ("nft", "--check", "-f", "-")
    assert plan.steps[1].argv == ("nft", "-f", "-")
    assert plan.steps[0].mutating is False
    assert plan.steps[1].mutating is True
    assert plan.steps[0].stdin == plan.steps[1].stdin

    ruleset = plan.steps[1].stdin
    assert ruleset is not None
    assert "250 kbytes/second" in ruleset
    assert "meta nfproto ipv4" in ruleset
    assert "meta nfproto ipv6" in ruleset
    assert ruleset.count("meta l4proto { tcp, udp }") == 4
    assert ruleset.count("th dport 8443") == 2
    assert ruleset.count("th sport 8443") == 2
    assert "meter " not in ruleset
    assert ruleset.count("flags dynamic,timeout") == 4
    assert ruleset.count("limit rate over 250 kbytes/second") == 4
    assert "update @pkr_soft_v4_in { ip saddr timeout 10m" in ruleset
    assert "update @pkr_soft_v6_in { ip6 saddr timeout 10m" in ruleset
    assert "update @pkr_soft_v4_out { ip daddr timeout 10m" in ruleset
    assert "update @pkr_soft_v6_out { ip6 daddr timeout 10m" in ruleset
    assert ruleset.count("size 65535") == 4
    assert 'iifname "eth0"' in ruleset
    assert 'oifname "eth0"' in ruleset


def test_setup_plan_is_deterministic_idempotent_and_bounded_to_owned_table() -> None:
    module = _load_module()
    config = _default_config(module)

    first = module.build_plan("setup", config)
    second = module.build_plan("setup", config)

    assert first == second
    ruleset = first.steps[1].stdin or ""
    assert ruleset.startswith("destroy table inet pokrov_free_soft\n")
    assert ruleset.count("table inet pokrov_free_soft") == 2
    assert "chain pkr_soft_input" in ruleset
    assert "chain pkr_soft_output" in ruleset
    assert "flush ruleset" not in ruleset
    assert "tc " not in ruleset
    assert len(first.steps) == 2


def test_audit_plan_is_read_only_and_scoped() -> None:
    module = _load_module()

    plan = module.build_plan("audit", _default_config(module))

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.name == "audit-owned-table"
    assert step.argv == (
        "nft",
        "--json",
        "list",
        "table",
        "inet",
        "pokrov_free_soft",
    )
    assert step.stdin is None
    assert step.mutating is False
    assert all(
        token not in step.argv
        for token in ("add", "delete", "destroy", "flush", "replace")
    )


def test_rollback_plan_is_idempotent_and_only_destroys_owned_table() -> None:
    module = _load_module()

    plan = module.build_plan("rollback", _default_config(module))

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.argv == ("nft", "-f", "-")
    assert step.stdin == "destroy table inet pokrov_free_soft\n"
    assert step.mutating is True
    assert "flush ruleset" not in (step.stdin or "")


@pytest.mark.parametrize(
    ("overrides", "error_code"),
    [
        ({"iface": ""}, "invalid_iface"),
        ({"iface": "eth0; reboot"}, "invalid_iface"),
        ({"iface": "x" * 16}, "invalid_iface"),
        ({"port": 0}, "invalid_port"),
        ({"port": 65536}, "invalid_port"),
        ({"port": "8443; reboot"}, "invalid_port"),
        ({"rate": "0mbit"}, "invalid_rate"),
        ({"rate": "2mbit; reboot"}, "invalid_rate"),
        ({"rate": "2MBps"}, "invalid_rate"),
        ({"meter_size": 0}, "invalid_meter_size"),
        ({"meter_timeout": "forever"}, "invalid_meter_timeout"),
        ({"burst_kbytes": 0}, "invalid_burst"),
    ],
)
def test_config_rejects_unsafe_or_unbounded_values(overrides, error_code) -> None:
    module = _load_module()
    payload = {
        "iface": "eth0",
        "port": 8443,
        "rate": "2mbit",
        "meter_size": 65535,
        "meter_timeout": "10m",
        "burst_kbytes": 64,
    }
    payload.update(overrides)

    with pytest.raises(module.ConfigError) as raised:
        module.ShaperConfig.from_mapping(payload)

    assert raised.value.code == error_code
    assert all(
        not str(value) or str(value) not in str(raised.value)
        for value in overrides.values()
    )


def test_direct_config_construction_cannot_bypass_validation() -> None:
    module = _load_module()

    with pytest.raises(module.ConfigError) as raised:
        module.ShaperConfig(
            iface="eth0; reboot",
            port=8443,
            rate="2mbit",
            meter_size=65535,
            meter_timeout="10m",
            burst_kbytes=64,
        )

    assert raised.value.code == "invalid_iface"


def test_dry_run_never_calls_executor() -> None:
    module = _load_module()
    calls = []

    def executor(argv, stdin):
        calls.append((argv, stdin))
        return 0, "", ""

    report = module.execute_plan(
        module.build_plan("setup", _default_config(module)),
        apply=False,
        executor=executor,
        platform_name="Linux",
    )

    assert calls == []
    assert report["mode"] == "dry-run"
    assert report["status"] == "planned"
    assert report["redacted"] is True


def test_apply_uses_injected_local_executor_in_order() -> None:
    module = _load_module()
    calls = []

    def executor(argv, stdin):
        calls.append((argv, stdin))
        return 0, "ignored output", "ignored error"

    plan = module.build_plan("setup", _default_config(module))
    report = module.execute_plan(
        plan,
        apply=True,
        executor=executor,
        platform_name="Linux",
    )

    assert calls == [(step.argv, step.stdin) for step in plan.steps]
    assert report["mode"] == "apply"
    assert report["status"] == "ok"
    assert [item["status"] for item in report["results"]] == ["ok", "ok"]


def test_apply_stops_on_partial_failure_without_echoing_executor_output() -> None:
    module = _load_module()
    calls = []

    def executor(argv, stdin):
        calls.append((argv, stdin))
        if len(calls) == 1:
            return 0, "token=first-secret", ""
        return 17, "password=second-secret", "private-key=third-secret"

    report = module.execute_plan(
        module.build_plan("setup", _default_config(module)),
        apply=True,
        executor=executor,
        platform_name="Linux",
    )
    encoded = json.dumps(report, sort_keys=True)

    assert len(calls) == 2
    assert report["status"] == "failed"
    assert report["failed_step"] == "apply-ruleset"
    assert report["error_code"] == "command_failed"
    assert "first-secret" not in encoded
    assert "second-secret" not in encoded
    assert "third-secret" not in encoded


def test_executor_exception_is_redacted() -> None:
    module = _load_module()

    def executor(argv, stdin):
        raise RuntimeError("token=must-never-leak")

    report = module.execute_plan(
        module.build_plan("rollback", _default_config(module)),
        apply=True,
        executor=executor,
        platform_name="Linux",
    )

    assert report["status"] == "failed"
    assert report["error_code"] == "executor_exception"
    assert "must-never-leak" not in json.dumps(report)


def test_apply_is_refused_off_linux_without_executor_calls() -> None:
    module = _load_module()
    calls = []

    def executor(argv, stdin):
        calls.append((argv, stdin))
        return 0, "", ""

    report = module.execute_plan(
        module.build_plan("rollback", _default_config(module)),
        apply=True,
        executor=executor,
        platform_name="Windows",
    )

    assert calls == []
    assert report["status"] == "refused"
    assert report["error_code"] == "linux_required"


def test_live_audit_execution_remains_read_only() -> None:
    module = _load_module()
    calls = []

    def executor(argv, stdin):
        calls.append((argv, stdin))
        return 0, '{"nftables": []}', ""

    plan = module.build_plan("audit", _default_config(module))
    report = module.execute_plan(
        plan,
        apply=True,
        executor=executor,
        platform_name="Linux",
    )

    assert calls == [(plan.steps[0].argv, None)]
    assert all(step.mutating is False for step in plan.steps)
    assert report["status"] == "ok"


def test_fixture_and_json_cli_report_state_per_ip_nat_limit_honestly() -> None:
    module = _load_module()
    output = io.StringIO()

    exit_code = module.main(
        ["setup", "--config", str(FIXTURE_PATH)],
        executor=lambda argv, stdin: (_ for _ in ()).throw(
            AssertionError("dry-run executed a command")
        ),
        platform_name="Windows",
        stdout=output,
    )
    report = json.loads(output.getvalue())

    assert exit_code == 0
    assert report["status"] == "planned"
    assert report["scope"]["rate"] == "2mbit"
    assert report["scope"]["nft_rate"] == "250 kbytes/second"
    assert report["scope"]["per_client_ip"] is True
    assert report["scope"]["per_account_proof"] is False
    assert report["scope"]["nat_clients_share_cap"] is True
    assert all("ssh" not in " ".join(step["argv"]).lower() for step in report["steps"])
