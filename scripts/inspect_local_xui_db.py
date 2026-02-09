from __future__ import annotations

"""
Inspect a local x-ui/3x-ui SQLite DB file (read-only).

Use this for DB backups you copy into the repo for analysis. WARNING:
these DBs usually contain private Reality keys. This script never prints private keys.
"""

import argparse
import base64
import json
import sqlite3
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization


def _b64url_nopad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def _derive_public_from_private(priv_b64: str) -> str:
    pad = "=" * ((4 - (len(priv_b64) % 4)) % 4)
    priv_bytes = base64.urlsafe_b64decode(priv_b64 + pad)
    priv = x25519.X25519PrivateKey.from_private_bytes(priv_bytes)
    pub_bytes = priv.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    return _b64url_nopad(pub_bytes)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="x-ui.db", help="path to x-ui.db backup")
    args = ap.parse_args()

    p = Path(args.db)
    if not p.exists():
        raise SystemExit(f"DB not found: {p}")

    con = sqlite3.connect(str(p))
    try:
        cur = con.cursor()
        rows = cur.execute("select id, port, protocol, remark, enable, stream_settings from inbounds order by id").fetchall()
        out = []
        for inb_id, port, proto, remark, enable, stream_settings in rows:
            ss = {}
            try:
                ss = json.loads(stream_settings or "{}")
            except Exception:
                ss = {}
            rs = ss.get("realitySettings") or {}
            pvk = rs.get("privateKey") or ""
            pbk = _derive_public_from_private(str(pvk)) if pvk else ""
            out.append(
                {
                    "id": int(inb_id),
                    "port": int(port),
                    "protocol": proto,
                    "remark": remark,
                    "enable": bool(enable),
                    "network": ss.get("network"),
                    "security": ss.get("security"),
                    "dest": rs.get("dest"),
                    "server_names": rs.get("serverNames") or [],
                    "short_ids": rs.get("shortIds") or [],
                    "public_key": pbk,
                }
            )
        print(json.dumps({"inbounds": out}, indent=2, ensure_ascii=True))
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())

