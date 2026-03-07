from __future__ import annotations

"""
Read-only drift report between PORTAL node source-of-truth and live node runtime.

The script does NOT mutate panels or xray. It connects over SSH, inspects the
configured inbound on each enabled node, and compares it with what PORTAL expects
from the `nodes` table.
"""

import argparse
import base64
import json
import sys
from pathlib import Path

import paramiko
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

from node_access import DEFAULT_PASSWORDS, connect_node


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL_DIR = REPO_ROOT / "portal_bot"
if str(PORTAL_DIR) not in sys.path:
    sys.path.insert(0, str(PORTAL_DIR))


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


def inspect_runtime_inbound(
    *,
    code: str,
    host: str,
    inbound_id: int,
    ssh_user: str,
    ssh_port: int,
    passwords_path: Path,
) -> dict:
    ssh, auth_method = connect_node(
        code=code,
        host=host,
        user=ssh_user,
        port=ssh_port,
        passwords_path=passwords_path,
    )
    try:
        sql = (
            "sqlite3 /etc/x-ui/x-ui.db "
            f"\"select id, port, protocol, stream_settings, remark, enable from inbounds where id={int(inbound_id)};\""
        )
        _, out, _err = _run(ssh, sql, timeout=30)
    finally:
        ssh.close()

    if not out.strip():
        return {"inspect_error": "inbound_not_found", "auth_method": auth_method}

    row = out.strip().split("|", 5)
    stream = {}
    try:
        stream = json.loads(row[3])
    except Exception:
        stream = {}
    reality = stream.get("realitySettings") or {}
    private_key = str(reality.get("privateKey") or "")
    return {
        "inspect_error": "",
        "auth_method": auth_method,
        "inbound_id": int(row[0]),
        "port": int(row[1]),
        "protocol": row[2],
        "remark": row[4],
        "enable": bool(int(row[5]) if len(row) > 5 else 1),
        "network": stream.get("network"),
        "security": stream.get("security"),
        "dest": reality.get("dest", ""),
        "server_names": reality.get("serverNames") or [],
        "short_ids": reality.get("shortIds") or [],
        "public_key": _derive_public_from_private(private_key) if private_key else "",
    }


def compare_node_runtime(node, inspected: dict) -> dict:
    expected_sni = str(getattr(node, "reality_sni", "") or "").strip()
    expected_sid = str(getattr(node, "reality_sid", "") or "").strip()
    expected_pbk = str(getattr(node, "reality_pbk", "") or "").strip()
    server_names = [str(x or "").strip() for x in inspected.get("server_names", [])]
    dest = str(inspected.get("dest", "") or "").strip()
    checks = {
        "inbound_present": not bool(inspected.get("inspect_error")),
        "enabled_match": bool(inspected.get("enable")) is True,
        "port_match": int(inspected.get("port") or 0) == int(getattr(node, "vless_port", 443) or 443),
        "protocol_match": str(inspected.get("protocol") or "") == "vless",
        "network_match": str(inspected.get("network") or "") == "tcp",
        "security_match": str(inspected.get("security") or "") == "reality",
        "sni_match": (not expected_sni) or (expected_sni in server_names) or dest.startswith(f"{expected_sni}:"),
        "sid_match": (not expected_sid) or (expected_sid in [str(x or "").strip() for x in inspected.get("short_ids", [])]),
        "pbk_match": (not expected_pbk) or (expected_pbk == str(inspected.get("public_key") or "")),
    }
    mismatches = [name for name, ok in checks.items() if not ok]
    return {
        "node_code": str(getattr(node, "code", "") or ""),
        "node_host": str(getattr(node, "host", "") or ""),
        "expected": {
            "inbound_id": int(getattr(node, "inbound_id", 0) or 0),
            "port": int(getattr(node, "vless_port", 443) or 443),
            "sni": expected_sni,
            "sid": expected_sid,
            "pbk": expected_pbk,
        },
        "runtime": inspected,
        "checks": checks,
        "status": "ok" if not mismatches else "drift",
        "mismatches": mismatches,
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser()
    ap.add_argument("--passwords", default=str(DEFAULT_PASSWORDS))
    ap.add_argument("--ssh-user", default="root")
    ap.add_argument("--ssh-port", type=int, default=29374)
    ap.add_argument("--only", default="", help="comma-separated node codes")
    ap.add_argument("--out", default="", help="write JSON result to path")
    args = ap.parse_args()

    from db import SessionLocal  # noqa: WPS433,E402
    from nodes_repo import enabled_nodes  # noqa: WPS433,E402

    only = {c.strip() for c in args.only.split(",") if c.strip()}
    session = SessionLocal()
    try:
        nodes = enabled_nodes(session)
    finally:
        session.close()

    if only:
        nodes = [n for n in nodes if n.code in only]

    results: list[dict] = []
    for node in nodes:
        try:
            inspected = inspect_runtime_inbound(
                code=node.code,
                host=node.host,
                inbound_id=node.inbound_id,
                ssh_user=args.ssh_user,
                ssh_port=args.ssh_port,
                passwords_path=Path(args.passwords),
            )
        except Exception as exc:
            inspected = {
                "inspect_error": str(exc)[:240],
                "auth_method": "",
            }
        results.append(compare_node_runtime(node, inspected))

    payload = {
        "summary": {
            "total": len(results),
            "ok": sum(1 for row in results if row["status"] == "ok"),
            "drift": sum(1 for row in results if row["status"] != "ok"),
        },
        "results": results,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
