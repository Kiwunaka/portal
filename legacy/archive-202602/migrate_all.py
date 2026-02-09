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
    # User table new columns
    ("users.last_wheel_spin", 'ALTER TABLE users ADD COLUMN last_wheel_spin DATETIME;'),
    ("users.streak_months", 'ALTER TABLE users ADD COLUMN streak_months INTEGER DEFAULT 0;'),
    ("users.streak_last_check", 'ALTER TABLE users ADD COLUMN streak_last_check DATETIME;'),
    
    # Achievements table
    ("achievements table", '''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id BIGINT,
        achievement_id VARCHAR(50),
        unlocked_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );'''),
    ("achievements index", 'CREATE INDEX IF NOT EXISTS ix_achievements_tg_id ON achievements(tg_id);'),
    
    # Gift cards table
    ("gift_cards table", '''CREATE TABLE IF NOT EXISTS gift_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code VARCHAR(14) UNIQUE,
        card_type VARCHAR(20),
        created_by BIGINT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        redeemed_by BIGINT,
        redeemed_at DATETIME
    );'''),
    ("gift_cards index", 'CREATE INDEX IF NOT EXISTS ix_gift_cards_code ON gift_cards(code);'),
    
    # Reviews table
    ("reviews table", '''CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id BIGINT,
        username VARCHAR(100),
        rating INTEGER,
        text VARCHAR(500),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_featured BOOLEAN DEFAULT 0
    );'''),
    ("reviews index", 'CREATE INDEX IF NOT EXISTS ix_reviews_tg_id ON reviews(tg_id);'),
]

for name, sql in migrations:
    cmd = f'sqlite3 /root/portal_bot/portal.db "{sql}"'
    stdin, stdout, stderr = client.exec_command(cmd)
    err = stderr.read().decode()
    if err and "duplicate column" not in err.lower() and "already exists" not in err.lower():
        print(f"[FAIL] {name}: {err}")
    else:
        print(f"[OK] {name}")

# Verify
print("\nChecking database structure...")
stdin, stdout, stderr = client.exec_command('sqlite3 /root/portal_bot/portal.db ".tables"')
print("Tables:", stdout.read().decode().strip())

stdin, stdout, stderr = client.exec_command('sqlite3 /root/portal_bot/portal.db "PRAGMA table_info(users);"')
print("\nUsers columns:")
for line in stdout.read().decode().strip().split('\n')[-5:]:  # Last 5 columns
    print(f"  {line}")

client.close()
print("\n[DONE] Migration complete!")
