import os

import paramiko


hostname = os.getenv("SSH_HOST", "")
port = int(os.getenv("SSH_PORT", "22"))
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

check_tg_id = os.getenv("CHECK_TG_ID", "").strip()
extra = [p.strip().lower() for p in os.getenv("CHECK_PATTERNS", "").split(",") if p.strip()]
default_kw = ["tariff", "traffic set", "setclient", "error", "exception"]
patterns = ([check_tg_id] if check_tg_id else []) + (extra or default_kw)

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port=port, username=username, password=password, timeout=30)

try:
    title = f"=== CHECKING LOGS ({check_tg_id}) ===" if check_tg_id else "=== CHECKING LOGS ==="
    print(title + "\n")

    stdin, stdout, stderr = client.exec_command('journalctl -u portal-bot --since="5 min ago" --no-pager')
    output = stdout.read().decode("utf-8", errors="replace")
    for line in output.splitlines():
        low = line.lower()
        if any(p and (p in low or p in line) for p in patterns):
            print(line)

    print("\n=== ALL RECENT LOGS ===\n")
    stdin, stdout, stderr = client.exec_command("journalctl -u portal-bot -n 30 --no-pager")
    log_content = stdout.read().decode("utf-8", errors="replace")
    print(log_content)
finally:
    client.close()

