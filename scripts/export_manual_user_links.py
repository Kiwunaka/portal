from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import urllib.parse


REPO_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Export manual user subscription URLs into an untracked file.")
    ap.add_argument("--db", default=str(REPO_ROOT / "portal.db.cluster.db"))
    ap.add_argument("--domain", required=True)
    ap.add_argument("--port", type=int, default=2096)
    ap.add_argument("--out", default=str(REPO_ROOT / "VPN NODE SSH KEYS" / "MANUAL_USERS_URLS.txt"))
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"DB not found: {db}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        rows = cur.execute(
            "select tg_id,email,sub_token from users where tg_id < 0 order by tg_id",
        ).fetchall()
    finally:
        con.close()

    lines = []
    lines.append(f"# Manual users subscription URLs for {args.domain}:{args.port}")
    lines.append("# Treat as secrets.")
    lines.append("")
    for tg_id, email, sub_token in rows:
        if not sub_token:
            continue
        frag = urllib.parse.quote(str(email))
        url = f"https://{args.domain}:{int(args.port)}/s8Kx2mP7qR4wT/{sub_token}#{frag}"
        lines.append(f"{email} (tg_id={tg_id})")
        lines.append(url)
        lines.append("")

    out.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

