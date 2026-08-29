from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from remote_probe_owned_awg_udp_roundtrip import (  # noqa: E402
    PAYLOAD_SIZE,
    _echo_command,
    _finalize_report,
    _probe_local,
    _temporary_snat_rule,
    _temporary_policy_commands,
)


def test_echo_command_is_bounded_to_the_owned_port_and_fixed_payload() -> None:
    command = _echo_command(3478)

    assert "3478" in command
    assert str(PAYLOAD_SIZE) in command
    assert "s.sendto(payload,source)" in command
    assert "deadline=time.monotonic()+12" in command
    assert "print(count,matches)" in command


def test_ingress_source_echo_uses_bounded_pktinfo_without_printing_addresses() -> None:
    command = _echo_command(4500, "ingress")

    assert "IP_PKTINFO" in command
    assert "recvmsg(512,128)" in command
    assert "s.sendmsg([payload]" in command
    assert "print(count,matches)" in command


def test_temporary_snat_rule_is_bound_to_one_owned_lab_port() -> None:
    command = _temporary_snat_rule("pokrovawg2", 4500, "192.0.2.10", "-I")

    assert "-I POSTROUTING 1" in command
    assert "--sport 4500" in command
    assert "roundtrip temporary reply source" in command
    assert "--to-source 192.0.2.10" in command


def test_temporary_policy_route_is_bound_to_one_owned_lab_port() -> None:
    preflight, apply, cleanup = _temporary_policy_commands(4500, "192.0.2.10")

    assert "14500:" in preflight
    assert "table 24500" in preflight
    assert "sport 4500 lookup 24500" in apply
    assert "src 192.0.2.10" in apply
    assert "priority 14500" in cleanup
    assert "table 24500" in cleanup


def test_roundtrip_requires_the_reverse_echo_and_service_restore() -> None:
    report = {
        "server_received_all": True,
        "phone_received_valid_echo": False,
        "service_restored": True,
    }

    assert _finalize_report(report) is False
    assert report == {
        "server_received_all": True,
        "phone_received_valid_echo": False,
        "service_restored": True,
        "roundtrip_pass": False,
        "execution_safe": True,
        "ok": False,
    }


def test_roundtrip_passes_only_when_both_directions_and_restore_pass() -> None:
    report = {
        "server_received_all": True,
        "phone_received_valid_echo": True,
        "service_restored": True,
    }

    assert _finalize_report(report) is True
    assert report["roundtrip_pass"] is True
    assert report["ok"] is True


def test_roundtrip_uses_source_neutral_echo_result() -> None:
    report = {
        "server_received_all": True,
        "source_received_valid_echo": True,
        "service_restored": True,
    }

    assert _finalize_report(report) is True


def test_local_probe_requires_all_exact_echoes(monkeypatch) -> None:
    class FakeSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def settimeout(self, _seconds):
            return None

        def sendto(self, payload, target):
            assert payload == b"P" * PAYLOAD_SIZE
            assert target == ("198.51.100.10", 3478)

        def recvfrom(self, _size):
            return b"P" * PAYLOAD_SIZE, ("198.51.100.10", 3478)

    monkeypatch.setattr(
        "remote_probe_owned_awg_udp_roundtrip.socket.socket",
        lambda *_args, **_kwargs: FakeSocket(),
    )
    monkeypatch.setattr(
        "remote_probe_owned_awg_udp_roundtrip.time.sleep", lambda _seconds: None
    )

    assert _probe_local("198.51.100.10", 3478) is True
