from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from remote_count_owned_awg_packets import _emit_result, _outer_size_classifier  # noqa: E402


def test_awg2_keeps_fixed_size_classification() -> None:
    classifier = _outer_size_classifier("awg2_lab")

    assert classifier["mode"] == "fixed_sizes_v1"
    assert classifier["applicable"] is True
    assert "$NF == 148" in classifier["awk"]
    assert "$NF == 92" in classifier["awk"]


def test_randomized_awg31_uses_direction_counts_without_false_fixed_sizes() -> None:
    classifier = _outer_size_classifier("awg31_lab")

    assert classifier == {
        "mode": "not_applicable_randomized_trailers",
        "applicable": False,
        "awk": "",
    }


def test_unknown_profile_fails_closed() -> None:
    with pytest.raises(ValueError, match="unknown owned AWG profile"):
        _outer_size_classifier("unknown")


def test_secret_free_packet_result_can_be_retained_without_shell_redirect(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "nested" / "packet-count.json"
    result = {
        "schema_version": "pokrov-owned-awg-packet-count-v1",
        "profile": "awg2_lab",
        "raw_addresses_returned": False,
    }

    _emit_result(result, str(output))

    assert output.read_text(encoding="utf-8").endswith("\n")
    assert '"raw_addresses_returned": false' in output.read_text(encoding="utf-8")
    assert capsys.readouterr().out.strip() == output.read_text(encoding="utf-8").strip()
