from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "remote_ensure_owned_awg_firewall.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "remote_ensure_owned_awg_firewall",
    SCRIPT_PATH,
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class _Channel:
    def recv_exit_status(self) -> int:
        return 0


class _Reader:
    def __init__(self, value: str = "") -> None:
        self._value = value.encode()
        self.channel = _Channel()

    def read(self) -> bytes:
        return self._value


class _FakeClient:
    def __init__(self, status: str) -> None:
        self.status = status
        self.commands: list[str] = []

    def exec_command(self, command: str, timeout: int):
        self.commands.append(command)
        output = self.status if command == "ufw status" else ""
        return None, _Reader(output), _Reader()


def test_audit_distinguishes_missing_and_allowed_owned_udp_ports() -> None:
    client = _FakeClient(
        "Status: active\n"
        "3478/udp                  ALLOW       Anywhere\n"
        "3478/udp (v6)             ALLOW       Anywhere (v6)\n"
    )

    result = MODULE._audit(client)

    assert result["ufw_active"] is True
    assert result["all_owned_awg_udp_allowed"] is False
    assert result["ports"]["awg2_lab"] == {
        "port": 4500,
        "allow_present": False,
        "deny_present": False,
        "matching_rule_count": 0,
    }
    assert result["ports"]["awg31_lab"]["allow_present"] is True


def test_apply_adds_only_the_two_owned_udp_rules() -> None:
    client = _FakeClient("Status: active\n")

    MODULE._apply(client)

    assert client.commands == [
        "ufw status",
        "ufw allow 4500/udp comment 'POKROV owned awg2_lab'",
        "ufw allow 3478/udp comment 'POKROV owned awg31_lab'",
    ]


def test_apply_fails_closed_when_ufw_is_inactive() -> None:
    client = _FakeClient("Status: inactive\n")

    with pytest.raises(MODULE.FirewallError, match="UFW is not active"):
        MODULE._apply(client)

    assert client.commands == ["ufw status"]
