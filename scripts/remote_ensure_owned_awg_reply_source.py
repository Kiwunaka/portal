from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import shlex
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import (
    AWG2_INTERFACE,
    AWG2_PORT,
    AWG31_INTERFACE,
    AWG31_PORT,
    CONFIG_ROOT,
    _node_host,
    _reply_source_policy_lines,
    _run_remote,
    _sftp_write,
)


NODE_CODE = "de"
OUTPUT_SCHEMA = "pokrov-owned-awg-reply-source-v1"
BACKUP_ROOT = "/root/pokrov-awg-lab-reply-source-backups"
PROFILES = (
    ("awg2_lab", AWG2_INTERFACE, AWG2_PORT),
    ("awg31_lab", AWG31_INTERFACE, AWG31_PORT),
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Guardedly pin owned AWG lab UDP replies to the public endpoint address."
        )
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--confirm-node", default="")
    parser.add_argument("--confirm-target-address-sha256", default="")
    parser.add_argument("--cycle-services", action="store_true")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def _target_address(host: str) -> str:
    address = socket.gethostbyname(host)
    parsed = ipaddress.ip_address(address)
    if parsed.version != 4 or not parsed.is_global:
        raise RuntimeError("owned node endpoint is not a public IPv4 address")
    return address


def _address_sha256(address: str) -> str:
    return hashlib.sha256(address.encode("ascii")).hexdigest()


def _comment(interface: str) -> str:
    return f"POKROV owned {interface} reply source"


def _rule(interface: str, port: int, address: str, operation: str = "-C") -> str:
    position = " 1" if operation == "-I" else ""
    return (
        f"iptables -t nat {operation} POSTROUTING{position} -o eth0 -p udp "
        f"-m udp --sport {port} -m comment --comment '{_comment(interface)}' "
        f"-j SNAT --to-source {address}"
    )


def _persistent_lines(
    interface: str, port: int, address: str
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    post_up, post_down = _reply_source_policy_lines(interface, port, address)
    return (
        tuple(f"PostUp = {line}" for line in post_up),
        tuple(f"PostDown = {line}" for line in post_down),
    )


def _updated_config(
    raw: bytes, interface: str, port: int, address: str
) -> tuple[bytes, bool]:
    if not 1 <= len(raw) <= 64 * 1024:
        raise RuntimeError("owned AWG configuration size invalid")
    text = raw.decode("utf-8", "strict")
    expected_up, expected_down = _persistent_lines(interface, port, address)
    expected = (*expected_up, *expected_down)
    if all(line in text for line in expected):
        return raw, False
    expected_comment_lines = tuple(
        line for line in expected if _comment(interface) in line
    )
    if _comment(interface) in text and not all(
        line in text for line in expected_comment_lines
    ):
        raise RuntimeError("conflicting owned AWG reply-source rule exists")
    if text.count("[Interface]") != 1 or f"ListenPort = {port}" not in text:
        raise RuntimeError("owned AWG configuration identity mismatch")
    lines = text.splitlines()
    insertion = next(
        (index for index, line in enumerate(lines) if line.startswith("PostDown =")),
        None,
    )
    if insertion is None:
        raise RuntimeError("owned AWG configuration has no PostDown boundary")
    missing_up = [line for line in expected_up if line not in text]
    lines[insertion:insertion] = missing_up
    peer = next(
        (index for index, line in enumerate(lines) if line.strip() == "[Peer]"),
        None,
    )
    if peer is None:
        raise RuntimeError("owned AWG configuration has no peer section")
    missing_down = [line for line in expected_down if line not in text]
    lines[peer:peer] = missing_down
    updated = ("\n".join(lines) + "\n").encode("utf-8")
    return updated, True


def _rule_present(node: Any, interface: str, port: int, address: str) -> bool:
    command = f"{_rule(interface, port, address)} >/dev/null 2>&1 && echo present || echo absent"
    result = _run_remote(node, command)
    if result not in {"present", "absent"}:
        raise RuntimeError("owned AWG reply-source rule readback invalid")
    return result == "present"


def _managed_rule_count(node: Any, interface: str) -> int:
    comment = shlex.quote(_comment(interface))
    raw = _run_remote(
        node,
        f"iptables -t nat -S POSTROUTING | grep -F -- {comment} | wc -l",
    )
    try:
        count = int(raw)
    except ValueError as exc:
        raise RuntimeError("owned AWG reply-source rule count invalid") from exc
    if count not in {0, 1}:
        raise RuntimeError("duplicate owned AWG reply-source rules exist")
    return count


def _managed_rule_counters(node: Any, interface: str) -> tuple[int, int]:
    comment = shlex.quote(_comment(interface))
    raw = _run_remote(
        node,
        "iptables -t nat -L POSTROUTING -v -n -x | "
        f"grep -F -- {comment} | "
        "awk 'NR==1 { print $1, $2; found=1 } END { if (!found) print \"0 0\" }'",
    ).split()
    if len(raw) != 2 or not all(value.isdigit() for value in raw):
        raise RuntimeError("owned AWG reply-source counters invalid")
    return int(raw[0]), int(raw[1])


def _routing_capabilities(node: Any) -> dict[str, bool | int]:
    raw = _run_remote(
        node,
        "selector=0; ip -4 rule help 2>&1 | grep -q 'sport' && selector=1; "
        "set -- $(ip -4 route show table main default | "
        'awk \'{ count+=1; for(i=1;i<=NF;i++){ if($i=="via") via=1; '
        'if($i=="dev" && $(i+1)=="eth0") eth0=1 } } '
        "END { print count+0, via+0, eth0+0 }'); "
        'printf \'%s %s %s %s\' "$selector" "$1" "$2" "$3"',
    ).split()
    if len(raw) != 4 or not all(value.isdigit() for value in raw):
        raise RuntimeError("owned AWG reply-routing capability readback invalid")
    return {
        "udp_source_port_rule_supported": raw[0] == "1",
        "main_default_route_count": int(raw[1]),
        "main_default_route_has_gateway": raw[2] == "1",
        "main_default_route_uses_eth0": raw[3] == "1",
    }


def _policy_commands(port: int, address: str) -> tuple[str, str]:
    priority = 10_000 + port
    table = 20_000 + port
    apply = (
        "set -eu; gateway=$(ip -4 route show table main default | "
        "awk 'NR==1 { for(i=1;i<=NF;i++) if($i==\"via\") { print $(i+1); exit } }'); "
        'test -n "$gateway"; '
        f'ip -4 route replace table {table} default via "$gateway" dev eth0 src {address}; '
        f"ip -4 rule add priority {priority} ipproto udp sport {port} lookup {table}; "
        "ip -4 route flush cache"
    )
    cleanup = (
        f"ip -4 rule del priority {priority} 2>/dev/null || true; "
        f"ip -4 route flush table {table}; ip -4 route flush cache"
    )
    return apply, cleanup


def _policy_state(node: Any, port: int, address: str) -> dict[str, bool | int]:
    priority = 10_000 + port
    table = 20_000 + port
    raw = _run_remote(
        node,
        f"rules=$(ip -4 rule show | grep -Ec '^{priority}:'); "
        f"exact=$(ip -4 rule show | grep -Ec '^{priority}:.*ipproto udp.*sport {port}.*lookup {table}'); "
        f"routes=$(ip -4 route show table {table} default | wc -l); "
        f"route_exact=$(ip -4 route show table {table} default | "
        f"grep -Ec '^default via .* dev eth0.* src {address}'); "
        'printf \'%s %s %s %s\' "$rules" "$exact" "$routes" "$route_exact"',
    ).split()
    if len(raw) != 4 or not all(value.isdigit() for value in raw):
        raise RuntimeError("owned AWG reply-policy state invalid")
    rule_count, exact_rule_count, route_count, exact_route_count = map(int, raw)
    conflict = (
        rule_count not in {0, 1}
        or exact_rule_count not in {0, 1}
        or route_count not in {0, 1}
        or exact_route_count not in {0, 1}
        or rule_count != exact_rule_count
        or route_count != exact_route_count
        or (rule_count == 1) != (route_count == 1)
    )
    return {
        "policy_rule_present": exact_rule_count == 1,
        "policy_route_present": exact_route_count == 1,
        "policy_conflict": conflict,
    }


def _safe_report(mode: str, target_hash: str) -> dict[str, Any]:
    return {
        "schema_version": OUTPUT_SCHEMA,
        "mode": mode,
        "node": NODE_CODE,
        "target_address_sha256": target_hash,
        "raw_addresses_returned": False,
        "raw_material_returned": False,
    }


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    if args.cycle_services and not args.apply:
        raise SystemExit("--cycle-services requires --apply")
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)

    brain = None
    node = None
    sftp = None
    report: dict[str, Any] = {}
    original: dict[str, tuple[bytes, int]] = {}
    updated: dict[str, bytes] = {}
    initially_present: dict[str, bool] = {}
    added_rules: list[tuple[str, int]] = []
    added_policies: list[int] = []
    backup_directory = ""
    target = ""
    try:
        brain, _brain_auth = connect_node(
            code="brain", host=str(args.brain_ip), passwords_path=passwords
        )
        node_host = _node_host(brain)
        target = _target_address(node_host)
        target_hash = _address_sha256(target)
        report = _safe_report("APPLY" if args.apply else "PLAN", target_hash)
        node, _node_auth = connect_node(
            code=NODE_CODE, host=node_host, passwords_path=passwords
        )
        assigned = _run_remote(
            node,
            "ip -4 -o address show dev eth0 | awk '{print $4}' | cut -d/ -f1",
        ).splitlines()
        if target not in assigned:
            raise RuntimeError("owned endpoint address is not assigned to eth0")
        report["routing_capabilities"] = _routing_capabilities(node)

        sftp = node.open_sftp()
        profiles: dict[str, dict[str, Any]] = {}
        for profile, interface, port in PROFILES:
            path = f"{CONFIG_ROOT}/{interface}.conf"
            stat = sftp.stat(path)
            with sftp.open(path, "rb") as handle:
                raw = handle.read(64 * 1024 + 1)
            next_raw, needs_update = _updated_config(raw, interface, port, target)
            original[interface] = (raw, stat.st_mode & 0o777)
            updated[interface] = next_raw
            present = _rule_present(node, interface, port, target)
            managed_count = _managed_rule_count(node, interface)
            if present != (managed_count == 1):
                raise RuntimeError(
                    "conflicting live owned AWG reply-source rule exists"
                )
            initially_present[interface] = present
            rule_packets, rule_bytes = _managed_rule_counters(node, interface)
            policy = _policy_state(node, port, target)
            service = f"pokrov-awg-lab@{interface}.service"
            active = _run_remote(node, f"systemctl is-active {service}") == "active"
            listen_port = _run_remote(
                node, f"/usr/local/bin/awg show {interface} listen-port"
            )
            profiles[profile] = {
                "configuration_update_required": needs_update,
                "live_rule_present": present,
                "managed_live_rule_count": managed_count,
                "live_rule_packet_count": rule_packets,
                "live_rule_byte_count": rule_bytes,
                **policy,
                "service_active": active,
                "listen_port_matches": listen_port == str(port),
            }
        report["profiles"] = profiles
        report["preconditions_ok"] = (
            all(
                state["service_active"]
                and state["listen_port_matches"]
                and not state["policy_conflict"]
                for state in profiles.values()
            )
            and all(
                bool(value)
                for key, value in report["routing_capabilities"].items()
                if key != "main_default_route_count"
            )
            and report["routing_capabilities"]["main_default_route_count"] == 1
        )
        if not report["preconditions_ok"]:
            raise RuntimeError("owned AWG service precondition failed")

        if not args.apply:
            report["apply_guard"] = {
                "confirm_node": NODE_CODE,
                "confirm_target_address_sha256": target_hash,
            }
            report["ok"] = True
            print(json.dumps(report, sort_keys=True))
            return 0

        if (
            args.confirm_node != NODE_CODE
            or args.confirm_target_address_sha256.lower() != target_hash
        ):
            raise RuntimeError("APPLY confirmation does not match PLAN")

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup_directory = f"{BACKUP_ROOT}/{stamp}"
        _run_remote(node, f"install -d -m 0700 {backup_directory}")
        for _profile, interface, _port in PROFILES:
            path = f"{CONFIG_ROOT}/{interface}.conf"
            _run_remote(
                node,
                f"cp --preserve=mode,ownership,timestamps {path} {backup_directory}/{interface}.conf",
            )
        report["backup_created"] = True

        for _profile, interface, _port in PROFILES:
            path = f"{CONFIG_ROOT}/{interface}.conf"
            _sftp_write(sftp, path, updated[interface], original[interface][1])
        for _profile, interface, port in PROFILES:
            if not initially_present[interface]:
                _run_remote(node, _rule(interface, port, target, "-I"))
                added_rules.append((interface, port))
            if not profiles[_profile]["policy_rule_present"]:
                apply_policy, _cleanup_policy = _policy_commands(port, target)
                added_policies.append(port)
                _run_remote(node, apply_policy)

        for profile, interface, port in PROFILES:
            path = f"{CONFIG_ROOT}/{interface}.conf"
            with sftp.open(path, "rb") as handle:
                readback = handle.read(64 * 1024 + 1)
            expected, _changed = _updated_config(readback, interface, port, target)
            config_matches = expected == readback
            live_present = _rule_present(node, interface, port, target)
            managed_count = _managed_rule_count(node, interface)
            policy = _policy_state(node, port, target)
            service = f"pokrov-awg-lab@{interface}.service"
            active = _run_remote(node, f"systemctl is-active {service}") == "active"
            profiles[profile].update(
                {
                    "configuration_matches": config_matches,
                    "live_rule_present": live_present,
                    "managed_live_rule_count": managed_count,
                    **policy,
                    "service_active": active,
                }
            )
        if not all(
            state.get("configuration_matches")
            and state.get("live_rule_present")
            and state.get("policy_rule_present")
            and state.get("policy_route_present")
            and not state.get("policy_conflict")
            and state.get("service_active")
            for state in profiles.values()
        ):
            raise RuntimeError("owned AWG reply-source APPLY readback failed")
        if args.cycle_services:
            for _profile, interface, _port in PROFILES:
                service = f"pokrov-awg-lab@{interface}.service"
                _run_remote(node, f"systemctl restart {service}", timeout=120)
            for profile, interface, port in PROFILES:
                service = f"pokrov-awg-lab@{interface}.service"
                post_cycle_ok = (
                    _run_remote(node, f"systemctl is-active {service}") == "active"
                    and _rule_present(node, interface, port, target)
                    and bool(_policy_state(node, port, target)["policy_rule_present"])
                    and bool(_policy_state(node, port, target)["policy_route_present"])
                )
                profiles[profile]["post_cycle_readback_ok"] = post_cycle_ok
            report["service_cycle_pass"] = all(
                state.get("post_cycle_readback_ok") for state in profiles.values()
            )
            if not report["service_cycle_pass"]:
                raise RuntimeError("owned AWG service-cycle readback failed")
        report["applied"] = True
        report["rollback_required"] = False
        report["ok"] = True
        print(json.dumps(report, sort_keys=True))
        return 0
    except Exception as exc:
        rollback_ok = True
        if args.apply and node is not None:
            for port in reversed(added_policies):
                try:
                    _apply_policy, cleanup_policy = _policy_commands(port, target)
                    _run_remote(node, cleanup_policy)
                except Exception:
                    rollback_ok = False
            for interface, port in reversed(added_rules):
                try:
                    _run_remote(node, _rule(interface, port, target, "-D"))
                except Exception:
                    rollback_ok = False
            if backup_directory:
                for _profile, interface, _port in PROFILES:
                    try:
                        _run_remote(
                            node,
                            f"cp --preserve=mode,ownership,timestamps {backup_directory}/{interface}.conf {CONFIG_ROOT}/{interface}.conf",
                        )
                    except Exception:
                        rollback_ok = False
                for _profile, interface, port in PROFILES:
                    try:
                        service = f"pokrov-awg-lab@{interface}.service"
                        _run_remote(node, f"systemctl restart {service}", timeout=120)
                        rollback_ok = rollback_ok and (
                            _run_remote(node, f"systemctl is-active {service}")
                            == "active"
                            and _run_remote(
                                node,
                                f"/usr/local/bin/awg show {interface} listen-port",
                            )
                            == str(port)
                        )
                    except Exception:
                        rollback_ok = False
        if not report:
            report = _safe_report("APPLY" if args.apply else "PLAN", "")
        report.update(
            {
                "ok": False,
                "error_class": type(exc).__name__,
                "rollback_attempted": bool(args.apply and backup_directory),
                "rollback_ok": rollback_ok,
            }
        )
        print(json.dumps(report, sort_keys=True))
        return 1
    finally:
        for raw, _mode in original.values():
            if isinstance(raw, bytearray):
                raw[:] = b"\0" * len(raw)
        for raw in updated.values():
            if isinstance(raw, bytearray):
                raw[:] = b"\0" * len(raw)
        if sftp is not None:
            sftp.close()
        if node is not None:
            node.close()
        if brain is not None:
            brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
