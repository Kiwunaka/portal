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

print("=== FIREWALL STATUS ===")
stdin, stdout, stderr = client.exec_command("ufw status")
print(stdout.read().decode())

print("\n=== IPTABLES FOR PORT 2096 ===")
stdin, stdout, stderr = client.exec_command("iptables -L -n | grep -E '2096|DROP|REJECT' | head -10")
print(stdout.read().decode())

print("\n=== OPENING PORT 2096 ===")
stdin, stdout, stderr = client.exec_command("ufw allow 2096/tcp")
print(stdout.read().decode())
print(stderr.read().decode())

print("\n=== UFW STATUS AFTER ===")
stdin, stdout, stderr = client.exec_command("ufw status | grep 2096")
print(stdout.read().decode())

print("\n=== X-UI LISTENING ===")
stdin, stdout, stderr = client.exec_command("ss -tlnp | grep 2096")
print(stdout.read().decode())

client.close()
print("Done!")
