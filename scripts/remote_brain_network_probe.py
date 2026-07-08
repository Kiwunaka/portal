from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import paramiko
from ssh_host_keys import configure_ssh_host_key_policy

from node_inventory import DEFAULT_INVENTORY, inventory_ipv4_map


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"


def _parse_inventory(path: Path) -> dict[str, str]:
    out = inventory_ipv4_map(path)
    if not out:
        raise SystemExit(f"Failed to parse inventory: {path}")
    return out


def _parse_brain_password(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" not in ln:
            continue
        for j in range(i + 1, min(i + 30, len(lines))):
            v = lines[j].strip()
            if v and not v.startswith("ssh-ed25519 "):
                return v
    return ""


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def main() -> int:
    ap = argparse.ArgumentParser(description="Probe worker-node ports from brain node.")
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--brain-ip", default="", help="Override brain IP (optional)")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--ports", default="443,8443,29374")
    args = ap.parse_args()

    inv = _parse_inventory(Path(args.inventory))
    brain_ip = (args.brain_ip or "").strip() or inv.get("brain", "")
    if not brain_ip:
        raise SystemExit("Brain IP is missing.")

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_brain_password(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    ports = [int(p.strip()) for p in str(args.ports).split(",") if p.strip()]
    targets = {k: v for k, v in inv.items() if k != "brain"}

    ssh = paramiko.SSHClient()
    configure_ssh_host_key_policy(ssh)
    ssh.connect(
        brain_ip,
        port=args.ssh_port,
        username=args.ssh_user,
        password=pw,
        timeout=30,
        banner_timeout=30,
        auth_timeout=30,
    )
    try:
        report: dict[str, dict[str, str]] = {}
        for code, ip in targets.items():
            host_report: dict[str, str] = {"ip": ip}
            for port in ports:
                cmd = (
                    f"timeout 5 bash -lc 'cat < /dev/null > /dev/tcp/{ip}/{port}' "
                    f"&& echo open || echo closed"
                )
                _, out, _ = _run(ssh, cmd, timeout=15)
                host_report[f"port_{port}"] = (out.strip().splitlines()[-1] if out.strip() else "closed")
            report[code] = host_report

        print(json.dumps(report, indent=2))
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
