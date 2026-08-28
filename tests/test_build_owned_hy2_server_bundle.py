from __future__ import annotations

import importlib.util
import json
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "build_owned_hy2_server_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_owned_hy2_server_bundle", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _synthetic_bundle(tmp_path: Path) -> Path:
    contents = {
        member: path.read_bytes() for member, path in MODULE.STATIC_MEMBERS.items()
    }
    contents.update(
        {
            "LICENSES/sing-box-GPL-3.0-or-later.txt": b"GPL synthetic fixture\n",
            "THIRD_PARTY_NOTICES.md": b"Synthetic third-party notice\n",
            MODULE.BINARY_MEMBER: b"\x7fELF" + b"0" * 10_000_000,
        }
    )
    source = MODULE._validate_source_contract(contents)
    provenance = {
        "repository": "Kiwunaka/pokrov-core",
        "revision": MODULE.EXPECTED_CORE_REVISION,
        "source_epoch": 1,
        "source_time_utc": "1970-01-01T00:00:01Z",
        "go_toolchain": MODULE.EXPECTED_GO_VERSION,
        "sing_box_source_version": MODULE.SOURCE_ENGINE_VERSION,
        "contract_id": MODULE.EXPECTED_CONTRACT_ID,
        "contract_sha256": MODULE.EXPECTED_CONTRACT_SHA256,
    }
    manifest = MODULE._manifest(
        provenance=provenance,
        contract=source["contract"],
        contents=contents,
    )
    bundle = tmp_path / "hy2.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr(MODULE._zip_info(MODULE.MANIFEST_NAME), MODULE._canonical_json(manifest))
        for member in MODULE.EXPECTED_MEMBERS:
            if member != MODULE.MANIFEST_NAME:
                archive.writestr(MODULE._zip_info(member), contents[member])
    return bundle


def test_source_contract_is_single_port_tls13_salamander_and_secret_free() -> None:
    contents = {member: path.read_bytes() for member, path in MODULE.STATIC_MEMBERS.items()}
    source = MODULE._validate_source_contract(contents)
    template = source["template"]
    inbound = template["inbounds"][0]
    serialized = json.dumps(template, sort_keys=True)

    assert inbound["type"] == "hysteria2"
    assert inbound["listen_port"] == 443
    assert inbound["tls"]["enabled"] is True
    assert inbound["tls"]["min_version"] == "1.3"
    assert inbound["tls"]["alpn"] == ["h3"]
    assert inbound["obfs"]["type"] == "salamander"
    assert "server_ports" not in serialized
    assert "hop_interval" not in serialized
    assert "hysteria2://" not in serialized
    assert "hy2://" not in serialized
    assert "Environment=" not in contents["systemd/pokrov-hy2-lab.service"].decode()


def test_verify_and_plan_are_read_only_and_return_no_runtime_material(tmp_path: Path) -> None:
    bundle = _synthetic_bundle(tmp_path)

    verified = MODULE.verify_bundle(bundle)
    install = MODULE.plan_bundle(bundle=bundle, operation="install", node_code="de")
    rollback = MODULE.plan_bundle(bundle=bundle, operation="rollback", node_code="de")

    assert verified["ok"] is True
    assert verified["deployment_performed"] is False
    assert install["mutation_performed"] is False
    assert rollback["mutation_performed"] is False
    assert install["listen_port"] == 443
    assert rollback["operation"] == "rollback"
    assert install["raw_runtime_material_returned"] is False
    assert rollback["raw_runtime_material_returned"] is False


def test_verify_rejects_tampered_binary(tmp_path: Path) -> None:
    bundle = _synthetic_bundle(tmp_path)
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(bundle, "r") as source, zipfile.ZipFile(tampered, "w") as target:
        for info in source.infolist():
            value = source.read(info.filename)
            if info.filename == MODULE.BINARY_MEMBER:
                value += b"tamper"
            target.writestr(info, value)

    with pytest.raises(MODULE.Hy2ServerBundleError, match="bundle_file_digest_mismatch"):
        MODULE.verify_bundle(tampered)


def test_plan_rejects_unbounded_node_code(tmp_path: Path) -> None:
    bundle = _synthetic_bundle(tmp_path)

    with pytest.raises(MODULE.Hy2ServerBundleError, match="node_code_invalid"):
        MODULE.plan_bundle(bundle=bundle, operation="install", node_code="../de")
