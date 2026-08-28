from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from remote_audit_owned_awg_alignment import (  # noqa: E402
    _normalize_enabled,
    _normalize_padding,
    _parse_config,
)


def test_live_showconf_parser_retains_runtime_variant_fields() -> None:
    parsed = _parse_config(
        b"[Interface]\nContentPaddingAddition = 64-512\nRandomTrailers = on\n"
    )

    assert parsed["Interface"]["ContentPaddingAddition"] == "64-512"
    assert parsed["Interface"]["RandomTrailers"] == "on"


def test_runtime_variant_normalization_handles_minimal_and_randomized_profiles() -> None:
    assert _normalize_padding(None) == "0"
    assert _normalize_padding("64-512") == "64-512"
    assert _normalize_enabled(None) is False
    assert _normalize_enabled("on") is True
    assert _normalize_enabled("true") is True
    assert _normalize_enabled("off") is False
