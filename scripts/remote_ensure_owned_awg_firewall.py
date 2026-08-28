from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from node_access import DEFAULT_PASSWORDS, connect_node
from remote_activate_owned_awg_labs import _node_host


NODE_CODE = "de"
OWNED_AWG_PORTS = {
    "awg2_lab": 4500,
    "awg31_lab": 3478,
}


class FirewallError(RuntimeError):
    pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan or apply the narrow UFW rules required by the owned AWG labs."
    )
    parser.add_argument("--brain-ip", default="82.21.114.104")
    parser.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    parser.add_argument("--known-hosts", required=True)
    parser.add_argument("--confirm-node", default="")
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def _run_remote(client: Any, command: str) -> str:
    _stdin, stdout, stderr = client.exec_command(command, timeout=30)
    code = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", "replace")
    stderr.read()
    if code != 0:
        raise FirewallError("remote firewall command failed")
    return output


def _audit(client: Any) -> dict[str, Any]:
    status = _run_remote(client, "ufw status")
    active = any(line.strip().lower() == "status: active" for line in status.splitlines())
    ports: dict[str, dict[str, Any]] = {}
    for profile, port in OWNED_AWG_PORTS.items():
        matches = [line.lower() for line in status.splitlines() if str(port) in line]
        ports[profile] = {
            "port": port,
            "allow_present": any("allow" in line and "udp" in line for line in matches),
            "deny_present": any(
                marker in line
                for line in matches
                for marker in ("deny", "reject", "limit")
            ),
            "matching_rule_count": len(matches),
        }
    return {
        "ufw_active": active,
        "ports": ports,
        "all_owned_awg_udp_allowed": active
        and all(
            item["allow_present"] and not item["deny_present"]
            for item in ports.values()
        ),
    }


def _apply(client: Any) -> None:
    if not _audit(client)["ufw_active"]:
        raise FirewallError("UFW is not active on the owned AWG node")
    for profile, port in OWNED_AWG_PORTS.items():
        comment = f"POKROV owned {profile}"
        _run_remote(client, f"ufw allow {port}/udp comment '{comment}'")


def main() -> int:
    args = _parse_args()
    known_hosts = Path(args.known_hosts).resolve()
    passwords = Path(args.passwords).resolve()
    if not known_hosts.is_file() or not passwords.is_file():
        raise SystemExit("SSH trust or authentication input is missing")
    os.environ["POKROV_SSH_KNOWN_HOSTS"] = str(known_hosts)

    brain, _brain_auth = connect_node(
        code="brain",
        host=str(args.brain_ip),
        passwords_path=passwords,
    )
    node = None
    try:
        node = connect_node(
            code=NODE_CODE,
            host=_node_host(brain),
            passwords_path=passwords,
        )[0]
        before = _audit(node)
        report: dict[str, Any] = {
            "schema_version": "pokrov-owned-awg-firewall-v1",
            "mode": "APPLY" if args.apply else "PLAN",
            "node_code": NODE_CODE,
            "before": before,
            "raw_addresses_returned": False,
        }
        if args.apply:
            if str(args.confirm_node).strip().lower() != NODE_CODE:
                raise FirewallError("--confirm-node mismatch")
            _apply(node)
            report["after"] = _audit(node)
            if not report["after"]["all_owned_awg_udp_allowed"]:
                raise FirewallError("owned AWG UDP firewall readback failed")
        report["ok"] = bool(
            report.get("after", before)["all_owned_awg_udp_allowed"]
        )
        print(json.dumps(report, sort_keys=True))
        return 0 if report["ok"] or not args.apply else 1
    except Exception as exc:
        print(
            json.dumps(
                {
                    "schema_version": "pokrov-owned-awg-firewall-v1",
                    "mode": "APPLY" if args.apply else "PLAN",
                    "node_code": NODE_CODE,
                    "ok": False,
                    "error_type": type(exc).__name__,
                    "raw_addresses_returned": False,
                },
                sort_keys=True,
            )
        )
        return 1
    finally:
        if node is not None:
            node.close()
        brain.close()


if __name__ == "__main__":
    raise SystemExit(main())
