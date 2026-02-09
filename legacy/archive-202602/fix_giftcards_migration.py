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

# Create gift_cards table
cmd = '''sqlite3 /root/portal_bot/portal.db "CREATE TABLE IF NOT EXISTS gift_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(14) UNIQUE,
    card_type VARCHAR(20),
    created_by BIGINT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    redeemed_by BIGINT,
    redeemed_at DATETIME
);"'''

stdin, stdout, stderr = client.exec_command(cmd)
err = stderr.read().decode()
if err:
    print(f"stderr: {err}")
else:
    print("gift_cards table created")

# Create index
stdin, stdout, stderr = client.exec_command('sqlite3 /root/portal_bot/portal.db "CREATE INDEX IF NOT EXISTS ix_gift_cards_code ON gift_cards(code);"')
print("Index created")

client.close()
print("Done!")
