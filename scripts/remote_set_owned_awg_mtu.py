from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import (
    CONFIG_ROOT,
    NODE_CODE,
    OWNED_AWG_MTU,
    _activate_control_plane,
    _node_host,
    _run_remote,
    _sftp_write,
)
from remote_rebind_owned_awg_lab_ports import _active_identity, _read_config
from remote_run_owned_awg_core_interop import _load_material


PROFILES = {
    "awg2_lab": "pokrovawg2",
    "awg31_lab": "pokrovawg31",
}
ALLOWED_SOURCE_MTUS = frozenset({1280, 1400, 1408})
_MTU_RE = re.compile(rb"(?m)^(MTU\s*=\s*)(\d+)(\s*)$")


class MtuUpdateError(RuntimeError):
    pass


def _server_mtu(raw: bytes | bytearray) -> int:
    matches = list(_MTU_RE.finditer(bytes(raw)))
    if len(matches) != 1:
        raise MtuUpdateError("server configuration MTU precondition failed")
    value = int(matches[0].group(2))
    if value not in ALLOWED_SOURCE_MTUS:
        raise MtuUpdateError("server configuration MTU is outside the owned contract")
    return value


def _replace_server_mtu(raw: bytes | bytearray, *, target: int) -> bytes:
    _server_mtu(raw)
    updated = _MTU_RE.sub(
        lambda match: match.group(1) + str(target).encode("ascii") + match.group(3),
        bytes(raw),
        count=1,
    )
    if _server_mtu(updated) != target:
        raise MtuUpdateError("server configuration MTU transform failed")
    return updated


def _material_with_mtu(raw: bytes | bytearray, *, target: int) -> dict[str, Any]:
    try:
        endpoint = json.loads(raw)
        current = int(endpoint["mtu"])
    except Exception as exc:
        raise MtuUpdateError("AWG endpoint material shape invalid") from exc
    if current not in ALLOWED_SOURCE_MTUS:
        raise MtuUpdateError("AWG endpoint material MTU is outside the owned contract")
    endpoint["mtu"] = target
    return endpoint


def _write_config(node: Any, interface: str, raw: bytes | bytearray) -> None:
    sftp = node.open_sftp()
    try:
        _sftp_write(sftp, f"{CONFIG_ROOT}/{interface}.conf", bytes(raw), 0o600)
    finally:
        sftp.close()


def _retain_backup(node: Any, configs: dict[str, bytes | bytearray]) -> None:
    root = (
        "/root/pokrov-awg-lab-mtu-backups/"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    _run_remote(node, f"install -d -m 0700 {shlex.quote(root)}")
    sftp = node.open_sftp()
    try:
        for profile, interface in PROFILES.items():
            _sftp_write(sftp, f"{root}/{interface}.conf", bytes(configs[profile]), 0o600)
    finally:
        sftp.close()


def _apply_server_configs(node: Any, configs: dict[str, bytes | bytearray]) -> None:
    for profile, interface in PROFILES.items():
        _write_config(node, interface, configs[profile])
    for interface in PROFILES.values():
        _run_remote(
            node,
            f"systemctl restart pokrov-awg-lab@{interface}.service",
            timeout=120,
        )


def _server_checks(node: Any, *, target: int) -> dict[str, dict[str, bool]]:
    checks: dict[str, dict[str, bool]] = {}
    for profile, interface in PROFILES.items():
        persisted = _read_config(node, interface)
        try:
            live_mtu = _run_remote(
                node,
                f"ip -o link show dev {shlex.quote(interface)} | "
                "awk '{ for (i=1; i<=NF; i++) if ($i == \"mtu\") { print $(i+1); exit } }'",
            )
            service = _run_remote(
                node,
                f"systemctl is-active pokrov-awg-lab@{interface}.service",
            )
            checks[profile] = {
                "persisted_mtu": _server_mtu(persisted) == target,
                "live_mtu": live_mtu == str(target),
                "service_active": service == "active",
            }
        finally:
            for index in range(len(persisted)):
                persisted[index] = 0
    return checks


def _material_checks(brain: Any, *, target: int) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    buffers: list[bytearray] = []
    try:
        for profile in PROFILES:
            raw = bytearray(_load_material(brain, profile))
            buffers.append(raw)
            checks[profile] = int(json.loads(raw)["mtu"]) == target
        return checks
    finally:
        for raw in buffers:
            for index in range(len(raw)):
                raw[index] = 0


def _emit(report: dict[str, Any], output_path: str) -> None:
    encoded = json.dumps(report, sort_keys=True)
    if output_path:
        target = Path(output_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guarded update of both owned AWG lab MTUs after a measured path-MTU failure."
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--confirm-node", default="")
    parser.add_argument("--confirm-mtu", type=int, default=0)
    parser.add_argument("--json-out", default="")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    target_mtu = int(OWNED_AWG_MTU)
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)

    brain, _brain_auth = connect_node(
        code="brain", host=str(args.brain_ip), passwords_path=passwords
    )
    node = None
    materials: dict[str, bytearray] = {}
    old_configs: dict[str, bytearray] = {}
    server_changed = False
    control_attempted = False
    tg_id = 0
    install_id = ""
    stage = "connect"
    try:
        stage = "active_identity"
        tg_id, install_id = _active_identity(brain)
        stage = "node_connect"
        node = connect_node(
            code=NODE_CODE,
            host=_node_host(brain),
            passwords_path=passwords,
        )[0]
        stage = "preflight"
        for profile, interface in PROFILES.items():
            materials[profile] = bytearray(_load_material(brain, profile))
            old_configs[profile] = _read_config(node, interface)
        updated_materials = {
            profile: _material_with_mtu(raw, target=target_mtu)
            for profile, raw in materials.items()
        }
        updated_configs = {
            profile: _replace_server_mtu(raw, target=target_mtu)
            for profile, raw in old_configs.items()
        }
        source_mtus = {
            profile: {
                "server": _server_mtu(old_configs[profile]),
                "material": int(json.loads(materials[profile])["mtu"]),
            }
            for profile in PROFILES
        }
        report: dict[str, Any] = {
            "schema_version": "pokrov-owned-awg-mtu-update-v1",
            "mode": "APPLY" if args.apply else "PLAN",
            "node_code": NODE_CODE,
            "target_mtu": target_mtu,
            "source_mtus": source_mtus,
            "target_install_sha256": hashlib.sha256(install_id.encode()).hexdigest(),
            "preflight": {
                "active_material_identity_consistent": True,
                "server_transform_ready": all(
                    _server_mtu(raw) == target_mtu for raw in updated_configs.values()
                ),
                "material_transform_ready": all(
                    int(endpoint["mtu"]) == target_mtu
                    for endpoint in updated_materials.values()
                ),
            },
            "raw_identifiers_returned": False,
            "raw_material_returned": False,
        }
        if not args.apply:
            report["ok"] = True
            _emit(report, str(args.json_out or ""))
            return 0
        if str(args.confirm_node).strip().lower() != NODE_CODE:
            raise MtuUpdateError("--confirm-node mismatch")
        if int(args.confirm_mtu) != target_mtu:
            raise MtuUpdateError("--confirm-mtu mismatch")

        already_target = all(
            values["server"] == target_mtu and values["material"] == target_mtu
            for values in source_mtus.values()
        )
        if not already_target:
            stage = "backup"
            _retain_backup(node, old_configs)
            stage = "dataplane"
            server_changed = True
            _apply_server_configs(node, updated_configs)
            stage = "control_plane"
            control_attempted = True
            report["control_plane"] = _activate_control_plane(
                brain,
                tg_id=tg_id,
                install_id=install_id,
                extend_entitlement=False,
                awg2_endpoint=updated_materials["awg2_lab"],
                awg31_endpoint=updated_materials["awg31_lab"],
            )
        stage = "readback"
        report["readback"] = {
            "server": _server_checks(node, target=target_mtu),
            "material": _material_checks(brain, target=target_mtu),
            "backup_retained": not already_target,
        }
        report["ok"] = all(
            all(values.values())
            for values in report["readback"]["server"].values()
        ) and all(report["readback"]["material"].values())
        if not report["ok"]:
            raise MtuUpdateError("AWG MTU readback failed")
        _emit(report, str(args.json_out or ""))
        return 0
    except Exception as exc:
        if node is not None and server_changed and old_configs:
            try:
                _apply_server_configs(node, old_configs)
            except Exception:
                pass
        if control_attempted and tg_id > 0 and install_id and materials:
            try:
                _activate_control_plane(
                    brain,
                    tg_id=tg_id,
                    install_id=install_id,
                    extend_entitlement=False,
                    awg2_endpoint=json.loads(materials["awg2_lab"]),
                    awg31_endpoint=json.loads(materials["awg31_lab"]),
                )
            except Exception:
                pass
        _emit(
            {
                "schema_version": "pokrov-owned-awg-mtu-update-v1",
                "mode": "APPLY" if args.apply else "PLAN",
                "node_code": NODE_CODE,
                "target_mtu": target_mtu,
                "ok": False,
                "error_type": type(exc).__name__,
                "failure_stage": stage,
                "rollback_attempted": bool(server_changed or control_attempted),
                "raw_identifiers_returned": False,
                "raw_material_returned": False,
            },
            str(args.json_out or ""),
        )
        return 1
    finally:
        if node is not None:
            node.close()
        brain.close()
        for raw in [*materials.values(), *old_configs.values()]:
            for index in range(len(raw)):
                raw[index] = 0


if __name__ == "__main__":
    raise SystemExit(main())
