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

# Add last_wheel_spin column
cmd = 'sqlite3 /root/portal_bot/portal.db "ALTER TABLE users ADD COLUMN last_wheel_spin DATETIME;"'
stdin, stdout, stderr = client.exec_command(cmd)
print("stdout:", stdout.read().decode())
print("stderr:", stderr.read().decode())

# Restart bot
stdin, stdout, stderr = client.exec_command('systemctl restart portal-bot')
print("Bot restarted")

# Check status
stdin, stdout, stderr = client.exec_command('systemctl is-active portal-bot')
print("Bot status:", stdout.read().decode().strip())

client.close()
print("Done!")
