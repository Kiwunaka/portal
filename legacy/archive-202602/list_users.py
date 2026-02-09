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

print("=== Все юзеры в БД ===\n")
stdin, stdout, stderr = c.exec_command('sqlite3 -header -column /root/portal_bot/portal.db "SELECT tg_id, username, sub_type, is_active FROM users ORDER BY created_at;"')
print(stdout.read().decode())

c.close()
