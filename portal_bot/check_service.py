
import os
import paramiko

hostname = os.getenv("SSH_HOST", "")
port = int(os.getenv("SSH_PORT", "22"))
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

def check_service():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        
        # Cat the service file
        stdin, stdout, stderr = client.exec_command("cat /etc/systemd/system/portal-api.service")
        content = stdout.read().decode()
        print("\n--- portal-api.service ---\n")
        print(content)
        print("\n--------------------------\n")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    check_service()
