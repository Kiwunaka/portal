from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "build_ru_origin_probe_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_ru_origin_probe_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _members() -> dict[str, bytes]:
    values: dict[str, bytes] = {}
    for path in MODULE.SOURCE_MEMBERS:
        if path == "scripts/internal_hmac_client.py":
            values[path] = b"from internal_request_auth import sign_internal_request\n"
        elif path.endswith(".py"):
            values[path] = b"VALUE = 1\n"
        elif path.endswith("pokrov-ru-probe.service") or path.endswith(
            "pokrov-ru-probe-uploader.service"
        ):
            values[path] = b"\n".join(
                [
                    b"[Service]",
                    b"User=pokrov-ru-probe",
                    b"Group=pokrov-ru-probe",
                    b"UMask=0077",
                    b"NoNewPrivileges=true",
                    b"ProtectSystem=strict",
                    b"ReadWritePaths=/var/lib/pokrov-ru-probe",
                    b"",
                ]
            )
        elif path.endswith("pokrov-ru-probe-uploader.timer"):
            values[path] = b"[Timer]\nOnUnitActiveSec=15m\nPersistent=true\nUMask=0077\n"
        else:
            values[path] = b"[Timer]\nOnCalendar=*-*-* 00,06,12,18:00:00\nPersistent=true\nUMask=0077\n"
    return values


def _bundle(tmp_path: Path) -> Path:
    members = _members()
    manifest = MODULE._manifest(
        source_revision=MODULE.EXPECTED_SOURCE_REVISION,
        source_epoch=1_788_000_000,
        members=members,
    )
    output = tmp_path / "ru-origin.zip"
    MODULE._write_bundle(output, manifest=manifest, members=members)
    return output


def test_synthetic_bundle_is_deterministic_and_verifies(tmp_path: Path) -> None:
    first = _bundle(tmp_path / "first")
    second = _bundle(tmp_path / "second")

    assert first.read_bytes() == second.read_bytes()
    manifest = MODULE.verify_bundle(first)
    assert manifest["source"]["revision"] == MODULE.EXPECTED_SOURCE_REVISION
    assert manifest["raw_runtime_material_included"] is False
    assert len(manifest["members"]) == 10


def test_bundle_contains_internal_request_auth_dependency(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    with ZipFile(bundle, "r") as archive:
        assert "portal_bot/internal_request_auth.py" in archive.namelist()


def test_tampered_member_fails_closed(tmp_path: Path) -> None:
    source = _bundle(tmp_path / "source")
    target = tmp_path / "tampered.zip"
    with ZipFile(source, "r") as archive, ZipFile(target, "w") as output:
        for info in archive.infolist():
            content = archive.read(info.filename)
            if info.filename == "scripts/ru_probe_runner.py":
                content += b"VALUE = 2\n"
            replacement = ZipInfo(info.filename, info.date_time)
            replacement.external_attr = info.external_attr
            replacement.create_system = info.create_system
            output.writestr(replacement, content, compress_type=ZIP_DEFLATED)
    with pytest.raises(MODULE.RuProbeBundleError, match="digest_or_mode"):
        MODULE.verify_bundle(target)


def test_wrong_source_revision_is_rejected() -> None:
    with pytest.raises(MODULE.RuProbeBundleError, match="not_candidate6"):
        MODULE._validate_source_revision("a" * 40)


def test_missing_runtime_dependency_is_rejected() -> None:
    members = _members()
    members["scripts/internal_hmac_client.py"] = b"VALUE = 1\n"
    with pytest.raises(MODULE.RuProbeBundleError, match="dependency_missing"):
        MODULE._manifest(
            source_revision=MODULE.EXPECTED_SOURCE_REVISION,
            source_epoch=1_788_000_000,
            members=members,
        )


def test_plan_never_claims_deploy_or_manual_run(tmp_path: Path) -> None:
    report = MODULE.plan_bundle(path=_bundle(tmp_path), operation="install")

    assert report["mode"] == "PLAN"
    assert report["deployment_performed"] is False
    assert report["runtime_material_required"] is True
    assert report["manual_run_upload_heartbeat_admin_readback_required"] is True
