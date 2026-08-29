#!/usr/bin/env python3
"""Build and verify the immutable POKROV owned Smart DNS server bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "infra" / "owned-smart-dns"
MODULE_ROOT = SOURCE_ROOT
POLICY_PATH = REPO_ROOT / "shared" / "contracts" / "network" / "smart-dns-policy.v1.json"
BUNDLE_SCHEMA = "pokrov-owned-smart-dns-server-bundle-v1"
MANIFEST_NAME = "owned-smart-dns-server-bundle.json"
EXPECTED_GO_VERSION = "go1.25.13"
BINARY_MEMBER = "bin/pokrov-smart-dns"
STATIC_MEMBERS = {
    "contract/bundle-contract.json": SOURCE_ROOT / "bundle-contract.json",
    "config/config.template.json": SOURCE_ROOT / "config.template.json",
    "config/config.fronted.template.json": SOURCE_ROOT / "config.fronted.template.json",
    "systemd/pokrov-smart-dns-lab.service": SOURCE_ROOT / "pokrov-smart-dns-lab.service",
    "share/smart-dns-policy.v1.json": POLICY_PATH,
    "LICENSES/miekg-dns-BSD-3-Clause.txt": SOURCE_ROOT / "LICENSES" / "miekg-dns-BSD-3-Clause.txt",
    "LICENSES/Go-and-golang-x-BSD-3-Clause.txt": SOURCE_ROOT / "LICENSES" / "Go-and-golang-x-BSD-3-Clause.txt",
    "THIRD_PARTY_NOTICES.md": SOURCE_ROOT / "THIRD_PARTY_NOTICES.md",
    "README.md": SOURCE_ROOT / "README.md",
}
EXPECTED_MEMBERS = frozenset({MANIFEST_NAME, BINARY_MEMBER, *STATIC_MEMBERS})


class SmartDNSBundleError(RuntimeError):
    pass


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_text_member(path: Path) -> bytes:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise SmartDNSBundleError("bundle_text_member_utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SmartDNSBundleError("bundle_text_member_not_utf8") from exc
    normalized = text.replace("\r\n", "\n")
    if "\r" in normalized:
        raise SmartDNSBundleError("bundle_text_member_lone_cr_forbidden")
    return normalized.encode("utf-8")


def _run(command: list[str], *, cwd: Path, env: Mapping[str, str] | None = None) -> str:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        env=dict(env) if env is not None else None,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "command_failed").strip()
        raise SmartDNSBundleError(f"command_failed:{detail[:800]}")
    return result.stdout.strip()


def _go_executable(value: str | Path) -> Path:
    path = Path(value).resolve()
    if not path.is_file():
        raise SmartDNSBundleError("go_executable_invalid")
    return path


def _provenance(go_executable: Path) -> dict[str, Any]:
    revision = _run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).lower()
    status = _run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=REPO_ROOT)
    if status:
        raise SmartDNSBundleError("platform_tree_not_clean")
    go_version = _run([str(go_executable), "env", "GOVERSION"], cwd=MODULE_ROOT)
    if go_version != EXPECTED_GO_VERSION:
        raise SmartDNSBundleError("go_toolchain_mismatch")
    source_epoch = int(_run(["git", "show", "-s", "--format=%ct", revision], cwd=REPO_ROOT))
    dependencies = _run(
        [str(go_executable), "list", "-mod=readonly", "-m", "-f", "{{.Path}} {{.Version}}", "all"],
        cwd=MODULE_ROOT,
        env=_build_environment(),
    ).splitlines()
    return {
        "repository": "Kiwunaka/portal",
        "revision": revision,
        "source_epoch": source_epoch,
        "source_time_utc": datetime.fromtimestamp(source_epoch, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "go_toolchain": go_version,
        "module_dependencies": dependencies,
    }


def _build_environment() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "CGO_ENABLED": "0",
            "GOOS": "linux",
            "GOARCH": "amd64",
            "GOFLAGS": "-mod=readonly",
        }
    )
    return env


def _module_environment() -> dict[str, str]:
    env = dict(os.environ)
    env["GOFLAGS"] = "-mod=readonly"
    return env


def _build_command(go_executable: Path, output: Path) -> list[str]:
    return [
        str(go_executable),
        "build",
        "-trimpath",
        "-buildvcs=false",
        "-ldflags",
        "-s -w -buildid=",
        "-o",
        str(output),
        "./cmd/pokrov-smart-dns",
    ]


def _build_binary_twice(go_executable: Path) -> bytes:
    env = _build_environment()
    host_env = _module_environment()
    _run([str(go_executable), "test", "./..."], cwd=MODULE_ROOT, env=host_env)
    _run([str(go_executable), "vet", "./..."], cwd=MODULE_ROOT, env=host_env)
    with tempfile.TemporaryDirectory(prefix="pokrov-smart-dns-build-") as raw_temp:
        temp = Path(raw_temp)
        first = temp / "first" / "pokrov-smart-dns"
        second = temp / "second" / "pokrov-smart-dns"
        first.parent.mkdir()
        second.parent.mkdir()
        _run(_build_command(go_executable, first), cwd=MODULE_ROOT, env=env)
        _run(_build_command(go_executable, second), cwd=MODULE_ROOT, env=env)
        first_bytes = first.read_bytes()
        if first_bytes != second.read_bytes():
            raise SmartDNSBundleError("linux_binary_not_reproducible")
        if len(first_bytes) < 1_000_000 or not first_bytes.startswith(b"\x7fELF"):
            raise SmartDNSBundleError("linux_binary_shape_invalid")
        return first_bytes


def _zip_timestamp(source_epoch: int) -> tuple[int, int, int, int, int, int]:
    moment = datetime.fromtimestamp(max(source_epoch, 315532800), tz=timezone.utc)
    return (moment.year, moment.month, moment.day, moment.hour, moment.minute, moment.second // 2 * 2)


def _manifest(*, binary: bytes, provenance: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, bytes]]:
    members = {name: _canonical_text_member(path) for name, path in STATIC_MEMBERS.items()}
    members[BINARY_MEMBER] = binary
    contract = json.loads(members["contract/bundle-contract.json"])
    policy_digest = _sha256(members["share/smart-dns-policy.v1.json"])
    if (
        contract.get("schema_version") != BUNDLE_SCHEMA
        or contract.get("state") != "source_only_default_off"
        or contract.get("source_text_normalization") != "utf8_crlf_to_lf"
        or contract.get("policy_sha256") != policy_digest
        or (contract.get("runtime") or {}).get("recursive_dns") is not False
        or (contract.get("runtime") or {}).get("enabled_by_default") is not False
    ):
        raise SmartDNSBundleError("bundle_contract_invalid")
    manifest = {
        "schema_version": BUNDLE_SCHEMA,
        "state": "source_only_default_off",
        "created_from": dict(provenance),
        "target": {"goos": "linux", "goarch": "amd64", "cgo_enabled": False},
        "policy_sha256": policy_digest,
        "members": {
            name: {"sha256": _sha256(content), "size": len(content)}
            for name, content in sorted(members.items())
        },
        "evidence_ceiling": "immutable_local_server_bundle_only_until_authorized_listener_deploy_and_live_matrix",
    }
    return manifest, members


def _write_bundle(output: Path, manifest: Mapping[str, Any], members: Mapping[str, bytes]) -> None:
    output = output.resolve()
    try:
        output.relative_to(REPO_ROOT)
    except ValueError:
        pass
    else:
        raise SmartDNSBundleError("bundle_output_must_be_outside_repository")
    output.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _zip_timestamp(int((manifest.get("created_from") or {}).get("source_epoch") or 0))
    payload = {MANIFEST_NAME: _canonical_json(manifest), **members}
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo(name, date_time=timestamp)
            mode = 0o755 if name == BINARY_MEMBER else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            archive.writestr(info, payload[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def verify_bundle(path: Path) -> dict[str, Any]:
    path = path.resolve()
    if not path.is_file():
        raise SmartDNSBundleError("bundle_missing")
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != EXPECTED_MEMBERS:
            raise SmartDNSBundleError("bundle_members_invalid")
        if any(info.file_size > 64 * 1024 * 1024 for info in archive.infolist()):
            raise SmartDNSBundleError("bundle_member_too_large")
        payload = {name: archive.read(name) for name in names}
    try:
        manifest = json.loads(payload[MANIFEST_NAME])
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmartDNSBundleError("bundle_manifest_invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != BUNDLE_SCHEMA:
        raise SmartDNSBundleError("bundle_schema_invalid")
    declared = manifest.get("members")
    if not isinstance(declared, dict) or set(declared) != EXPECTED_MEMBERS - {MANIFEST_NAME}:
        raise SmartDNSBundleError("bundle_manifest_members_invalid")
    for name, expected in declared.items():
        if not isinstance(expected, dict):
            raise SmartDNSBundleError("bundle_member_descriptor_invalid")
        content = payload[name]
        if expected.get("sha256") != _sha256(content) or expected.get("size") != len(content):
            raise SmartDNSBundleError("bundle_member_digest_mismatch")
    if not payload[BINARY_MEMBER].startswith(b"\x7fELF") or len(payload[BINARY_MEMBER]) < 1_000_000:
        raise SmartDNSBundleError("bundle_binary_invalid")
    if manifest.get("policy_sha256") != _sha256(payload["share/smart-dns-policy.v1.json"]):
        raise SmartDNSBundleError("bundle_policy_digest_mismatch")
    contract = json.loads(payload["contract/bundle-contract.json"])
    if contract.get("policy_sha256") != manifest.get("policy_sha256"):
        raise SmartDNSBundleError("bundle_contract_policy_mismatch")
    return manifest


def build_bundle(*, go_executable: Path, output: Path) -> dict[str, Any]:
    provenance = _provenance(go_executable)
    binary = _build_binary_twice(go_executable)
    manifest, members = _manifest(binary=binary, provenance=provenance)
    _write_bundle(output, manifest, members)
    verified = verify_bundle(output)
    if verified != manifest:
        raise SmartDNSBundleError("bundle_readback_mismatch")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--go-executable", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--bundle", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "build":
        manifest = build_bundle(go_executable=_go_executable(args.go_executable), output=args.output)
        bundle = args.output.resolve()
    else:
        manifest = verify_bundle(args.bundle)
        bundle = args.bundle.resolve()
    print(
        json.dumps(
            {
                "status": "PASS_LOCAL_IMMUTABLE_BUNDLE",
                "bundle_sha256": _sha256(bundle.read_bytes()),
                "source_revision": (manifest.get("created_from") or {}).get("revision"),
                "policy_sha256": manifest.get("policy_sha256"),
                "evidence_ceiling": manifest.get("evidence_ceiling"),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
