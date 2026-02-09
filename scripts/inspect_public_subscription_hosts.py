from __future__ import annotations

import argparse
import base64
import re
import sqlite3
import ssl
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch a subscription from PUBLIC_API_BASE_URL and print unique hosts (no tokens printed).")
    ap.add_argument("--db", default=str(REPO_ROOT / "portal.db.cluster.db"))
    ap.add_argument("--public-api-base", default="https://kiwunaka.space:2096")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"DB not found: {db}")

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        row = cur.execute(
            "select sub_token from users where is_active=1 and sub_token is not null order by created_at asc limit 1"
        ).fetchone()
    finally:
        con.close()

    if not row or not row[0]:
        raise SystemExit("No active user with sub_token found in DB.")

    tok = row[0]
    url = f"{args.public_api_base.rstrip('/')}/s8Kx2mP7qR4wT/{tok}"

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    raw = urllib.request.urlopen(url, context=ctx, timeout=15).read().decode("utf-8", errors="replace")

    # If it's smart-client JSON, just extract "server" fields.
    if raw.lstrip().startswith("{"):
        hosts = set(re.findall(r"\"server\"\\s*:\\s*\"([^\"]+)\"", raw))
        print("\n".join(sorted(hosts)))
        return 0

    # Otherwise it's base64 of newline-separated vless:// links.
    try:
        decoded = base64.b64decode(raw).decode("utf-8", errors="replace")
    except Exception:
        decoded = raw

    hosts: set[str] = set()
    for ln in decoded.splitlines():
        m = re.search(r"@([^:/?#]+)", ln)
        if m:
            hosts.add(m.group(1))
    print("\n".join(sorted(hosts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

