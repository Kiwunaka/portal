#!/usr/bin/env python3
from __future__ import annotations

"""
Install per-IP Free limiter on a remote node via SSH.

Example:
  python scripts/remote_install_free_per_ip_limiter.py \
    --ip 1.2.3.4 --user root --password '***' \
    --port 8443 --rate-kbps 6250 --burst-kb 512
"""

import argparse
import os
import sys
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy

from node_inventory import DEFAULT_INVENTORY, inventory_ipv4_map


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"

try:
    # Avoid Windows cp1251 crashes when remote systemd output contains unicode bullets.
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def _run(ssh: paramiko.SSHClient, cmd: str, timeout: int = 300) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return stdout.channel.recv_exit_status(), out, err


def _parse_inventory(path: Path) -> dict[str, str]:
    out = inventory_ipv4_map(path)
    if not out:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return out


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Install per-IP limiter for Free inbound on remote node.")
    ap.add_argument("--ip", default="", help="Node IP (optional when --code + --inventory are used)")
    ap.add_argument("--code", default="pl", help="Node code from inventory (default: pl)")
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY), help="Inventory markdown path")
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS), help="Passwords file path")
    ap.add_argument("--user", default="root", help="SSH username")
    ap.add_argument("--password", default="", help="SSH password (optional, fallback to PASSWORDS.txt/env)")
    ap.add_argument("--ssh-port", type=int, default=29374, help="SSH port")
    ap.add_argument("--port", type=int, default=8443, help="Free inbound port")
    ap.add_argument("--rate-kbps", type=int, default=6250, help="Per-IP rate in KBytes/s (50 Mbps ~= 6250)")
    ap.add_argument("--burst-kb", type=int, default=512, help="Burst in KBytes")
    args = ap.parse_args()

    inv = _parse_inventory(Path(args.inventory))
    node_code = (args.code or "").strip().lower()
    ip = (args.ip or "").strip() or inv.get(node_code, "")
    if not ip:
        raise SystemExit(f"Node IP not found for code={node_code}. Use --ip or fix inventory.")

    pw = (args.password or "").strip()
    if not pw:
        env_name = f"NODE_PASS_{node_code.upper()}"
        pw = (os.getenv(env_name, "") or "").strip()
    if not pw:
        pw_map = _parse_passwords(Path(args.passwords))
        pw = pw_map.get(node_code, "")
    if not pw:
        raise SystemExit(f"Missing password for node={node_code}. Set --password or env NODE_PASS_{node_code.upper()}.")

    setup_local = REPO_ROOT / "infra" / "setup_free_per_ip_limiter.sh"
    install_local = REPO_ROOT / "infra" / "install_free_per_ip_limiter.sh"
    if not setup_local.exists() or not install_local.exists():
        raise SystemExit("Required infra scripts not found.")

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(
        hostname=ip,
        port=args.ssh_port,
        username=args.user,
        password=pw,
        timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    try:
        sftp = ssh.open_sftp()
        try:
            sftp.put(str(setup_local), "/root/setup_free_per_ip_limiter.sh")
            sftp.put(str(install_local), "/root/install_free_per_ip_limiter.sh")
        finally:
            sftp.close()

        code, out, err = _run(
            ssh,
            (
                "chmod +x /root/setup_free_per_ip_limiter.sh /root/install_free_per_ip_limiter.sh && "
                "command -v nft >/dev/null 2>&1 || (apt-get update -y && apt-get install -y nftables) && "
                f"PORT={int(args.port)} RATE_KBPS={int(args.rate_kbps)} BURST_KB={int(args.burst_kb)} "
                "/root/install_free_per_ip_limiter.sh"
            ),
            timeout=1200,
        )
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "remote install failed")

        print(f"node={node_code} ip={ip} status=OK")
        if out.strip():
            print(out.strip())
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
