
import paramiko
import sys
import os

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
port = int(os.getenv("SSH_PORT", "22"))
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

local_script = r"c:\Users\kiwun\Documents\ai\VPN\debug_inbound6.py"
remote_script = "/root/portal_bot/debug_inbound6.py"

def run():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, port=port, username=username, password=password)
        
        sftp = client.open_sftp()
        print("Uploading debug script...")
        sftp.put(local_script, remote_script)
        sftp.close()
        
        print("Running debug script...")
        stdin, stdout, stderr = client.exec_command(f"python3 {remote_script}")
        print("Output:")
        print(stdout.read().decode())
        print("Errors:")
        print(stderr.read().decode())
        
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run()
