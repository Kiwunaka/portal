from __future__ import annotations

"""
Inspect 3x-ui/x-ui inbounds on each node via SSH (password or key auth).

This script is read-only. It helps confirm whether nodes are "empty"
and what inbound IDs/ports exist before configuring multi-node.
"""

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko

from node_access import connect_node
from node_inventory import DEFAULT_INVENTORY, read_inventory


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


@dataclass(frozen=True)
class Node:
    code: str
    ip: str


def _parse_inventory(path: Path) -> list[Node]:
    nodes = [Node(code=row.code, ip=row.ip) for row in read_inventory(path)]
    if not nodes:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return nodes


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--only", default="", help="comma-separated node codes")
    ap.add_argument("--out", default="", help="write JSON result to path")
    args = ap.parse_args()

    nodes = _parse_inventory(Path(args.inventory))
    only = {c.strip() for c in args.only.split(",") if c.strip()}
    if only:
        nodes = [n for n in nodes if n.code in only]

    results: list[dict] = []
    for n in nodes:
        print(f"[{n.code}] inspect {n.ip} ...")
        ssh, auth_method = connect_node(
            code=n.code,
            host=n.ip,
            user=args.ssh_user,
            port=args.ssh_port,
            passwords_path=Path(args.passwords),
        )
        try:
            # Check DB presence and list inbounds.
            facts: dict[str, object] = {"code": n.code, "ip": n.ip, "auth_method": auth_method}
            code, out, err = _run(
                ssh,
                "test -f /etc/x-ui/x-ui.db && echo HAS_DB || echo NO_DB",
                timeout=20,
            )
            facts["xui_db"] = out.strip().splitlines()[-1] if out.strip() else "unknown"

            code, out, err = _run(
                ssh,
                "sqlite3 /etc/x-ui/x-ui.db \"select id, port, protocol, enable from inbounds order by id;\" 2>/dev/null || true",
                timeout=30,
            )
            rows = []
            for line in out.splitlines():
                parts = line.split("|")
                if len(parts) != 4:
                    continue
                try:
                    rows.append(
                        {
                            "id": int(parts[0]),
                            "port": int(parts[1]),
                            "protocol": parts[2],
                            "enable": int(parts[3]),
                        }
                    )
                except Exception:
                    continue
            facts["inbounds"] = rows
            results.append(facts)
        finally:
            ssh.close()
        time.sleep(0.2)

    payload = {"results": results}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved: {args.out}")
    else:
        out_path = REPO_ROOT / f"node_inbounds-{time.strftime('%Y%m%d-%H%M%S')}.json"
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Saved: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
