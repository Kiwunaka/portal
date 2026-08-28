from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from remote_probe_owned_awg_udp_roundtrip import (  # noqa: E402
    PAYLOAD_SIZE,
    _echo_command,
    _finalize_report,
)


def test_echo_command_is_bounded_to_the_owned_port_and_fixed_payload() -> None:
    command = _echo_command(3478)

    assert "3478" in command
    assert str(PAYLOAD_SIZE) in command
    assert "s.sendto(payload,source)" in command
    assert "deadline=time.monotonic()+12" in command


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
