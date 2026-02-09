from __future__ import annotations

import argparse
import base64
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sqlite3


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ManualUser:
    tg_id: int
    email: str
    uuid: str


DEFAULT_MANUAL_USERS = [
    # Elderly / relatives (static UUIDs) - stored as negative tg_id to avoid collisions with real Telegram ids.
    ManualUser(tg_id=-10001, email="RODITELI", uuid="e396db00-b105-41f7-b671-bf26d1098494"),
    ManualUser(tg_id=-10002, email="User_1808391444", uuid="20dfd743-f430-438f-9149-ac53373b9c75"),
    ManualUser(tg_id=-10003, email="User_5187992322", uuid="8522a2fb-157f-4e8e-9898-75df19ff52d2"),
    ManualUser(tg_id=-10004, email="Admin", uuid="49a30dde-ac75-42fc-a29f-aa3bf32c2e2b"),
]


def _gen_token(nbytes: int = 32) -> str:
    # URL-safe, no padding.
    return base64.urlsafe_b64encode(secrets.token_bytes(nbytes)).decode("ascii").rstrip("=")


def main() -> int:
    ap = argparse.ArgumentParser(description="Add/update manual (non-Telegram) users into portal.db for subscription usage.")
    ap.add_argument("--db", default=str(REPO_ROOT / "portal.db.cluster.db"))
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"DB not found: {db}")

    now = datetime.now(timezone.utc).replace(microsecond=0)
    expiry = now + timedelta(days=int(args.days))

    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        for u in DEFAULT_MANUAL_USERS:
            # If this UUID is already present (user exists in portal DB), just extend/activate it.
            by_uuid = cur.execute("select tg_id, email, sub_token from users where uuid = ?", (u.uuid,)).fetchone()
            if by_uuid:
                tg_id_existing, email_existing, tok_existing = by_uuid
                sub_token = tok_existing or _gen_token()
                if args.dry_run:
                    continue
                cur.execute(
                    "update users set email=?, sub_type=coalesce(sub_type,'manual'), expiry_at=?, is_active=1, sub_token=? where tg_id=?",
                    (
                        u.email or email_existing,
                        expiry.isoformat(sep=" "),
                        sub_token,
                        tg_id_existing,
                    ),
                )
                continue

            # Upsert by tg_id (primary key).
            row = cur.execute("select tg_id, uuid, email, sub_token from users where tg_id = ?", (u.tg_id,)).fetchone()
            if row:
                # Keep existing token if present; otherwise create one.
                sub_token = row[3] or _gen_token()
                if args.dry_run:
                    continue
                cur.execute(
                    "update users set uuid=?, email=?, sub_type=?, created_at=coalesce(created_at, ?), expiry_at=?, is_active=1, sub_token=? where tg_id=?",
                    (
                        u.uuid,
                        u.email,
                        "manual",
                        now.isoformat(sep=" "),
                        expiry.isoformat(sep=" "),
                        sub_token,
                        u.tg_id,
                    ),
                )
            else:
                sub_token = _gen_token()
                if args.dry_run:
                    continue
                cur.execute(
                    """
                    insert into users
                      (tg_id, uuid, email, sub_type, created_at, expiry_at, is_active, stars_paid, total_gb, trial_used, username, referrer_id, referral_count, tos_accepted, first_purchase_done, referral_code, sub_token)
                    values
                      (?, ?, ?, ?, ?, ?, 1, 0, 0, 0, null, null, 0, 1, 1, null, ?)
                    """.strip(),
                    (
                        u.tg_id,
                        u.uuid,
                        u.email,
                        "manual",
                        now.isoformat(sep=" "),
                        expiry.isoformat(sep=" "),
                        sub_token,
                    ),
                )
        if not args.dry_run:
            con.commit()
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
