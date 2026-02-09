
import paramiko
import os
import json

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
    
    # Get inbounds from x-ui directly (since we can't easily auth session via script without duplication)
    # Actually let's just use the api call if we can, but easier is to query the DB?
    # No, let's just check the bot's logs or run a small snippet to list inbounds.
    
    stdin, stdout, stderr = client.exec_command('sqlite3 /etc/x-ui/x-ui.db "SELECT value FROM settings WHERE key = \'xrayRouting\';"')
    print("Xray Routing Settings:")
    print(stdout.read().decode())
    
    client.close()
except Exception as e:
    print(f"Error: {e}")
