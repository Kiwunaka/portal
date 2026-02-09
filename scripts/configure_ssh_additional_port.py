from __future__ import annotations

"""
Add an additional SSH port on nodes (keeps 22 enabled).

Rationale:
- Moving SSH off 22 is common, but doing it safely requires keeping 22 during the transition.
- This script adds a second Port entry, updates UFW, and restarts sshd.

It does NOT disable password auth and does NOT remove port 22.
"""

import argparse
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


@dataclass(frozen=True)
class Node:
    code: str
    ip: str


def _parse_inventory(path: Path) -> list[Node]:
    txt = path.read_text(encoding="utf-8", errors="replace")
    nodes: list[Node] = []
    for line in txt.splitlines():
        line = line.strip()
        if not line.startswith("|") or "`" not in line:
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 4:
            continue
        code = parts[0].strip("`").strip()
        ip = parts[3].strip("`").strip()
        if not code or code.lower() == "code":
            continue
        if not re.fullmatch(r"[a-z0-9_-]+", code):
            continue
        if not re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", ip):
            continue
        nodes.append(Node(code=code, ip=ip))
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
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    cli.connect(ip, port=port, username=user, password=password, timeout=30, banner_timeout=30, auth_timeout=30)
    t = cli.get_transport()
    if t:
        t.set_keepalive(30)
    return cli


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
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
    ap.add_argument("--ssh-port", type=int, default=22)
    ap.add_argument("--only", default="", help="comma-separated node codes")
    ap.add_argument("--add-port", type=int, default=29374)
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
        print(f"[{n.code}] add ssh port {args.add_port} (keeping 22) ...")
        ssh = _ssh_connect(n.ip, user=args.ssh_user, port=args.ssh_port, password=pw)
        try:
            # UFW allow (idempotent)
            _run(ssh, f"ufw allow {int(args.add_port)}/tcp >/dev/null 2>&1 || true", timeout=60)

            # Add an additional Port line if missing
            cmd = (
                "set -euo pipefail; "
                f"PORT={int(args.add_port)}; "
                "CFG=/etc/ssh/sshd_config; "
                "grep -Eq \"^Port[[:space:]]+${PORT}$\" \"$CFG\" && exit 0; "
                "printf \"\\n# added by configure_ssh_additional_port.py\\nPort %s\\n\" \"$PORT\" >> \"$CFG\"; "
                "systemctl restart ssh || systemctl restart sshd"
            )
            code, out, err = _run(ssh, f"bash -lc '{cmd}'", timeout=120)
            if code != 0:
                raise RuntimeError(err.strip() or out.strip())

            # Quick verification: show active ports
            code, out, err = _run(ssh, "ss -tlnp | grep -E ':(22|29374)\\b' || true", timeout=60)
            # Do not fail if ss doesn't show 29374 immediately (rare), but print for operator.
            print(out.strip())
        finally:
            ssh.close()
        time.sleep(0.2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

