from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.verify_awg31_contract_sync import verify_awg31_contract_sync


CONTRACT_ID = "pokrov.awg31.endpoint.v1"


def _write_fixture_roots(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    platform_root = tmp_path / "platform"
    core_root = tmp_path / "core"
    client_root = tmp_path / "client"
    contract_path = core_root / "config" / "awg31-capability.json"
    platform_path = platform_root / "portal_bot" / "awg31_lab_service.py"
    client_path = client_root / "packages" / "runtime_engine" / "lib" / "runtime_engine.dart"
    contract_path.parent.mkdir(parents=True)
    platform_path.parent.mkdir(parents=True)
    client_path.parent.mkdir(parents=True)

    contract_bytes = (
        json.dumps({"contract_id": CONTRACT_ID}, separators=(",", ":")) + "\n"
    ).encode()
    contract_path.write_bytes(contract_bytes)
    digest = hashlib.sha256(contract_bytes).hexdigest()
    platform_path.write_text(
        f'AWG31_CONTRACT_ID = "{CONTRACT_ID}"\n'
        f'AWG31_CONTRACT_SHA256 = (\n    "{digest}"\n)\n',
        encoding="utf-8",
    )
    client_path.write_text(
        f"const _pokrovAwg31ContractId = '{CONTRACT_ID}';\n"
        f"const _pokrovAwg31ContractSha256 =\n    '{digest}';\n",
        encoding="utf-8",
    )
    return platform_root, core_root, client_root, digest


def test_verifies_exact_contract_identity_and_digest(tmp_path: Path) -> None:
    platform_root, core_root, client_root, digest = _write_fixture_roots(tmp_path)

    result = verify_awg31_contract_sync(
        platform_root=platform_root,
        core_root=core_root,
        client_root=client_root,
    )

    assert result["status"] == "PASS"
    assert result["contract_id"] == CONTRACT_ID
    assert result["contract_sha256"] == digest
    assert result["candidate_proven"] is False


def test_rejects_a_stale_consumer_digest(tmp_path: Path) -> None:
    platform_root, core_root, client_root, _digest = _write_fixture_roots(tmp_path)
    platform_path = platform_root / "portal_bot" / "awg31_lab_service.py"
    platform_path.write_text(
        f'AWG31_CONTRACT_ID = "{CONTRACT_ID}"\n'
        f'AWG31_CONTRACT_SHA256 = (\n    "{"0" * 64}"\n)\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="contract drift in platform"):
        verify_awg31_contract_sync(
            platform_root=platform_root,
            core_root=core_root,
            client_root=client_root,
        )
