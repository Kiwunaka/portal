from __future__ import annotations

"""
Inspect VLESS Reality inbound settings on nodes via SSH (password auth).

Outputs a sanitized summary:
- protocol/port/network/security
- dest + serverNames
- shortId(s)
- derived public key (PBK) from stored privateKey (never prints privateKey)

This is useful to answer "what VLESS settings do we use" and to double-check
node_reality-*.json matches server state.
"""

import argparse
import base64
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import paramiko
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization


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


def _run(ssh: paramiko.SSHClient, cmd: str, *, timeout: int = 60) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    code = stdout.channel.recv_exit_status()
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    return code, out, err


def _b64url_nopad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _derive_public_from_private(priv_b64: str) -> str:
    pad = "=" * ((4 - (len(priv_b64) % 4)) % 4)
    priv_bytes = base64.urlsafe_b64decode(priv_b64 + pad)
    priv = x25519.X25519PrivateKey.from_private_bytes(priv_bytes)
    pub_bytes = priv.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return _b64url_nopad(pub_bytes)


def main() -> int:
    # Make stdout safe on Windows terminals (avoid cp1251 encode errors).
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", default=str(DEFAULT_INVENTORY))
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--only", default="pl,it,us", help="comma-separated node codes")
    ap.add_argument("--inbound-id", type=int, default=1, help="inbound id to inspect (default: 1)")
    args = ap.parse_args()

    nodes = _parse_inventory(Path(args.inventory))
    only = {c.strip() for c in args.only.split(",") if c.strip()}
    nodes = [n for n in nodes if n.code in only]
    pw_map = _parse_passwords(Path(args.passwords))

    results: list[dict] = []
    for n in nodes:
        pw = os.getenv(f"NODE_PASS_{n.code.upper()}", "").strip() or pw_map.get(n.code, "")
        if not pw:
            raise SystemExit(f"Missing password for node {n.code}")
        ssh = _ssh_connect(n.ip, user=args.ssh_user, port=args.ssh_port, password=pw)
        try:
            sql = (
                "sqlite3 /etc/x-ui/x-ui.db "
                f"\"select id, port, protocol, stream_settings, remark, enable from inbounds where id={int(args.inbound_id)};\""
            )
            code, out, err = _run(ssh, sql, timeout=30)
            if not out.strip():
                results.append({"code": n.code, "ip": n.ip, "error": "inbound_not_found"})
                continue
            row = out.strip().split("|", 5)
            inb_id = int(row[0])
            port = int(row[1])
            protocol = row[2]
            stream = row[3]
            remark = row[4]
            enable = int(row[5]) if len(row) > 5 else 1

            try:
                ss = json.loads(stream)
            except Exception:
                ss = {}
            sec = ss.get("security")
            net = ss.get("network")
            rs = ss.get("realitySettings") or {}
            dest = rs.get("dest", "")
            snis = rs.get("serverNames") or []
            short_ids = rs.get("shortIds") or []
            pvk = rs.get("privateKey") or ""
            pbk = _derive_public_from_private(str(pvk)) if pvk else ""

            results.append(
                {
                    "code": n.code,
                    "ip": n.ip,
                    "inbound_id": inb_id,
                    "remark": remark,
                    "enable": bool(enable),
                    "port": port,
                    "protocol": protocol,
                    "network": net,
                    "security": sec,
                    "dest": dest,
                    "server_names": snis,
                    "short_ids": short_ids,
                    "public_key": pbk,
                }
            )
        finally:
            ssh.close()
        time.sleep(0.2)

    # ensure ASCII output; avoid BOM/encoding surprises when redirected on Windows
    print(json.dumps({"results": results}, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
