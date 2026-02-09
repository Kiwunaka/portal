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

print("=== SETTING UP DAILY BACKUP ===\n")

# Upload backup script
backup_script = '''#!/bin/bash
# Daily backup script for portal_bot
# Runs at 3am via cron

BACKUP_DIR="/root/backups"
DB_PATH="/root/portal_bot/portal.db"
DATE=$(date +%Y-%m-%d_%H-%M)
KEEP_DAYS=7

mkdir -p $BACKUP_DIR
cp $DB_PATH "$BACKUP_DIR/portal_$DATE.db"
gzip "$BACKUP_DIR/portal_$DATE.db"
find $BACKUP_DIR -name "portal_*.db.gz" -mtime +$KEEP_DAYS -delete

echo "$(date): Backup done: portal_$DATE.db.gz" >> /var/log/portal_backup.log
'''

# Save script to server
stdin, stdout, stderr = client.exec_command(f"cat > /root/portal_bot/backup_db.sh << 'EOF'\n{backup_script}\nEOF")
stdout.read()
print("[OK] backup_db.sh uploaded")

# Make executable
stdin, stdout, stderr = client.exec_command("chmod +x /root/portal_bot/backup_db.sh")
stdout.read()
print("[OK] Made executable")

# Create backups directory
stdin, stdout, stderr = client.exec_command("mkdir -p /root/backups")
stdout.read()
print("[OK] /root/backups created")

# Add cron job (if not exists)
cron_job = "0 3 * * * /root/portal_bot/backup_db.sh"
stdin, stdout, stderr = client.exec_command(f'(crontab -l 2>/dev/null | grep -v backup_db.sh; echo "{cron_job}") | crontab -')
stdout.read()
print("[OK] Cron job added (daily at 3am)")

# Run first backup now
stdin, stdout, stderr = client.exec_command("/root/portal_bot/backup_db.sh")
print("[OK] First backup created")
print(stdout.read().decode())

# Verify
stdin, stdout, stderr = client.exec_command("ls -la /root/backups/")
print("\n=== BACKUPS ===")
print(stdout.read().decode())

stdin, stdout, stderr = client.exec_command("crontab -l | grep backup")
print("=== CRON ===")
print(stdout.read().decode())

client.close()
print("\n✅ Daily backup configured!")
