
import os
import paramiko

hostname = os.getenv("SSH_HOST", "")
port = int(os.getenv("SSH_PORT", "22"))
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

def cleanup():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        
        print("\n--- Searching for service running kiwunaka_bot.py... ---")
        # Grep in systemd directory
        cmd = "grep -r 'kiwunaka_bot.py' /etc/systemd/system/"
        stdin, stdout, stderr = client.exec_command(cmd)
        services = stdout.read().decode().strip().split('\n')
        
        found_service = None
        for line in services:
            if line:
                print(f"Match: {line}")
                # Extract filename
                # usually /etc/systemd/system/servicename.service:ExecStart=...
                parts = line.split(':')
                if len(parts) > 0:
                    svc_path = parts[0]
                    svc_name = svc_path.split('/')[-1]
                    found_service = svc_name
        
        if found_service:
            print(f"\n!!! Found conflicting service: {found_service}")
            print(f"--- Stopping and disabling {found_service}...")
            client.exec_command(f"systemctl stop {found_service}")
            client.exec_command(f"systemctl disable {found_service}")
            print("Done: Service disabled.")
        else:
            print("\n--- No specific service file found (maybe running manually or via cron?).")
            
        print("\n--- Killing kiwunaka_bot.py process... ---")
        client.exec_command("pkill -9 -f kiwunaka_bot.py")
        print("Done: Process killed.")
        
        print("\n--- Restarting portal-bot to be sure... ---")
        client.exec_command("systemctl restart portal-bot")
        print("Done: portal-bot restarted.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    cleanup()
