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

migrations = [
    # PromoCode table
    ("promo_codes table", '''CREATE TABLE IF NOT EXISTS promo_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code VARCHAR(20) UNIQUE,
        promo_type VARCHAR(10),
        value INTEGER,
        uses_left INTEGER,
        expires_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );'''),
    ("promo_codes index", 'CREATE INDEX IF NOT EXISTS ix_promo_codes_code ON promo_codes(code);'),
    
    # PromoUsage table
    ("promo_usage table", '''CREATE TABLE IF NOT EXISTS promo_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id BIGINT,
        promo_code VARCHAR(20),
        used_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );'''),
    ("promo_usage index", 'CREATE INDEX IF NOT EXISTS ix_promo_usage_tg_id ON promo_usage(tg_id);'),
]

for name, sql in migrations:
    cmd = f'sqlite3 /root/portal_bot/portal.db "{sql}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.read().decode()
    if err and "already exists" not in err.lower():
        print(f"[FAIL] {name}: {err}")
    else:
        print(f"[OK] {name}")

print("\n[DONE] Admin migrations complete!")
client.close()
