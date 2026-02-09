
import os
import paramiko
import time

hostname = os.getenv("SSH_HOST", "")
port = int(os.getenv("SSH_PORT", "22"))
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

def debug_panel():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        
        print("\n--- Checking Port 8445 ---")
        stdin, stdout, stderr = client.exec_command("netstat -tulpn | grep 8445")
        print(stdout.read().decode())
        
        print("\n--- Querying Panel Inbounds from Localhost ---")
        # We use python on the server to query the internal API because it's easier than curl with cookies
        remote_script = """
import os
import json
import requests

PANEL_URL = os.getenv("PANEL_URL", "http://127.0.0.1:15739").rstrip("/")
PANEL_PATH = os.getenv("PANEL_PATH", "").strip("/")
if not PANEL_PATH:
    raise SystemExit("Set PANEL_PATH in the server environment")

USERNAME = os.getenv("PANEL_USER", "admin")
PASSWORD = os.getenv("PANEL_PASS", "")

LOGIN_URL = f"{PANEL_URL}/{PANEL_PATH}/login"
LIST_URL = f"{PANEL_URL}/{PANEL_PATH}/panel/api/inbounds/list"

s = requests.Session()
resp = s.post(LOGIN_URL, data={"username": USERNAME, "password": PASSWORD}, timeout=10)
print(f"Login Status: {resp.status_code}")

resp = s.get(LIST_URL, timeout=15)
data = resp.json()
if not data.get("success"):
    print("API Error:", data)
    raise SystemExit(2)

print("--- Inbounds ---")
for obj in data.get("obj", []) or []:
    try:
        settings = json.loads(obj.get("settings", "{}"))
        clients = settings.get("clients", []) or []
    except Exception:
        clients = []
    print(f"ID: {obj.get('id')} | Port: {obj.get('port')} | Protocol: {obj.get('protocol')} | Enable: {obj.get('enable')} | Clients: {len(clients)}")
"""
        # Write remote script
        stdin, stdout, stderr = client.exec_command("cat > /root/debug_inbounds.py <<EOF\n" + remote_script + "\nEOF")
        if stderr.read():
             print("Error writing script")
        
        # Run remote script
        stdin, stdout, stderr = client.exec_command("python3 /root/debug_inbounds.py")
        print(stdout.read().decode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    debug_panel()
