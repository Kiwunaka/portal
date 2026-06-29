from __future__ import annotations

import argparse
import os
import re
import time
from pathlib import Path

import paramiko


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PASSWORDS = REPO_ROOT / "VPN NODE SSH KEYS" / "PASSWORDS.txt"
DEFAULT_INVENTORY = REPO_ROOT / "docs" / "08-node-inventory.md"


def _parse_passwords(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in raw.splitlines()]
    for i, ln in enumerate(lines):
        if "BRAINnode" in ln:
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


def _parse_inventory_ips(path: Path) -> dict[str, str]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    out: dict[str, str] = {}
    row_re = re.compile(r"^\|\s*`([^`]+)`\s*\|.*?\|\s*`?(\d{1,3}(?:\.\d{1,3}){3})`?\s*\|\s*$")
    for ln in raw.splitlines():
        m = row_re.match(ln.strip())
        if not m:
            continue
        code = m.group(1).strip().lower()
        ip = m.group(2).strip()
        out[code] = ip
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Set nodes.host to DNS or IPv4 values on the brain control-plane DB.")
    ap.add_argument("--brain-ip", required=True)
    ap.add_argument("--domain", required=True, help="root domain, e.g. pokrov.space")
    ap.add_argument("--mode", choices=["dns", "ip"], default="dns", help="dns: per-country hostnames; ip: force per-node IPv4 hosts")
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY), help="inventory markdown with node IPs (used in --mode ip)")
    ap.add_argument("--db", default="/root/portal_bot/portal.db")
    ap.add_argument("--include-brain", action="store_true", help="also set brain host to root domain")
    args = ap.parse_args()

    pw = os.getenv("NODE_PASS_BRAIN", "").strip() or _parse_passwords(Path(args.passwords))
    if not pw:
        raise SystemExit("Missing brain password.")

    domain = args.domain.strip().lower()
    if not domain:
        raise SystemExit("Missing --domain")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(args.brain_ip, port=args.ssh_port, username=args.ssh_user, password=pw, timeout=30, banner_timeout=30, auth_timeout=30)
    try:
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get update -y >/dev/null 2>&1 || true", timeout=600)
        _run(ssh, "DEBIAN_FRONTEND=noninteractive apt-get install -y sqlite3 >/dev/null 2>&1 || true", timeout=600)

        ts = time.strftime("%Y%m%d-%H%M%S")
        code, out, err = _run(ssh, f"cp {args.db} {args.db}.bak-hosts-{ts}", timeout=60)
        if code != 0:
            raise SystemExit(err.strip() or out.strip() or "DB backup failed")

        sql: list[str] = []
        if args.mode == "dns":
            sql = [
                f"update nodes set host='pl.{domain}' where code='pl';",
                f"update nodes set host='pl.{domain}' where code='pl_free';",
                f"update nodes set host='free.{domain}' where code='free';",
                f"update nodes set host='it.{domain}' where code='it';",
                f"update nodes set host='us.{domain}' where code='us';",
                f"update nodes set host='nl.{domain}' where code='nl';",
            ]
            if args.include_brain:
                sql.append(f"update nodes set host='{domain}' where code='brain';")
        else:
            inv = _parse_inventory_ips(Path(args.inventory))
            for code in ("pl", "it", "us", "free", "nl"):
                ip = (inv.get(code) or "").strip()
                if not ip:
                    raise SystemExit(f"Missing IPv4 for '{code}' in inventory: {args.inventory}")
                sql.append(f"update nodes set host='{ip}' where code='{code}';")
                if code == "pl":
                    sql.append(f"update nodes set host='{ip}' where code='pl_free';")
            if args.include_brain:
                b_ip = (inv.get("brain") or args.brain_ip).strip()
                sql.append(f"update nodes set host='{b_ip}' where code='brain';")

        joined = "BEGIN; " + " ".join(sql) + " COMMIT;"
        code, out, err = _run(ssh, f"sqlite3 {args.db} \"{joined}\"", timeout=30)
        if code != 0:
            raise SystemExit((out.strip() or err.strip()).strip())

        # Show effective hosts (safe to print).
        _, out, err = _run(ssh, f"sqlite3 {args.db} \"select code,host from nodes order by code;\"", timeout=30)
        print((out.strip() or err.strip()).strip())

        # portal-api reads DB on each request, but restart is cheap and makes it deterministic.
        _run(ssh, "systemctl restart portal-api >/dev/null 2>&1 || true", timeout=60)
        return 0
    finally:
        ssh.close()


if __name__ == "__main__":
    raise SystemExit(main())
