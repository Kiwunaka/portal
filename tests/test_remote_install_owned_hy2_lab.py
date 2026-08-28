from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT_PATH = SCRIPTS / "remote_install_owned_hy2_lab.py"
SPEC = importlib.util.spec_from_file_location("remote_install_owned_hy2_lab", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BUNDLE = MODULE.bundle_contract


def _synthetic_bundle(tmp_path: Path) -> Path:
    contents = {member: path.read_bytes() for member, path in BUNDLE.STATIC_MEMBERS.items()}
    contents.update(
        {
            "LICENSES/sing-box-GPL-3.0-or-later.txt": b"GPL synthetic fixture\n",
            "THIRD_PARTY_NOTICES.md": b"Synthetic third-party notice\n",
            BUNDLE.BINARY_MEMBER: b"\x7fELF" + b"0" * 10_000_000,
        }
    )
    source = BUNDLE._validate_source_contract(contents)
    provenance = {
        "repository": "Kiwunaka/pokrov-core",
        "revision": BUNDLE.EXPECTED_CORE_REVISION,
        "source_epoch": 1,
        "source_time_utc": "1970-01-01T00:00:01Z",
        "go_toolchain": BUNDLE.EXPECTED_GO_VERSION,
        "sing_box_source_version": BUNDLE.SOURCE_ENGINE_VERSION,
        "contract_id": BUNDLE.EXPECTED_CONTRACT_ID,
        "contract_sha256": BUNDLE.EXPECTED_CONTRACT_SHA256,
    }
    manifest = BUNDLE._manifest(
        provenance=provenance, contract=source["contract"], contents=contents
    )
    destination = tmp_path / "hy2.zip"
    with zipfile.ZipFile(destination, "w") as archive:
        archive.writestr(BUNDLE._zip_info(BUNDLE.MANIFEST_NAME), BUNDLE._canonical_json(manifest))
        for member in BUNDLE.EXPECTED_MEMBERS:
            if member != BUNDLE.MANIFEST_NAME:
                archive.writestr(BUNDLE._zip_info(member), contents[member])
    return destination


def test_local_bundle_is_exact_and_derives_receipt_bound_paths(tmp_path: Path) -> None:
    path, manifest, contents, digest = MODULE._validated_local_bundle(
        _synthetic_bundle(tmp_path)
    )

    assert path.is_file()
    assert MODULE.SAFE_SHA256_RE.fullmatch(digest)
    assert manifest["source"]["revision"] == BUNDLE.EXPECTED_CORE_REVISION
    assert BUNDLE.BINARY_MEMBER in contents
    assert f"{MODULE.RELEASE_ROOT}/{digest}".endswith(digest)
    assert f"{MODULE.RUNTIME_STAGE_ROOT}/{digest}".endswith(digest)


def test_plan_probe_is_read_only_and_never_returns_runtime_material() -> None:
    command = MODULE._preflight_command(
        release_dir=f"{MODULE.RELEASE_ROOT}/{'a' * 64}",
        runtime_material_dir=f"{MODULE.RUNTIME_STAGE_ROOT}/{'a' * 64}",
    )

    prohibited = ("mkdir", "install -", "systemctl start", "systemctl enable", "ufw allow", "rm -")
    assert not any(token in command for token in prohibited)
    assert "ss -H -lun" in command
    assert "runtime_placeholders_absent" in command
    assert "runtime_contract_valid" in command
    assert "python3" in command
    assert "cat " not in command


def test_apply_commands_are_digest_bound_secret_safe_and_rollback_armed(
    tmp_path: Path,
) -> None:
    _path, manifest, _contents, digest = MODULE._validated_local_bundle(
        _synthetic_bundle(tmp_path)
    )
    receipt_id = "20260828T120000Z-7-" + digest[:12]
    backup = f"{MODULE.BACKUP_ROOT}/{receipt_id}"
    stage = f"{MODULE.STAGE_ROOT}/{receipt_id}"
    release = f"{MODULE.RELEASE_ROOT}/{digest}"
    runtime = f"{MODULE.RUNTIME_STAGE_ROOT}/{digest}"

    install = MODULE._install_command(
        stage_dir=stage,
        release_dir=release,
        runtime_material_dir=runtime,
        backup_dir=backup,
        manifest=manifest,
    )
    rollback = MODULE._rollback_command(
        backup_dir=backup,
        bundle_sha256=digest,
        node_code="de",
        release_dir=release,
        require_current_release=True,
    )

    assert "systemctl start pokrov-hy2-lab.service" in install
    assert install.index("systemctl start") < install.index("systemctl enable")
    assert "runuser -u pokrov-hy2" in install
    assert "ufw allow 443/udp" in install
    assert "${POKROV_" not in install
    assert "password" not in install.lower()
    assert "disable --now pokrov-hy2-lab.service" in rollback
    assert "ufw --force delete allow 443/udp" in rollback
    assert rollback.index("listener_after_stop=free") < rollback.index("rm -f")
    assert rollback.rindex("listener_after_stop") > rollback.index("rm -f")
    assert digest in rollback
    assert "readlink -f /opt/pokrov/hy2/current" in rollback
    assert "rm -rf" not in rollback
    assert f"test -d {release}" in rollback


def test_fresh_install_rejects_port_path_firewall_or_material_conflicts() -> None:
    ready = {
        "root": True,
        "required_tools": True,
        "ufw_installed": True,
        "ufw_active": True,
        "ufw_rule_present": False,
        "udp_443": "free",
        "occupied_targets": [],
        "service_state": "inactive",
        "runtime_material_ready": True,
    }
    MODULE._assert_fresh_install_preflight(ready)

    cases = (
        {"udp_443": "busy"},
        {"occupied_targets": ["unit"]},
        {"ufw_rule_present": True},
        {"runtime_material_ready": False},
        {"ufw_active": False},
    )
    for override in cases:
        with pytest.raises(MODULE.Hy2RemoteOperationError):
            MODULE._assert_fresh_install_preflight({**ready, **override})


def test_probe_parser_rejects_unbounded_remote_output() -> None:
    assert MODULE._parse_probe("root=yes\nudp_busy=no") == {
        "root": "yes",
        "udp_busy": "no",
    }
    with pytest.raises(MODULE.Hy2RemoteOperationError):
        MODULE._parse_probe("host=198.51.100.1/path")


class _Channel:
    def __init__(self, code: int = 0) -> None:
        self._code = code

    def recv_exit_status(self) -> int:
        return self._code

    def shutdown_write(self) -> None:
        return None


class _Stream:
    def __init__(self, value: str = "", code: int = 0) -> None:
        self._value = value.encode()
        self.channel = _Channel(code)

    def read(self) -> bytes:
        return self._value

    def write(self, _value: str) -> None:
        return None


class _Brain:
    def __init__(self, value: str) -> None:
        self.value = value

    def exec_command(self, _command: str, timeout: int = 60):
        del timeout
        return _Stream(), _Stream(self.value), _Stream()


@pytest.mark.parametrize(
    ("raw", "expected"),
    (("true\n", "engaged"), ("false\n", "disengaged"), ("\n", "unavailable")),
)
def test_brain_kill_switch_readback_keeps_old_brain_plan_safe(
    raw: str, expected: str
) -> None:
    assert MODULE._brain_hy2_kill_switch(_Brain(raw)) == expected


def test_report_contract_contains_no_endpoint_or_runtime_secret_fields(tmp_path: Path) -> None:
    bundle_path = _synthetic_bundle(tmp_path)
    _path, manifest, _contents, digest = MODULE._validated_local_bundle(bundle_path)
    report = {
        "schema_version": MODULE.REPORT_SCHEMA,
        "mode": "PLAN",
        "operation": "install",
        "node_code": "de",
        "bundle_sha256": digest,
        "source_revision": manifest["source"]["revision"],
        "raw_host_returned": False,
        "raw_runtime_material_returned": False,
    }
    serialized = json.dumps(report, sort_keys=True)

    assert "endpoint" not in serialized
    assert "private_key" not in serialized
    assert "password" not in serialized
    assert "hysteria2://" not in serialized
