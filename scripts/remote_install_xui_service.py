from __future__ import annotations

"""
Ensure 3x-ui (x-ui) has a systemd service installed and is running on nodes.

On some nodes the binary exists under /usr/local/x-ui/ but the unit file was not installed.
This script:
- copies /usr/local/x-ui/x-ui.service.debian -> /etc/systemd/system/x-ui.service (if missing)
- systemctl daemon-reload
- systemctl enable --now x-ui
"""

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy

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


def _parse_passwords(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    out: dict[str, str] = {}
    markers = {"brain": "BRAINnode", "us": "USnode", "pl": "PLnode", "it": "ITnode", "free": "Free Node"}
    for code, marker in markers.items():
        try:
            idx = next(i for i, ln in enumerate(lines) if marker in ln)
        except StopIteration:
            continue
        pw = ""
        for j in range(idx + 1, min(idx + 12, len(lines))):
            ln = lines[j]
            if not ln or ln.startswith("ssh-ed25519 "):
                continue
            pw = ln
            break
        if pw:
            out[code] = pw
    return out


def _ssh_connect(ip: str, *, user: str, port: int, password: str) -> paramiko.SSHClient:
    cli = paramiko.SSHClient()
    configure_ssh_host_key_policy(cli)
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 180) -> tuple[int, str, str]:
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
    args = ap.parse_args()

    nodes = _parse_inventory(Path(args.inventory))
    only = {c.strip() for c in args.only.split(",") if c.strip()}
    if only:
        nodes = [n for n in nodes if n.code in only]

    pw_map = _parse_passwords(Path(args.passwords))

    for n in nodes:
        pw = os.getenv(f"NODE_PASS_{n.code.upper()}", "").strip() or pw_map.get(n.code, "")
        if not pw:
            raise SystemExit(f"Missing password for node {n.code}")
        print(f"[{n.code}] ensure x-ui service ...")
        ssh = _ssh_connect(n.ip, user=args.ssh_user, port=args.ssh_port, password=pw)
        try:
            cmd = (
                "set -euo pipefail; "
                "test -x /usr/local/x-ui/x-ui; "
                "if [ ! -f /etc/systemd/system/x-ui.service ]; then "
                "  cp /usr/local/x-ui/x-ui.service.debian /etc/systemd/system/x-ui.service; "
                "  chmod 644 /etc/systemd/system/x-ui.service; "
                "fi; "
                "systemctl daemon-reload; "
                "systemctl enable x-ui >/dev/null 2>&1 || true; "
                "systemctl restart x-ui; "
                "systemctl is-active x-ui || true"
            )
            code, out, err = _run(ssh, f"bash -lc '{cmd}'", timeout=180)
            print((out.strip() or err.strip()).strip())
            # show panel port (best-effort)
            code, out, err = _run(ssh, "ss -tlnp | grep -E ':([0-9]+)\\b' | grep x-ui || true", timeout=60)
            if out.strip():
                print(out.strip())
        finally:
            ssh.close()
        time.sleep(0.2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

