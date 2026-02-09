
import paramiko
import os

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
port = int(os.getenv("SSH_PORT", "22"))
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port=port, username=username, password=password, timeout=30)
    
    print("Checking content of haproxy.pem (first 5 lines):")
    stdin, stdout, stderr = client.exec_command("head -n 5 /root/certs_keep/ssl/haproxy.pem")
    print(stdout.read().decode())
    
    print("Searching for Caddy certs:")
    stdin, stdout, stderr = client.exec_command("find /root -name 'limit_info' -o -name 'certificates' -maxdepth 5")
    print(stdout.read().decode())
    
    stdin, stdout, stderr = client.exec_command("ls -F /etc/x-ui/")
    print("\nFiles in /etc/x-ui/:")
    print(stdout.read().decode())
    
    client.close()
except Exception as e:
    print(f"Error: {e}")
