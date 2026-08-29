#!/usr/bin/env python3
"""Build, verify and plan the immutable POKROV-owned HY2 server bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPO_ROOT / "infra" / "owned-hy2"
BUNDLE_SCHEMA = "pokrov-owned-hy2-server-bundle-v1"
MANIFEST_NAME = "owned-hy2-server-bundle.json"
EXPECTED_CORE_REVISION = "a45d69e40ed7d892619a2b5c4592a527f630665e"
EXPECTED_CONTRACT_ID = "pokrov.hy2.outbound.v1"
EXPECTED_CONTRACT_SHA256 = "c96b38e58ea33f838f23b80a65f3a9a264e932b7248f206798df9a0b8fa0fb98"
EXPECTED_GO_VERSION = "go1.25.13"
SOURCE_ENGINE_VERSION = "1.13.0"
BINARY_VERSION = "1.13.0-pokrov-hy2-lab.2"
BUILD_TAGS = ("with_quic",)
BINARY_MEMBER = "bin/pokrov-sing-box-hy2"
STATIC_MEMBERS = {
    "contract/bundle-contract.json": SOURCE_ROOT / "bundle-contract.json",
    "config/config.template.json": SOURCE_ROOT / "config.template.json",
    "systemd/pokrov-hy2-lab.service": SOURCE_ROOT / "pokrov-hy2-lab.service",
    "README.md": SOURCE_ROOT / "README.md",
}
CORE_MEMBERS = {
    "LICENSES/sing-box-GPL-3.0-or-later.txt": "engine/sing-box/LICENSE",
    "THIRD_PARTY_NOTICES.md": "THIRD_PARTY_NOTICES.md",
}
EXPECTED_MEMBERS = (
    MANIFEST_NAME,
    BINARY_MEMBER,
    *STATIC_MEMBERS.keys(),
    *CORE_MEMBERS.keys(),
)
PLACEHOLDERS = {
    "${POKROV_HY2_USER_NAME}",
    "${POKROV_HY2_PASSWORD}",
    "${POKROV_HY2_OBFS_PASSWORD}",
    "${POKROV_HY2_CERTIFICATE_PATH}",
    "${POKROV_HY2_KEY_PATH}",
}


class Hy2ServerBundleError(RuntimeError):
    """Raised when the server artifact is incomplete, unsafe or non-reproducible."""


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(dict(value), ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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
        raise Hy2ServerBundleError(f"command_failed:{detail[:800]}")
    return result.stdout.strip()


def _resolved_file(value: str | Path, *, code: str) -> Path:
    path = Path(value).resolve()
    if not path.is_file():
        raise Hy2ServerBundleError(code)
    return path


def _resolved_core_root(value: str | Path) -> Path:
    root = Path(value).resolve()
    if not root.is_dir() or not (root / "engine" / "sing-box" / "go.mod").is_file():
        raise Hy2ServerBundleError("core_root_invalid")
    return root


def _load_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Hy2ServerBundleError(code) from exc
    if not isinstance(value, dict):
        raise Hy2ServerBundleError(code)
    return value


def _core_provenance(core_root: Path, go_executable: Path) -> dict[str, Any]:
    revision = _run(["git", "rev-parse", "HEAD"], cwd=core_root).lower()
    if revision != EXPECTED_CORE_REVISION:
        raise Hy2ServerBundleError("core_revision_mismatch")
    status = _run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=core_root
    )
    if status:
        raise Hy2ServerBundleError("core_tree_not_clean")
    go_version = _run([str(go_executable), "env", "GOVERSION"], cwd=core_root)
    if go_version != EXPECTED_GO_VERSION:
        raise Hy2ServerBundleError("go_toolchain_mismatch")
    release = _load_json(core_root / "config" / "release.json", code="core_release_invalid")
    capability_path = core_root / "config" / "hy2-capability.json"
    capability = _load_json(capability_path, code="hy2_capability_invalid")
    if (
        release.get("go_toolchain") != EXPECTED_GO_VERSION
        or (release.get("engine") or {}).get("sing_box") != SOURCE_ENGINE_VERSION
        or capability.get("contract_id") != EXPECTED_CONTRACT_ID
        or capability.get("status") != "lab_disabled_by_default"
        or capability.get("public_runtime_advertised") is not False
        or (capability.get("engine") or {}).get("build_tag") != "with_quic"
        or _sha256(capability_path.read_bytes()) != EXPECTED_CONTRACT_SHA256
    ):
        raise Hy2ServerBundleError("hy2_core_contract_mismatch")
    source_epoch = int(_run(["git", "show", "-s", "--format=%ct", revision], cwd=core_root))
    source_time = datetime.fromtimestamp(source_epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "repository": "Kiwunaka/pokrov-core",
        "revision": revision,
        "source_epoch": source_epoch,
        "source_time_utc": source_time,
        "go_toolchain": go_version,
        "sing_box_source_version": SOURCE_ENGINE_VERSION,
        "contract_id": EXPECTED_CONTRACT_ID,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
    }


def _build_environment(*, goos: str, goarch: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "CGO_ENABLED": "0",
            "GOOS": goos,
            "GOARCH": goarch,
            "GOFLAGS": "-mod=readonly",
        }
    )
    return env


def _build_command(go_executable: Path, output: Path) -> list[str]:
    ldflags = (
        "-s -w -buildid= "
        f"-X github.com/sagernet/sing-box/constant.Version={BINARY_VERSION}"
    )
    return [
        str(go_executable),
        "build",
        "-trimpath",
        "-buildvcs=false",
        "-tags",
        ",".join(BUILD_TAGS),
        "-ldflags",
        ldflags,
        "-o",
        str(output),
        "./cmd/sing-box",
    ]


def _build_linux_binary_twice(core_root: Path, go_executable: Path) -> bytes:
    engine_root = core_root / "engine" / "sing-box"
    with tempfile.TemporaryDirectory(prefix="pokrov-hy2-linux-build-") as raw_temp:
        temp = Path(raw_temp)
        first = temp / "first" / "pokrov-sing-box-hy2"
        second = temp / "second" / "pokrov-sing-box-hy2"
        first.parent.mkdir()
        second.parent.mkdir()
        env = _build_environment(goos="linux", goarch="amd64")
        _run(_build_command(go_executable, first), cwd=engine_root, env=env)
        _run(_build_command(go_executable, second), cwd=engine_root, env=env)
        first_bytes = first.read_bytes()
        second_bytes = second.read_bytes()
        if first_bytes != second_bytes:
            raise Hy2ServerBundleError("linux_binary_not_reproducible")
        if len(first_bytes) < 10_000_000 or not first_bytes.startswith(b"\x7fELF"):
            raise Hy2ServerBundleError("linux_binary_shape_invalid")
        return first_bytes


def _replace_placeholders(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: _replace_placeholders(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(item, replacements) for item in value]
    if isinstance(value, str):
        return replacements.get(value, value)
    return value


def _synthetic_certificate(directory: Path) -> tuple[Path, Path]:
    key = ec.generate_private_key(ec.SECP256R1())
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "hy2.example.invalid")]
    )
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(1)
        .not_valid_before(datetime(2026, 1, 1, tzinfo=timezone.utc))
        .not_valid_after(datetime(2030, 1, 1, tzinfo=timezone.utc))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("hy2.example.invalid")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    certificate_path = directory / "synthetic-cert.pem"
    key_path = directory / "synthetic-key.pem"
    certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return certificate_path, key_path


def _validate_template_with_host_binary(
    *, core_root: Path, go_executable: Path, template: Mapping[str, Any]
) -> None:
    engine_root = core_root / "engine" / "sing-box"
    with tempfile.TemporaryDirectory(prefix="pokrov-hy2-config-check-") as raw_temp:
        temp = Path(raw_temp)
        checker = temp / ("sing-box-check.exe" if os.name == "nt" else "sing-box-check")
        host_goos = _run([str(go_executable), "env", "GOOS"], cwd=engine_root)
        host_goarch = _run([str(go_executable), "env", "GOARCH"], cwd=engine_root)
        _run(
            _build_command(go_executable, checker),
            cwd=engine_root,
            env=_build_environment(goos=host_goos, goarch=host_goarch),
        )
        certificate_path, key_path = _synthetic_certificate(temp)
        materialized = _replace_placeholders(
            template,
            {
                "${POKROV_HY2_USER_NAME}": "synthetic-owner",
                "${POKROV_HY2_PASSWORD}": "synthetic-password-0001",
                "${POKROV_HY2_OBFS_PASSWORD}": "synthetic-obfs-password-0001",
                "${POKROV_HY2_CERTIFICATE_PATH}": str(certificate_path),
                "${POKROV_HY2_KEY_PATH}": str(key_path),
            },
        )
        config_path = temp / "config.json"
        config_path.write_bytes(_canonical_json(materialized))
        _run([str(checker), "check", "-c", str(config_path)], cwd=temp)


def _source_contents(core_root: Path) -> dict[str, bytes]:
    contents: dict[str, bytes] = {}
    for member, path in STATIC_MEMBERS.items():
        contents[member] = _resolved_file(path, code=f"source_missing:{member}").read_bytes()
    for member, relative in CORE_MEMBERS.items():
        contents[member] = _resolved_file(
            core_root / PurePosixPath(relative), code=f"core_source_missing:{member}"
        ).read_bytes()
    return contents


def _validate_source_contract(contents: Mapping[str, bytes]) -> dict[str, Any]:
    try:
        contract = json.loads(contents["contract/bundle-contract.json"].decode("utf-8"))
        template = json.loads(contents["config/config.template.json"].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Hy2ServerBundleError("bundle_source_json_invalid") from exc
    if not isinstance(contract, dict):
        raise Hy2ServerBundleError("bundle_contract_invalid")
    if (
        contract.get("schema_version") != BUNDLE_SCHEMA
        or contract.get("state") != "source_only_default_off"
        or contract.get("contract_id") != EXPECTED_CONTRACT_ID
        or contract.get("contract_sha256") != EXPECTED_CONTRACT_SHA256
        or (contract.get("engine") or {}).get("version") != BINARY_VERSION
        or (contract.get("engine") or {}).get("build_tags") != list(BUILD_TAGS)
        or (contract.get("runtime") or {}).get("listen_port") != 443
        or (contract.get("runtime") or {}).get("single_port") is not True
        or (contract.get("runtime") or {}).get("port_hopping") is not False
        or (contract.get("install") or {}).get("enable_by_default") is not False
        or set(contract.get("runtime_secret_placeholders") or [])
        != {item[2:-1] for item in PLACEHOLDERS}
    ):
        raise Hy2ServerBundleError("bundle_contract_mismatch")
    if not isinstance(template, dict):
        raise Hy2ServerBundleError("config_template_invalid")
    inbounds = template.get("inbounds")
    if not isinstance(inbounds, list) or len(inbounds) != 1:
        raise Hy2ServerBundleError("config_inbound_count_invalid")
    inbound = inbounds[0]
    tls = inbound.get("tls") if isinstance(inbound, dict) else None
    users = inbound.get("users") if isinstance(inbound, dict) else None
    obfs = inbound.get("obfs") if isinstance(inbound, dict) else None
    serialized = json.dumps(template, sort_keys=True)
    if (
        inbound.get("type") != "hysteria2"
        or inbound.get("listen") != "0.0.0.0"
        or inbound.get("listen_port") != 443
        or "server_ports" in serialized
        or "hop_interval" in serialized
        or not isinstance(users, list)
        or len(users) != 1
        or users[0].get("name") != "${POKROV_HY2_USER_NAME}"
        or users[0].get("password") != "${POKROV_HY2_PASSWORD}"
        or not isinstance(obfs, dict)
        or obfs != {
            "type": "salamander",
            "password": "${POKROV_HY2_OBFS_PASSWORD}",
        }
        or not isinstance(tls, dict)
        or tls.get("enabled") is not True
        or tls.get("alpn") != ["h3"]
        or tls.get("min_version") != "1.3"
        or set(_collect_strings(template)).intersection(PLACEHOLDERS) != PLACEHOLDERS
    ):
        raise Hy2ServerBundleError("config_template_contract_mismatch")
    unit = contents["systemd/pokrov-hy2-lab.service"].decode("utf-8")
    required_unit_tokens = (
        "User=pokrov-hy2",
        "ExecStartPre=/opt/pokrov/hy2/current/bin/pokrov-sing-box-hy2 check",
        "ExecStart=/opt/pokrov/hy2/current/bin/pokrov-sing-box-hy2 run",
        "AmbientCapabilities=CAP_NET_BIND_SERVICE",
        "NoNewPrivileges=true",
        "ProtectSystem=strict",
    )
    if any(token not in unit for token in required_unit_tokens) or "Environment=" in unit:
        raise Hy2ServerBundleError("systemd_unit_contract_mismatch")
    return {"contract": contract, "template": template}


def _collect_strings(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [item for child in value.values() for item in _collect_strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _collect_strings(child)]
    return [value] if isinstance(value, str) else []


def _manifest(
    *, provenance: Mapping[str, Any], contract: Mapping[str, Any], contents: Mapping[str, bytes]
) -> dict[str, Any]:
    files = [
        {
            "path": member,
            "sha256": _sha256(contents[member]),
            "size_bytes": len(contents[member]),
            "mode": "0755" if member == BINARY_MEMBER else "0644",
        }
        for member in EXPECTED_MEMBERS
        if member != MANIFEST_NAME
    ]
    return {
        "schema_version": BUNDLE_SCHEMA,
        "state": "immutable_local_server_bundle",
        "candidate_created": False,
        "deploy_authorized": False,
        "deployment_performed": False,
        "contract_id": EXPECTED_CONTRACT_ID,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "variant": contract["variant"],
        "source": dict(provenance),
        "binary": {
            "path": BINARY_MEMBER,
            "version": BINARY_VERSION,
            "goos": "linux",
            "goarch": "amd64",
            "cgo_enabled": False,
            "build_tags": list(BUILD_TAGS),
            "reproducibility": "PASS_BYTE_IDENTICAL_TWO_BUILDS",
            "config_check": "PASS_SYNTHETIC_HOST_BINARY",
        },
        "runtime": dict(contract["runtime"]),
        "install": dict(contract["install"]),
        "rollback": dict(contract["rollback"]),
        "runtime_secret_names": list(contract["runtime_secret_placeholders"]),
        "raw_runtime_material_included": False,
        "files": files,
        "evidence_ceiling": contract["evidence_ceiling"],
    }


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    mode = 0o100755 if name == BINARY_MEMBER else 0o100644
    info.external_attr = mode << 16
    return info


def build_bundle(*, core_root: str | Path, go_executable: str | Path, output: str | Path) -> dict[str, Any]:
    core = _resolved_core_root(core_root)
    go = _resolved_file(go_executable, code="go_executable_missing")
    destination = Path(output).resolve()
    if destination.exists():
        raise Hy2ServerBundleError("output_already_exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    provenance = _core_provenance(core, go)
    contents = _source_contents(core)
    source = _validate_source_contract(contents)
    _validate_template_with_host_binary(core_root=core, go_executable=go, template=source["template"])
    contents[BINARY_MEMBER] = _build_linux_binary_twice(core, go)
    manifest = _manifest(provenance=provenance, contract=source["contract"], contents=contents)
    descriptor: int | None = None
    temporary_name = ""
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=str(destination.parent)
        )
        os.close(descriptor)
        descriptor = None
        with zipfile.ZipFile(
            temporary_name,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            archive.writestr(_zip_info(MANIFEST_NAME), _canonical_json(manifest))
            for member in EXPECTED_MEMBERS:
                if member == MANIFEST_NAME:
                    continue
                archive.writestr(_zip_info(member), contents[member])
        os.replace(temporary_name, destination)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_name and Path(temporary_name).exists():
            Path(temporary_name).unlink()
    verified = verify_bundle(destination)
    return {
        **verified,
        "mode": "BUILD",
        "bundle_path": str(destination),
    }


def _validated_bundle(bundle: str | Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    source = _resolved_file(bundle, code="bundle_missing")
    try:
        with zipfile.ZipFile(source, mode="r") as archive:
            names = archive.namelist()
            if names != list(EXPECTED_MEMBERS) or len(names) != len(set(names)):
                raise Hy2ServerBundleError("bundle_member_set_invalid")
            if any(
                info.is_dir()
                or PurePosixPath(info.filename).is_absolute()
                or ".." in PurePosixPath(info.filename).parts
                for info in archive.infolist()
            ):
                raise Hy2ServerBundleError("bundle_member_path_invalid")
            if any(info.file_size > 100_000_000 for info in archive.infolist()):
                raise Hy2ServerBundleError("bundle_member_too_large")
            manifest_bytes = archive.read(MANIFEST_NAME)
            contents = {
                member: archive.read(member)
                for member in EXPECTED_MEMBERS
                if member != MANIFEST_NAME
            }
    except zipfile.BadZipFile as exc:
        raise Hy2ServerBundleError("bundle_zip_invalid") from exc
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Hy2ServerBundleError("bundle_manifest_invalid") from exc
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != BUNDLE_SCHEMA
        or manifest.get("state") != "immutable_local_server_bundle"
        or manifest.get("candidate_created") is not False
        or manifest.get("deploy_authorized") is not False
        or manifest.get("deployment_performed") is not False
        or manifest.get("contract_id") != EXPECTED_CONTRACT_ID
        or manifest.get("contract_sha256") != EXPECTED_CONTRACT_SHA256
        or manifest.get("raw_runtime_material_included") is not False
    ):
        raise Hy2ServerBundleError("bundle_manifest_contract_invalid")
    expected_files = manifest.get("files")
    if not isinstance(expected_files, list) or len(expected_files) != len(contents):
        raise Hy2ServerBundleError("bundle_file_manifest_invalid")
    records = {str(item.get("path")): item for item in expected_files if isinstance(item, dict)}
    if set(records) != set(contents):
        raise Hy2ServerBundleError("bundle_file_manifest_invalid")
    for member, content in contents.items():
        record = records[member]
        if record.get("sha256") != _sha256(content) or record.get("size_bytes") != len(content):
            raise Hy2ServerBundleError("bundle_file_digest_mismatch")
    binary = contents[BINARY_MEMBER]
    if len(binary) < 10_000_000 or not binary.startswith(b"\x7fELF"):
        raise Hy2ServerBundleError("bundle_binary_invalid")
    template = json.loads(contents["config/config.template.json"].decode("utf-8"))
    if set(_collect_strings(template)).intersection(PLACEHOLDERS) != PLACEHOLDERS:
        raise Hy2ServerBundleError("bundle_runtime_placeholders_missing")
    source = _validate_source_contract(contents)
    if (
        manifest.get("variant") != source["contract"].get("variant")
        or manifest.get("runtime") != source["contract"].get("runtime")
        or manifest.get("install") != source["contract"].get("install")
        or manifest.get("rollback") != source["contract"].get("rollback")
    ):
        raise Hy2ServerBundleError("bundle_embedded_contract_mismatch")
    return manifest, contents


def verify_bundle(bundle: str | Path) -> dict[str, Any]:
    source = _resolved_file(bundle, code="bundle_missing")
    manifest, _contents = _validated_bundle(source)
    return {
        "schema_version": BUNDLE_SCHEMA,
        "mode": "VERIFY",
        "ok": True,
        "bundle_sha256": _sha256(source.read_bytes()),
        "bundle_size_bytes": source.stat().st_size,
        "binary_sha256": next(
            item["sha256"] for item in manifest["files"] if item["path"] == BINARY_MEMBER
        ),
        "source_revision": manifest["source"]["revision"],
        "contract_sha256": manifest["contract_sha256"],
        "deployment_performed": False,
        "raw_runtime_material_included": False,
    }


def plan_bundle(*, bundle: str | Path, operation: str, node_code: str) -> dict[str, Any]:
    source = _resolved_file(bundle, code="bundle_missing")
    manifest, _contents = _validated_bundle(source)
    node = str(node_code or "").strip().lower()
    if not node or len(node) > 32 or not node.replace("-", "").isalnum():
        raise Hy2ServerBundleError("node_code_invalid")
    install = manifest["install"]
    rollback = manifest["rollback"]
    common = {
        "schema_version": "pokrov-owned-hy2-server-plan-v1",
        "mode": "PLAN",
        "operation": operation,
        "node_code": node,
        "bundle_sha256": _sha256(source.read_bytes()),
        "source_revision": manifest["source"]["revision"],
        "service_name": install["service_name"],
        "listen_protocol": "udp",
        "listen_port": manifest["runtime"]["listen_port"],
        "mutation_performed": False,
        "raw_addresses_returned": False,
        "raw_runtime_material_returned": False,
    }
    if operation == "install":
        common.update(
            {
                "preconditions": [
                    "separate_owner_authorization",
                    "exact_bundle_digest_confirmation",
                    "owned_node_identity_and_host_key_readback",
                    "udp_port_free_and_ufw_active",
                    "owner_only_runtime_config_and_tls_key_ready",
                    "previous_state_receipt_and_backup_ready",
                ],
                "ordered_actions": [
                    "stage_and_verify_bundle_without_runtime_material",
                    "retain_exact_previous_pointer_config_unit_and_firewall_receipt",
                    "install_release_directory_and_inactive_unit",
                    "write_owner_only_runtime_config_directly_from_secret_inputs",
                    "run_config_check_then_open_exact_udp_port",
                    "start_without_enable_then_verify_service_socket_and_sanitized_handshake",
                    "enable_only_after_post_start_readback",
                ],
                "rollback_contract": dict(rollback),
            }
        )
    elif operation == "rollback":
        common.update(
            {
                "required_inputs": [
                    "separate_owner_authorization",
                    "exact_current_bundle_digest",
                    "exact_previous_state_receipt",
                ],
                "ordered_actions": [
                    "engage_platform_hy2_kill_switch_before_server_change",
                    "disable_and_stop_exact_service",
                    "verify_udp_listener_absent",
                    "restore_only_receipt_bound_pointer_config_unit_and_firewall_state",
                    "daemon_reload_and_verify_previous_or_inactive_state",
                    "retain_failed_release_and_sanitized_rollback_evidence",
                ],
                "rollback_contract": dict(rollback),
            }
        )
    else:
        raise Hy2ServerBundleError("operation_invalid")
    return common


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build, verify or plan the immutable owned Hysteria2 server bundle."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--core-root", required=True)
    build.add_argument("--go-executable", required=True)
    build.add_argument("--output", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--bundle", required=True)
    plan = subparsers.add_parser("plan")
    plan.add_argument("--bundle", required=True)
    plan.add_argument("--operation", choices=("install", "rollback"), required=True)
    plan.add_argument("--node-code", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "build":
            result = build_bundle(
                core_root=args.core_root,
                go_executable=args.go_executable,
                output=args.output,
            )
        elif args.command == "verify":
            result = verify_bundle(args.bundle)
        else:
            result = plan_bundle(
                bundle=args.bundle,
                operation=args.operation,
                node_code=args.node_code,
            )
    except Hy2ServerBundleError as exc:
        print(
            json.dumps(
                {
                    "schema_version": BUNDLE_SCHEMA,
                    "mode": str(args.command or "UNKNOWN").upper(),
                    "ok": False,
                    "error": str(exc)[:800],
                    "mutation_performed": False,
                    "raw_runtime_material_returned": False,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
