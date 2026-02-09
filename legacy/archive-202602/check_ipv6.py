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

    # Check IPv6
    print("\n=== NETWORK INTERFACES (IPv6) ===")
    stdin, stdout, stderr = client.exec_command("ip -6 addr show")
    print(stdout.read().decode())
    
    # Check if x-ui internal bot is enabled (by checking config - but it's in db usually)
    # We can infer from logs "Conflict: terminated..." that it IS enabled.

    client.close()

except Exception as e:
    print(f"Error: {e}")
