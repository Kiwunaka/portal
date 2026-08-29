from __future__ import annotations

import importlib.util
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_owned_smart_dns_server_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_owned_smart_dns_server_bundle", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _synthetic_bundle(tmp_path: Path) -> Path:
    binary = b"\x7fELF" + (b"safe-test-byte" * 80_000)
    provenance = {
        "repository": "Kiwunaka/portal",
        "revision": "a" * 40,
        "source_epoch": 1_787_000_000,
        "source_time_utc": "2026-08-17T00:00:00Z",
        "go_toolchain": MODULE.EXPECTED_GO_VERSION,
        "module_dependencies": [],
    }
    manifest, members = MODULE._manifest(binary=binary, provenance=provenance)
    output = tmp_path / "smart-dns.zip"
    MODULE._write_bundle(output, manifest, members)
    return output


def test_synthetic_bundle_verifies_and_is_deterministic(tmp_path: Path) -> None:
    first = _synthetic_bundle(tmp_path / "first")
    second = _synthetic_bundle(tmp_path / "second")
    assert first.read_bytes() == second.read_bytes()
    manifest = MODULE.verify_bundle(first)
    assert manifest["state"] == "source_only_default_off"
    assert manifest["evidence_ceiling"].startswith("immutable_local")


def test_tampered_member_fails_closed(tmp_path: Path) -> None:
    source = _synthetic_bundle(tmp_path / "source")
    target = tmp_path / "tampered.zip"
    with ZipFile(source, "r") as archive, ZipFile(target, "w") as output:
        for info in archive.infolist():
            content = archive.read(info.filename)
            if info.filename == "share/smart-dns-policy.v1.json":
                content += b" "
            replacement = ZipInfo(info.filename, info.date_time)
            replacement.external_attr = info.external_attr
            replacement.create_system = info.create_system
            output.writestr(replacement, content, compress_type=ZIP_DEFLATED)
    with pytest.raises(MODULE.SmartDNSBundleError, match="digest_mismatch"):
        MODULE.verify_bundle(target)


def test_text_members_canonicalize_windows_crlf(tmp_path: Path) -> None:
    source = tmp_path / "member.json"
    source.write_bytes(b'{\r\n  "state": "safe"\r\n}\r\n')

    assert MODULE._canonical_text_member(source) == b'{\n  "state": "safe"\n}\n'


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        (b"unsafe\rlone-cr\n", "lone_cr"),
        (b"\xef\xbb\xbf{}\n", "utf8_bom"),
        (b"\xff\xfe", "not_utf8"),
    ],
)
def test_text_members_reject_noncanonical_bytes(
    tmp_path: Path,
    payload: bytes,
    error: str,
) -> None:
    source = tmp_path / "member.txt"
    source.write_bytes(payload)

    with pytest.raises(MODULE.SmartDNSBundleError, match=error):
        MODULE._canonical_text_member(source)
