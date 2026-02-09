from __future__ import annotations

"""
Grant (or reset) subscription expiry for all users in a portal.db SQLite database.

This is used for global promos like "everyone gets 14 days".

Behavior:
- Sets is_active=1 for all users
- Sets expiry_at = now_utc + <days> for all users
- Does not modify sub_type, uuid, sub_token, or traffic limits
"""

import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="portal.db.cluster.db", help="path to portal sqlite DB")
    ap.add_argument("--days", type=int, default=14)
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"DB not found: {db}")

    now = datetime.now(timezone.utc)
    expiry = now + timedelta(days=int(args.days))
    # Use a stable string representation compatible with SQLAlchemy DATETIME in SQLite.
    expiry_str = expiry.replace(tzinfo=None).isoformat(sep=" ", timespec="seconds")

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        # Count before
        total = cur.execute("select count(*) from users").fetchone()[0]
        cur.execute("update users set is_active=1, expiry_at=?", (expiry_str,))
        con.commit()
        # Count after
        active = cur.execute("select count(*) from users where is_active=1").fetchone()[0]
        print(f"OK: users_total={total} users_active={active} expiry_at_utc={expiry_str}")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())

