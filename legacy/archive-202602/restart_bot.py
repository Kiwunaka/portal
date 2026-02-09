import os
import paramiko
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
port = int(os.getenv("SSH_PORT", "22"))
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

def restart_bot():
    # Read files
    with open("portal_bot/bot.py", "r", encoding="utf-8") as f:
        bot_code = f.read()
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password)
    
    # Upload new code
    print("=== Uploading updated bot ===")
    sftp = client.open_sftp()
    with sftp.file("/root/portal_bot/bot.py", "wb") as f:
        f.write(bot_code.encode('utf-8'))
    sftp.close()
    
    # Restart
    print("=== Restarting portal-bot ===")
    client.exec_command("systemctl restart portal-bot")
    time.sleep(3)
    
    # Check status
    stdin, stdout, stderr = client.exec_command("systemctl status portal-bot --no-pager | head -12")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # Check logs
    stdin, stdout, stderr = client.exec_command("journalctl -u portal-bot -n 5 --no-pager")
    print("\n=== Logs ===")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    client.close()

if __name__ == "__main__":
    restart_bot()
