"""
Server-side helper: ensure users have `sub_token` in /root/portal_bot/portal.db.

Notes:
- The bot already does lazy migration when building a subscription link.
- Use this script only if you want to pre-fill tokens for all existing users.
- This script does NOT print tokens (to avoid accidental leakage).

Environment:
- SSH_HOST, SSH_PASS (optionally SSH_PORT/SSH_USER)
- APPLY=1 to actually write changes (dry-run by default)
"""

from __future__ import annotations

import os
import paramiko


SERVER = os.getenv("SSH_HOST", "")
PORT = int(os.getenv("SSH_PORT", "22"))
USER = os.getenv("SSH_USER", "root")
PASSWORD = os.getenv("SSH_PASS", "")
APPLY = os.getenv("APPLY", "").strip() in {"1", "true", "yes", "y"}

DB_PATH = os.getenv("REMOTE_PORTAL_DB", "/root/portal_bot/portal.db")


def _require_env() -> None:
    if not SERVER or not PASSWORD:
        raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")


def main() -> None:
    _require_env()

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD)

    try:
        stdin, stdout, stderr = ssh.exec_command(
            f"sqlite3 {DB_PATH} \"SELECT COUNT(1) FROM users WHERE sub_token IS NULL OR TRIM(sub_token)='';\""
        )
        missing = int((stdout.read().decode(errors="replace").strip() or "0").splitlines()[-1])
        print(f"Missing sub_token rows: {missing}")

        if not APPLY:
            print("Dry-run. Set APPLY=1 to generate tokens for missing users.")
            return

        # Run token generation server-side to avoid tokens in local stdout.
        script = f"""
import secrets
import sqlite3

db = sqlite3.connect("{DB_PATH}")
cur = db.cursor()

cur.execute("ALTER TABLE users ADD COLUMN sub_token VARCHAR(64) UNIQUE;")
db.commit()

cur.execute("SELECT tg_id FROM users WHERE sub_token IS NULL OR TRIM(sub_token)=''")
rows = cur.fetchall()

updated = 0
for (tg_id,) in rows:
    tok = secrets.token_urlsafe(32)
    cur.execute("UPDATE users SET sub_token=? WHERE tg_id=?", (tok, int(tg_id)))
    updated += 1

db.commit()
db.close()
print(updated)
"""
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/tmp/fill_sub_tokens.py", "w") as f:
                f.write(script)
        finally:
            sftp.close()

        stdin, stdout, stderr = ssh.exec_command("python3 /tmp/fill_sub_tokens.py")
        out = stdout.read().decode(errors="replace").strip()
        err = stderr.read().decode(errors="replace").strip()
        if err and not out:
            print(f"ERROR: {err}")
            return
        print(f"Updated rows: {out}")
    finally:
        ssh.close()


if __name__ == "__main__":
    main()

