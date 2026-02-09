import os
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
host = os.getenv("SSH_HOST", "")
user = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
port = int(os.getenv("SSH_PORT", "22"))
if not host or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")
c.connect(host, port=port, username=user, password=password)

# Add referral_code column
print("Adding referral_code column...")
stdin, stdout, stderr = c.exec_command('sqlite3 /root/portal_bot/portal.db "ALTER TABLE users ADD COLUMN referral_code VARCHAR(10);"')
out = stdout.read().decode()
err = stderr.read().decode()
if err and "duplicate column" not in err.lower():
    print(f"Error: {err}")
else:
    print("OK")

# Add first_purchase_done column
print("Adding first_purchase_done column...")
stdin, stdout, stderr = c.exec_command('sqlite3 /root/portal_bot/portal.db "ALTER TABLE users ADD COLUMN first_purchase_done BOOLEAN DEFAULT 0;"')
out = stdout.read().decode()
err = stderr.read().decode()
if err and "duplicate column" not in err.lower():
    print(f"Error: {err}")
else:
    print("OK")

# Add sub_token column
print("Adding sub_token column...")
stdin, stdout, stderr = c.exec_command('sqlite3 /root/portal_bot/portal.db "ALTER TABLE users ADD COLUMN sub_token VARCHAR(64);"')
out = stdout.read().decode()
err = stderr.read().decode()
if err and "duplicate column" not in err.lower():
    print(f"Error: {err}")
else:
    print("OK")

# Verify columns
print("\nVerifying schema...")
stdin, stdout, stderr = c.exec_command('sqlite3 /root/portal_bot/portal.db ".schema users"')
print(stdout.read().decode())

# Restart bot
print("Restarting bot...")
stdin, stdout, stderr = c.exec_command('systemctl restart portal-bot')
stdout.read()
stdin, stdout, stderr = c.exec_command('systemctl is-active portal-bot')
print(f"Status: {stdout.read().decode().strip()}")

c.close()
print("Done!")
