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
    client.connect(hostname, username=username, password=password, timeout=30)
    print("Connected to server")
    
    # Check x-ui status
    stdin, stdout, stderr = client.exec_command("systemctl is-active x-ui")
    status = stdout.read().decode().strip()
    print(f"x-ui status: {status}")
    
    if status != "active":
        print("Restarting x-ui...")
        stdin, stdout, stderr = client.exec_command("systemctl restart x-ui")
        stdout.read()
        import time
        time.sleep(3)
        stdin, stdout, stderr = client.exec_command("systemctl is-active x-ui")
        status = stdout.read().decode().strip()
        print(f"x-ui status after restart: {status}")
    
    # Check port
    stdin, stdout, stderr = client.exec_command("ss -tlnp | grep 2096")
    print(f"Port 2096: {stdout.read().decode()}")
    
    # Check bot and api
    stdin, stdout, stderr = client.exec_command("systemctl is-active portal-bot portal-api")
    print(f"Bot/API: {stdout.read().decode()}")
    
    client.close()
except Exception as e:
    print(f"Error: {e}")
