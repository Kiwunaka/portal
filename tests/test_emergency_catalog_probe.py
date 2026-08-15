from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

from portal_bot.emergency_catalog_probe import EmergencyProbeError, run_controlled_probe
from portal_bot.emergency_catalog_source import parse_emergency_source


EXPECTED = hashlib.sha256(b"pokrov-emergency-probe-v1").hexdigest()
PROBE_URL = "https://connect.pokrov.space/api/emergency-probe/payload-v1"


def _material():
    result = parse_emergency_source(
        "vless://11111111-1111-4111-8111-111111111111@reserve.example.com:443"
        "?type=tcp&security=reality&pbk=BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"
        "&sid=a1b2&sni=cover.example.com&fp=chrome&flow=xtls-rprx-vision"
    )
    return result.accepted[0]


def _write_adapter(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")


@pytest.mark.asyncio
async def test_owned_adapter_contract_returns_safe_probe_result(tmp_path) -> None:
    script = tmp_path / "adapter.py"
    _write_adapter(
        script,
        """import json, sys
request = json.load(sys.stdin)
json.dump({
  'schema_version': request['schema_version'],
  'stable_id': request['stable_id'],
  'authenticated': True,
  'payload_ok': True,
  'payload_sha256': request['expected_payload_sha256'],
  'exit_country': 'FR',
  'latency_ms': 42,
  'verified_at': '2026-08-15T12:00:00Z',
  'verification_source': 'exact_core',
  'error_code': ''
}, sys.stdout)
""",
    )

    result = await run_controlled_probe(
        _material(),
        adapter_command=(sys.executable, str(script)),
        probe_url=PROBE_URL,
        expected_payload_sha256=EXPECTED,
    )

    assert result.authenticated is True
    assert result.payload_ok is True
    assert result.exit_country == "FR"
    assert result.verification_source == "exact_core"


@pytest.mark.asyncio
async def test_adapter_cannot_echo_raw_material_or_unknown_fields(tmp_path) -> None:
    script = tmp_path / "adapter.py"
    _write_adapter(
        script,
        """import json, sys
request = json.load(sys.stdin)
json.dump({
  'schema_version': request['schema_version'],
  'stable_id': request['stable_id'],
  'authenticated': True,
  'payload_ok': True,
  'payload_sha256': request['expected_payload_sha256'],
  'exit_country': 'FR',
  'latency_ms': 1,
  'verified_at': '2026-08-15T12:00:00Z',
  'raw': request['outbound']
}, sys.stdout)
""",
    )

    with pytest.raises(EmergencyProbeError, match="probe_adapter_output_invalid") as error:
        await run_controlled_probe(
            _material(),
            adapter_command=(sys.executable, str(script)),
            probe_url=PROBE_URL,
            expected_payload_sha256=EXPECTED,
        )

    assert "reserve.example.com" not in repr(error.value)


@pytest.mark.asyncio
async def test_adapter_timeout_is_bounded_and_probe_url_is_allowlisted(tmp_path) -> None:
    script = tmp_path / "adapter.py"
    _write_adapter(script, "import time\ntime.sleep(2)\n")

    with pytest.raises(EmergencyProbeError, match="probe_adapter_timeout"):
        await run_controlled_probe(
            _material(),
            adapter_command=(sys.executable, str(script)),
            probe_url=PROBE_URL,
            expected_payload_sha256=EXPECTED,
            timeout_seconds=0.1,
        )
    with pytest.raises(EmergencyProbeError, match="probe_url_not_allowed"):
        await run_controlled_probe(
            _material(),
            adapter_command=(sys.executable, str(script)),
            probe_url="https://example.com/api/emergency-probe/payload-v1",
            expected_payload_sha256=EXPECTED,
        )
