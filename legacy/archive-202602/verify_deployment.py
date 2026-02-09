
import os
import paramiko
import sys
import json

hostname = os.getenv("SSH_HOST", "")
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
port = int(os.getenv("SSH_PORT", "22"))
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

def verify():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, port=port, username=username, password=password)
        
        # 1. Get a valid token
        print("Getting valid token from DB...")
        stdin, stdout, stderr = client.exec_command('sqlite3 /root/portal_bot/portal.db "SELECT sub_token FROM users WHERE is_active=1 LIMIT 1;"')
        token = stdout.read().decode().strip()
        
        if not token:
            print("No active users found to test with.")
            return

        print(f"Testing with token: {token[:10]}...")

        # 2. Test Hiddify (Smart)
        print("\n--- TEST 1: Hiddify (Smart Client) ---")
        cmd_smart = f'curl -k -s -H "User-Agent: Hiddify/1.0" https://127.0.0.1:2096/s8Kx2mP7qR4wT/{token}'
        stdin, stdout, stderr = client.exec_command(cmd_smart)
        resp_smart = stdout.read().decode()
        
        try:
            data = json.loads(resp_smart)
            print("SUCCESS: Received JSON!")
            print(f"Outbounds: {[o['tag'] for o in data.get('outbounds', [])]}")
            
            tags = [o.get("tag") for o in data.get("outbounds", [])]
            if "proxy" in tags and any(t and str(t).startswith("proxy_") for t in tags):
                print("SUCCESS: Multi-node selector/outbounds look present (tag='proxy', 'proxy_*')")
            else:
                print("FAILED: Expected selector/outbounds tags not found")
            
            # Check for direct rules
            rules = data.get('route', {}).get('rules', [])
            steam_rule = next((r for r in rules if 'steam' in r.get('geosite', []) and r.get('outbound') == 'direct'), None)
            bt_rule = next((r for r in rules if r.get('protocol') == 'bittorrent' and r.get('outbound') == 'direct'), None)
            
            if steam_rule:
                print("Steam rule found: DIRECT")
            else:
                print("Steam rule MISSING")
                
            if bt_rule:
                 print("BitTorrent rule found: DIRECT")
            else:
                 print("BitTorrent rule MISSING")
                 
        except json.JSONDecodeError:
            print(f"FAILED: Response is not JSON.\n{resp_smart[:200]}")

        # 3. Test Legacy (v2rayN)
        print("\n--- TEST 2: v2rayN (Legacy Client) ---")
        cmd_legacy = f'curl -k -s -H "User-Agent: Go-http-client/1.1" https://127.0.0.1:2096/s8Kx2mP7qR4wT/{token}'
        stdin, stdout, stderr = client.exec_command(cmd_legacy)
        resp_legacy = stdout.read().decode()
        
        if resp_legacy.startswith("vless://") or (len(resp_legacy) > 20 and "vless://" not in resp_legacy): # Base64
            print("SUCCESS: Received VLESS List (Legacy format)")
        else:
            print(f"UNEXPECTED: {resp_legacy[:100]}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    verify()
