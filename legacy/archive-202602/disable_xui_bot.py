import os
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}...")
    client.connect(hostname, username=username, password=password, timeout=30)
    print("Connected.")

    # 1. Stop x-ui to release DB lock
    print("\nStopping x-ui...")
    client.exec_command("systemctl stop x-ui")
    
    # 2. Update DB manually using sqlite3
    # The DB is usually at /etc/x-ui/x-ui.db
    print("Updating x-ui database...")
    sql = "UPDATE settings SET value = '' WHERE key = 'tg_bot_token';"
    cmd = f"sqlite3 /etc/x-ui/x-ui.db \"{sql}\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    
    if err:
        print(f"Error updating DB: {err}")
    else:
        print("Database updated successfully.")

    # 3. Start x-ui
    print("Starting x-ui...")
    client.exec_command("systemctl start x-ui")
    import time
    time.sleep(3)
    
    # 4. Check status
    stdin, stdout, stderr = client.exec_command("systemctl status x-ui --no-pager")
    print("\n=== STATUS ===")
    print(stdout.read().decode())
    
    # 5. Check logs for conflicts (last 10 lines)
    print("\n=== LOGS (Should be clean) ===")
    stdin, stdout, stderr = client.exec_command("journalctl -u x-ui -n 10 --no-pager")
    print(stdout.read().decode())

    client.close()

except Exception as e:
    print(f"Error: {e}")
