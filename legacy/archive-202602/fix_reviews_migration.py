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

# Create reviews table
cmd = '''sqlite3 /root/portal_bot/portal.db "CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id BIGINT,
    username VARCHAR(100),
    rating INTEGER,
    text VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_featured BOOLEAN DEFAULT 0
);"'''

stdin, stdout, stderr = client.exec_command(cmd)
err = stderr.read().decode()
if err:
    print(f"stderr: {err}")
else:
    print("reviews table created")

# Create index
stdin, stdout, stderr = client.exec_command('sqlite3 /root/portal_bot/portal.db "CREATE INDEX IF NOT EXISTS ix_reviews_tg_id ON reviews(tg_id);"')
print("Index created")

client.close()
print("Done!")
