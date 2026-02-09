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
    
    # Check Caddy Service Status
    print("\n=== CADDY SERVICE STATUS ===")
    stdin, stdout, stderr = client.exec_command("systemctl status caddy --no-pager")
    print(stdout.read().decode())
    
    # Check Caddy Logs (Recent)
    print("\n=== RECENT CADDY LOGS ===")
    stdin, stdout, stderr = client.exec_command("journalctl -u caddy -n 50 --no-pager")
    print(stdout.read().decode())
    
    # Check Caddy Config (Caddyfile)
    print("\n=== CADDYFILE CONFIG ===")
    # Common locations for Caddyfile
    locations = ["/etc/caddy/Caddyfile", "/etc/Caddyfile", "/usr/local/etc/Caddyfile"]
    found = False
    for loc in locations:
        stdin, stdout, stderr = client.exec_command(f"ls {loc}")
        if not stderr.read():
            print(f"Found Caddyfile at {loc}")
            stdin, stdout, stderr = client.exec_command(f"cat {loc}")
            print(stdout.read().decode())
            found = True
            break
    if not found:
        print("Caddyfile not found in common locations.")

    client.close()

except Exception as e:
    print(f"Error: {e}")
