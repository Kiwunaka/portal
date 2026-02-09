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

print("=== TEMPLATES MIGRATION ===\n")

migrations = [
    ("templates table", '''CREATE TABLE IF NOT EXISTS templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key VARCHAR(50) UNIQUE,
        text VARCHAR(2000),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );'''),
    ("templates index", 'CREATE INDEX IF NOT EXISTS ix_templates_key ON templates(key);'),
]

for name, sql in migrations:
    cmd = f'sqlite3 /root/portal_bot/portal.db "{sql}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.read().decode()
    if err and "already exists" not in err.lower():
        print(f"[FAIL] {name}: {err}")
    else:
        print(f"[OK] {name}")

print("\n[DONE] Templates table created!")
client.close()
