
import os
import paramiko

hostname = os.getenv("SSH_HOST", "")
port = int(os.getenv("SSH_PORT", "22"))
username = os.getenv("SSH_USER", "root")
password = os.getenv("SSH_PASS", "")
if not hostname or not password:
    raise SystemExit("Set SSH_HOST and SSH_PASS (and optionally SSH_PORT/SSH_USER) in your environment")

def get_debug_info():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {hostname}...")
        client.connect(hostname, port=port, username=username, password=password, timeout=10)
        
        print("\n--- API Logs (Last 50 lines) ---")
        stdin, stdout, stderr = client.exec_command("journalctl -u portal-api -n 50 --no-pager")
        print(stdout.read().decode())
        
        print("\n--- BOT Logs (Last 50 lines) ---")
        stdin, stdout, stderr = client.exec_command("journalctl -u portal-bot -n 50 --no-pager")
        log_content = stdout.read().decode('utf-8', errors='replace')
        try:
            print(log_content)
        except UnicodeEncodeError:
            print(log_content.encode('utf-8').decode('cp1251', errors='ignore')) # Fallback for Windows console
        
        print("\n--- Running Python Processes ---")
        stdin, stdout, stderr = client.exec_command("ps aux | grep python")
        print(stdout.read().decode())

        print("\n--- Check Panel Port (15739) ---")
        stdin, stdout, stderr = client.exec_command("netstat -tulpn | grep 15739")
        print(stdout.read().decode())
        
        print("\n--- Check API Port (2096) ---")
        stdin, stdout, stderr = client.exec_command("netstat -tulpn | grep 2096")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    get_debug_info()
