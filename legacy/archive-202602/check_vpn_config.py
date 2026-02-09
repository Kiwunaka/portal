import os
import paramiko
import sys
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

hostname = os.getenv("SSH_HOST", "")
port = int(os.getenv("SSH_PORT", "22"))
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"Connecting to {hostname}:{port}...")
    client.connect(hostname, port=port, username=username, password=password, timeout=30)
    
    cmd = "sqlite3 /etc/x-ui/x-ui.db \"SELECT id, port, protocol, stream_settings FROM inbounds\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    rows = stdout.read().decode().strip().split('\n')
    
    print("-" * 50)
    for row in rows:
        if not row: continue
        parts = row.split('|')
        if len(parts) < 4: continue
        
        iid = parts[0]
        iport = parts[1]
        iprotocol = parts[2]
        isettings = parts[3]
        
        try:
            settings_json = json.loads(isettings)
            reality = settings_json.get('realitySettings', {})
            sni = reality.get('serverNames', 'N/A')
            dest = reality.get('dest', 'N/A')
            print(f"ID: {iid} | Port: {iport} | Proto: {iprotocol}")
            print(f"Strange Settings: SNI={sni}, Dest={dest}")
        except:
            print(f"ID: {iid} | Port: {iport} | Proto: {iprotocol} | (Parse Error)")
        print("-" * 50)
        
    client.close()

except Exception as e:
    print(f"Error: {e}")
