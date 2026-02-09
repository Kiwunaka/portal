"""
Update x-ui inbound client `subId` values to match our control-plane `users.sub_token`.

Why:
- Some 3x-ui setups store a per-client `subId` used by subscription URLs.
- This script syncs x-ui.db inbound settings so clients can keep using a stable token.

Safety:
- No hardcoded tg_ids or tokens in this repo.
- Mapping is read from the server's `/root/portal_bot/portal.db`.
"""

from __future__ import annotations

import os
import json
import paramiko


SERVER = os.getenv("SSH_HOST", "")
PORT = int(os.getenv("SSH_PORT", "22"))
USER = os.getenv("SSH_USER", "root")
PASSWORD = os.getenv("SSH_PASS", "")
INBOUND_ID = int(os.getenv("INBOUND_ID", "4"))

PORTAL_DB = os.getenv("REMOTE_PORTAL_DB", "/root/portal_bot/portal.db")
XUI_DB = os.getenv("REMOTE_XUI_DB", "/etc/x-ui/x-ui.db")


def _require_env() -> None:
    if not SERVER or not PASSWORD:
        raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")


def _read_mapping(ssh: paramiko.SSHClient) -> dict[str, str]:
    """
    Returns {tg_id_str: sub_token}.
    """
    cmd = f"sqlite3 {PORTAL_DB} \"SELECT tg_id || '|' || sub_token FROM users WHERE sub_token IS NOT NULL;\""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    raw = stdout.read().decode(errors="replace")
    mapping: dict[str, str] = {}
    for line in raw.splitlines():
        if "|" not in line:
            continue
        tg_id, tok = line.split("|", 1)
        tg_id = tg_id.strip()
        tok = tok.strip()
        if not tg_id or not tok:
            continue
        mapping[tg_id] = tok
    return mapping


def main() -> None:
    _require_env()

    print("[*] Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SERVER, port=PORT, username=USER, password=PASSWORD)
    print("[+] Connected")

    try:
        print("[1/5] Reading mapping from portal.db ...")
        mapping = _read_mapping(ssh)
        print(f"    mapping rows: {len(mapping)}")
        if not mapping:
            print("    nothing to do (no sub_token rows)")
            return

        print("[2/5] Reading current inbound settings from x-ui.db ...")
        cmd = f"sqlite3 {XUI_DB} \"SELECT settings FROM inbounds WHERE id={INBOUND_ID};\""
        stdin, stdout, stderr = ssh.exec_command(cmd)
        settings_raw = stdout.read().decode(errors="replace").strip()
        if not settings_raw:
            print("    FAIL: could not read inbound settings")
            return

        settings = json.loads(settings_raw)
        clients = settings.get("clients", []) or []
        print(f"    inbound clients: {len(clients)}")

        print("[3/5] Updating clients (match by tgId) ...")
        updated = 0
        for c in clients:
            tg_id = str(c.get("tgId", "")).strip()
            if not tg_id:
                continue
            tok = mapping.get(tg_id)
            if not tok:
                continue
            if c.get("subId") == tok:
                continue
            c["subId"] = tok
            updated += 1
        print(f"    updated: {updated}")
        if updated == 0:
            print("    nothing to save")
            return

        print("[4/5] Writing updated settings to /tmp/new_settings.json ...")
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/tmp/new_settings.json", "w") as f:
                f.write(json.dumps(settings))
        finally:
            sftp.close()

        print("[5/5] Applying update via sqlite ...")
        update_script = f"""
import sqlite3
import json

db = sqlite3.connect("{XUI_DB}")
cur = db.cursor()
with open("/tmp/new_settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)
cur.execute("UPDATE inbounds SET settings=? WHERE id=?", (json.dumps(settings), {INBOUND_ID}))
db.commit()
db.close()
print("OK")
"""
        sftp = ssh.open_sftp()
        try:
            with sftp.file("/tmp/apply_update_xui.py", "w") as f:
                f.write(update_script)
        finally:
            sftp.close()

        stdin, stdout, stderr = ssh.exec_command("python3 /tmp/apply_update_xui.py")
        out = stdout.read().decode(errors="replace").strip()
        err = stderr.read().decode(errors="replace").strip()
        print(f"    result: {out or err}")

        print("Restarting x-ui ...")
        ssh.exec_command("systemctl restart x-ui")
        print("Done")
    finally:
        ssh.close()


if __name__ == "__main__":
    main()

