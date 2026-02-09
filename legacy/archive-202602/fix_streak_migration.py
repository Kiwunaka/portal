import os
import paramiko

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, username=username, password=password, timeout=30)

# Add streak columns
commands = [
    'sqlite3 /root/portal_bot/portal.db "ALTER TABLE users ADD COLUMN streak_months INTEGER DEFAULT 0;"',
    'sqlite3 /root/portal_bot/portal.db "ALTER TABLE users ADD COLUMN streak_last_check DATETIME;"',
]

for cmd in commands:
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.read().decode()
    if err and "duplicate column" not in err.lower():
        print(f"stderr: {err}")
    else:
        print(f"OK: {cmd[:60]}...")

print("Columns added")
client.close()
