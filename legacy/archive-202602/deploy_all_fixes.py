import os
import posixpath
import sys
import time
from pathlib import Path

import paramiko


sys.stdout.reconfigure(encoding="utf-8")

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
port = int(os.getenv("SSH_PORT", "22"))
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")


ROOT = Path(__file__).resolve().parent
LOCAL_PORTAL = ROOT / "portal_bot"
LOCAL_WEBAPP_DIST = ROOT / "webapp" / "dist"
LOCAL_WEBAPP_LEGACY = ROOT / "webapp" / "legacy_index.html"

REMOTE_PORTAL = "/root/portal_bot"
REMOTE_WEBAPP = "/var/www/html/webapp"
REMOTE_SERVICE = "/etc/systemd/system/portal-api.service"


SERVICE_CONTENT = """[Unit]
Description=Portal Bot API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/portal_bot
ExecStart=/root/portal_bot/venv/bin/python -m uvicorn api:app --host 0.0.0.0 --port 2096 --ssl-keyfile /root/portal_bot/certs/privkey.pem --ssl-certfile /root/portal_bot/certs/fullchain.pem
Restart=always
RestartSec=5
Environment=PATH=/usr/bin:/usr/local/bin

[Install]
WantedBy=multi-user.target
"""


def _sftp_mkdir_p(sftp: paramiko.SFTPClient, remote_dir: str) -> None:
    parts: list[str] = []
    cur = remote_dir
    while cur not in {"", "/"}:
        parts.append(cur)
        cur = posixpath.dirname(cur)
    for d in reversed(parts):
        try:
            sftp.stat(d)
        except IOError:
            try:
                sftp.mkdir(d)
            except IOError:
                pass


def _sftp_put_file(sftp: paramiko.SFTPClient, local_path: Path, remote_path: str) -> None:
    _sftp_mkdir_p(sftp, posixpath.dirname(remote_path))
    sftp.put(str(local_path), remote_path)


def _sftp_put_text(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    _sftp_mkdir_p(sftp, posixpath.dirname(remote_path))
    with sftp.file(remote_path, "w") as f:
        f.write(content)


def _upload_dir_recursive(sftp: paramiko.SFTPClient, local_dir: Path, remote_dir: str) -> None:
    for p in local_dir.rglob("*"):
        rel = p.relative_to(local_dir).as_posix()
        rp = f"{remote_dir.rstrip('/')}/{rel}"
        if p.is_dir():
            _sftp_mkdir_p(sftp, rp)
        else:
            _sftp_put_file(sftp, p, rp)


def deploy() -> None:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, port=port, username=username, password=password, timeout=30)

        # Ensure remote dirs.
        for cmd in [f"mkdir -p {REMOTE_PORTAL}", f"mkdir -p {REMOTE_WEBAPP}"]:
            client.exec_command(cmd, timeout=30)

        sftp = client.open_sftp()

        print("Uploading portal_bot/*.py ...")
        for p in sorted(LOCAL_PORTAL.glob("*.py")):
            _sftp_put_file(sftp, p, f"{REMOTE_PORTAL}/{p.name}")
        print("portal_bot uploaded")

        # Upload requirements + .env if present.
        req = LOCAL_PORTAL / "requirements.txt"
        env = LOCAL_PORTAL / ".env"
        if req.exists():
            _sftp_put_file(sftp, req, f"{REMOTE_PORTAL}/requirements.txt")
        if env.exists():
            _sftp_put_file(sftp, env, f"{REMOTE_PORTAL}/.env")

        # Upload helper scripts (optional).
        sync_clients = LOCAL_PORTAL / "sync_clients.py"
        if sync_clients.exists():
            _sftp_put_file(sftp, sync_clients, f"{REMOTE_PORTAL}/sync_clients.py")

        extract_local = ROOT / "extract_certs_remote.py"
        if extract_local.exists():
            _sftp_put_file(sftp, extract_local, f"{REMOTE_PORTAL}/extract_certs_remote.py")

        print("Uploading portal-api.service ...")
        _sftp_put_text(sftp, REMOTE_SERVICE, SERVICE_CONTENT)

        # Upload WebApp build output (preferred) or legacy file.
        if LOCAL_WEBAPP_DIST.exists() and (LOCAL_WEBAPP_DIST / "index.html").exists():
            print("Uploading webapp/dist ...")
            # Remove old assets to avoid stale files.
            client.exec_command(f"rm -rf {REMOTE_WEBAPP}/assets", timeout=60)
            _upload_dir_recursive(sftp, LOCAL_WEBAPP_DIST, REMOTE_WEBAPP)
            print("webapp dist uploaded")
        elif LOCAL_WEBAPP_LEGACY.exists():
            print("WARNING: webapp/dist not found; uploading legacy WebApp as index.html")
            _sftp_put_file(sftp, LOCAL_WEBAPP_LEGACY, f"{REMOTE_WEBAPP}/index.html")
        else:
            print("WARNING: WebApp not uploaded (no dist/legacy file found)")

        sftp.close()

        # Best-effort cert extraction.
        if extract_local.exists():
            print("Extracting SSL certificates ...")
            client.exec_command(f"python3 {REMOTE_PORTAL}/extract_certs_remote.py", timeout=120)

        print("Installing Python dependencies ...")
        install_cmd = f"cd {REMOTE_PORTAL} && (test -d venv || python3 -m venv venv) && . venv/bin/activate && pip install -r requirements.txt"
        stdin, stdout, stderr = client.exec_command(install_cmd, timeout=600)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            print(f"pip install warning/error: {stderr.read().decode(errors='replace')}")

        print("Restarting services ...")
        client.exec_command("systemctl daemon-reload", timeout=30)
        client.exec_command("systemctl stop portal-bot", timeout=30)
        time.sleep(2)
        client.exec_command("pkill -9 -f bot.py || true", timeout=10)
        client.exec_command("systemctl start portal-bot", timeout=30)
        client.exec_command("systemctl restart portal-api", timeout=30)

        # Quick smoke import (does not validate runtime config).
        smoke = f"cd {REMOTE_PORTAL} && . venv/bin/activate && python -c \"import api; import bot; print('import_ok')\""
        client.exec_command(smoke, timeout=60)

        time.sleep(2)
        stdin, stdout, stderr = client.exec_command("systemctl is-active portal-bot && systemctl is-active portal-api", timeout=30)
        status_output = stdout.read().decode().strip()
        print(f"Status output:\n{status_output}")

        if "active" in status_output:
            print("Deployment complete! Services are active.")
            print("Reminder: sync existing users if needed:")
            print("python3 /root/portal_bot/sync_clients.py")
        else:
            print("Services might not be active. Checking logs...")
            stdin, stdout, stderr = client.exec_command("journalctl -u portal-bot -n 20 --no-pager", timeout=30)
            print(f"Bot Logs:\n{stdout.read().decode(errors='replace')}")
            stdin, stdout, stderr = client.exec_command("journalctl -u portal-api -n 50 --no-pager", timeout=30)
            print(f"API Logs:\n{stdout.read().decode(errors='replace')}")

        print("Recent API Logs:")
        stdin, stdout, stderr = client.exec_command("journalctl -u portal-api -n 30 --no-pager", timeout=30)
        print(stdout.read().decode(errors="replace"))

    except Exception as e:
        print(f"Deployment failed: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    deploy()

