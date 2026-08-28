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
    AWG_TARGET,
    CONFIG_ROOT,
    NODE_CODE,
    _activate_control_plane,
    _node_host,
    _psql,
    _run_remote,
    _sftp_write,
)
from remote_run_owned_awg_core_interop import _load_material


PORTS = {
    "awg2_lab": {"interface": "pokrovawg2", "old": 51820, "new": 4500},
    "awg31_lab": {"interface": "pokrovawg31", "old": 51831, "new": 3478},
}
_LISTEN_PORT_RE = re.compile(rb"(?m)^(ListenPort\s*=\s*)(\d+)(\s*)$")


class RebindError(RuntimeError):
    pass


def _replace_listen_port(raw: bytes, *, expected: int, target: int) -> bytes:
    matches = list(_LISTEN_PORT_RE.finditer(raw))
    if len(matches) != 1 or int(matches[0].group(2)) != expected:
        raise RebindError("server configuration ListenPort precondition failed")
    return _LISTEN_PORT_RE.sub(
        lambda match: match.group(1) + str(target).encode("ascii") + match.group(3),
        raw,
        count=1,
    )


def _read_config(node: Any, interface: str) -> bytearray:
    sftp = node.open_sftp()
    try:
        with sftp.open(f"{CONFIG_ROOT}/{interface}.conf", "rb") as handle:
            raw = bytearray(handle.read(64 * 1024 + 1))
    finally:
        sftp.close()
    if not 1 <= len(raw) <= 64 * 1024:
        raise RebindError("server configuration size invalid")
    return raw


def _write_config(node: Any, interface: str, raw: bytes) -> None:
    sftp = node.open_sftp()
    try:
        _sftp_write(sftp, f"{CONFIG_ROOT}/{interface}.conf", raw, 0o600)
    finally:
        sftp.close()


def _active_identity(brain: Any) -> tuple[int, str]:
    raw = _psql(
        brain,
        """
with a as (
  select tg_id, install_id from awg2_lab_materials
  where is_active and state='ready'
  order by provisioned_at desc, id desc limit 1
), b as (
  select tg_id, install_id from awg31_lab_materials
  where is_active and state='ready'
  order by provisioned_at desc, id desc limit 1
)
select json_build_object('tg_id',a.tg_id,'install_id',a.install_id)::text
from a join b on b.tg_id=a.tg_id and b.install_id=a.install_id;
""".strip(),
    )
    try:
        payload = json.loads(raw)
        tg_id = int(payload["tg_id"])
        install_id = str(payload["install_id"]).strip()
    except Exception as exc:
        raise RebindError("active AWG lab identity is unavailable or inconsistent") from exc
    if tg_id <= 0 or not install_id:
        raise RebindError("active AWG lab identity is invalid")
    return tg_id, install_id


def _material_with_port(raw: bytes, *, expected: int, target: int) -> dict[str, Any]:
    try:
        endpoint = json.loads(raw)
        peers = endpoint["peers"]
        if not isinstance(peers, list) or len(peers) != 1:
            raise ValueError("peer count")
        current_port = int(peers[0]["port"])
    except Exception as exc:
        raise RebindError("AWG endpoint material shape invalid") from exc
    if current_port != expected:
        raise RebindError("AWG endpoint port precondition failed")
    peers[0]["port"] = target
    return endpoint


def _live_port_checks(node: Any, *, port_key: str) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    for profile, item in PORTS.items():
        interface = str(item["interface"])
        port = int(item[port_key])
        live = _run_remote(node, f"{AWG_TARGET} show {interface} listen-port")
        socket_ready = _run_remote(
            node,
            f"if ss -H -lun 'sport = :{port}' | grep -q .; then printf yes; else printf no; fi",
        )
        checks[profile] = live == str(port) and socket_ready == "yes"
    return checks


def _new_ports_free(node: Any) -> dict[str, bool]:
    return {
        profile: _run_remote(
            node,
            f"if ss -H -lun 'sport = :{int(item['new'])}' | grep -q .; then printf busy; else printf free; fi",
        )
        == "free"
        for profile, item in PORTS.items()
    }


def _apply_server_ports(
    node: Any, configs: dict[str, bytes | bytearray], *, port_key: str
) -> None:
    for profile, item in PORTS.items():
        interface = str(item["interface"])
        _write_config(node, interface, configs[profile])
        _run_remote(
            node,
            f"{AWG_TARGET} set {interface} listen-port {int(item[port_key])}",
        )
    if not all(_live_port_checks(node, port_key=port_key).values()):
        raise RebindError("live AWG listen-port readback failed")


def _allow_new_ports(node: Any) -> None:
    status = _run_remote(node, "ufw status")
    if not any(line.strip().lower() == "status: active" for line in status.splitlines()):
        raise RebindError("UFW is not active on the owned AWG node")
    for profile, item in PORTS.items():
        comment = shlex.quote(f"POKROV owned {profile}")
        _run_remote(node, f"ufw allow {int(item['new'])}/udp comment {comment}")


def _retain_backup(node: Any, configs: dict[str, bytes | bytearray]) -> None:
    backup_root = (
        "/root/pokrov-awg-lab-port-backups/"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    _run_remote(node, f"install -d -m 0700 {shlex.quote(backup_root)}")
    sftp = node.open_sftp()
    try:
        for profile, item in PORTS.items():
            _sftp_write(
                sftp,
                f"{backup_root}/{item['interface']}.conf",
                bytes(configs[profile]),
                0o600,
            )
    finally:
        sftp.close()


def _material_port_checks(brain: Any, *, port_key: str) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    buffers: list[bytearray] = []
    try:
        for profile, item in PORTS.items():
            raw = bytearray(_load_material(brain, profile))
            buffers.append(raw)
            endpoint = json.loads(raw)
            checks[profile] = int(endpoint["peers"][0]["port"]) == int(
                item[port_key]
            )
        return checks
    finally:
        for raw in buffers:
            for index in range(len(raw)):
                raw[index] = 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guarded port rebind for the existing owned AWG2/AWG3.1 labs."
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--confirm-node", default="")
    parser.add_argument("--confirm-awg2-port", type=int, default=0)
    parser.add_argument("--confirm-awg31-port", type=int, default=0)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
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
    new_configs: dict[str, bytes] = {}
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
            code=NODE_CODE, host=_node_host(brain), passwords_path=passwords
        )[0]
        stage = "preflight"
        for profile, item in PORTS.items():
            materials[profile] = bytearray(_load_material(brain, profile))
            old_configs[profile] = _read_config(node, str(item["interface"]))
            new_configs[profile] = _replace_listen_port(
                old_configs[profile],
                expected=int(item["old"]),
                target=int(item["new"]),
            )
            _material_with_port(
                materials[profile],
                expected=int(item["old"]),
                target=int(item["new"]),
            )
        old_live = _live_port_checks(node, port_key="old")
        free = _new_ports_free(node)
        report: dict[str, Any] = {
            "schema_version": "pokrov-owned-awg-port-rebind-v1",
            "mode": "APPLY" if args.apply else "PLAN",
            "node_code": NODE_CODE,
            "target_ports": {
                profile: int(item["new"]) for profile, item in PORTS.items()
            },
            "preflight": {
                "old_live_ports_match": old_live,
                "new_ports_free": free,
                "active_material_identity_consistent": True,
            },
            "target_install_sha256": hashlib.sha256(install_id.encode()).hexdigest(),
            "raw_identifiers_returned": False,
            "raw_material_returned": False,
        }
        if not all(old_live.values()) or not all(free.values()):
            raise RebindError("AWG port rebind preflight failed")
        if not args.apply:
            report["ok"] = True
            print(json.dumps(report, sort_keys=True))
            return 0
        if str(args.confirm_node).strip().lower() != NODE_CODE:
            raise RebindError("--confirm-node mismatch")
        if int(args.confirm_awg2_port) != int(PORTS["awg2_lab"]["new"]):
            raise RebindError("--confirm-awg2-port mismatch")
        if int(args.confirm_awg31_port) != int(PORTS["awg31_lab"]["new"]):
            raise RebindError("--confirm-awg31-port mismatch")

        stage = "backup"
        _retain_backup(node, old_configs)
        stage = "firewall"
        _allow_new_ports(node)
        server_changed = True
        stage = "dataplane"
        _apply_server_ports(node, new_configs, port_key="new")
        updated = {
            profile: _material_with_port(
                materials[profile],
                expected=int(item["old"]),
                target=int(item["new"]),
            )
            for profile, item in PORTS.items()
        }
        control_attempted = True
        stage = "control_plane"
        report["control_plane"] = _activate_control_plane(
            brain,
            tg_id=tg_id,
            install_id=install_id,
            extend_entitlement=False,
            awg2_endpoint=updated["awg2_lab"],
            awg31_endpoint=updated["awg31_lab"],
        )
        stage = "readback"
        report["readback"] = {
            "live_ports": _live_port_checks(node, port_key="new"),
            "material_ports": _material_port_checks(brain, port_key="new"),
            "backup_retained": True,
        }
        report["ok"] = all(report["readback"]["live_ports"].values()) and all(
            report["readback"]["material_ports"].values()
        )
        if not report["ok"]:
            raise RebindError("AWG port rebind readback failed")
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception as exc:
        if node is not None and server_changed:
            try:
                _apply_server_ports(node, old_configs, port_key="old")
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
        print(
            json.dumps(
                {
                    "schema_version": "pokrov-owned-awg-port-rebind-v1",
                    "mode": "APPLY" if args.apply else "PLAN",
                    "node_code": NODE_CODE,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "failure_stage": stage,
                    "rollback_attempted": bool(server_changed or control_attempted),
                    "raw_identifiers_returned": False,
                    "raw_material_returned": False,
                },
                sort_keys=True,
            )
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
