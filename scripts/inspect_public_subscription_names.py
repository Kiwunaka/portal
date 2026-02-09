from __future__ import annotations

import argparse
import base64
import re
import sqlite3
import ssl
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        import sys

        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    ap = argparse.ArgumentParser(description="Fetch a subscription and print the display names (#fragment) for each line.")
    ap.add_argument("--db", default=str(REPO_ROOT / "portal.db.cluster.db"))
    ap.add_argument("--public-api-base", default="https://kiwunaka.space:2096")
    args = ap.parse_args()

    con = sqlite3.connect(str(Path(args.db)))
    try:
        tok = con.execute(
            "select sub_token from users where is_active=1 and sub_token is not null order by created_at asc limit 1"
        ).fetchone()[0]
    finally:
        con.close()

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    url = f"{args.public_api_base.rstrip('/')}/s8Kx2mP7qR4wT/{tok}"
    raw = urllib.request.urlopen(url, context=ctx, timeout=15).read().decode("utf-8", errors="replace")

    decoded = base64.b64decode(raw).decode("utf-8", errors="replace")
    names = []
    for ln in decoded.splitlines():
        m = re.search(r"#(.+)$", ln)
        if not m:
            continue
        names.append(urllib.parse.unquote(m.group(1)))
    print("\n".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
