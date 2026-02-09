import os
import requests
import json
import logging
import time

# --- Configuration ---
PANEL_URL = os.getenv("PANEL_URL", "http://127.0.0.1:15739")
PANEL_USER = os.getenv("PANEL_USER", "admin")
PANEL_PASS = os.getenv("PANEL_PASS", "")
PANEL_PATH = os.getenv("PANEL_PATH", "")
if not PANEL_PATH:
    raise SystemExit("Set PANEL_PATH in your environment")
INBOUND_MAIN = 4
INBOUND_BACKUP = 6

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PanelSync:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = f"{PANEL_URL.rstrip('/')}/{PANEL_PATH.strip('/')}/panel/api/inbounds"

    def login(self):
        login_url = f"{PANEL_URL.rstrip('/')}/{PANEL_PATH.strip('/')}/login"
        payload = {"username": PANEL_USER, "password": PANEL_PASS}
        try:
            resp = self.session.post(login_url, data=payload, timeout=10)
            if resp.status_code == 200 and resp.json().get("success"):
                logger.info("Login successful")
                return True
            logger.error(f"Login failed: Status={resp.status_code}, Response={resp.text}")
        except Exception as e:
            logger.error(f"Login error: {e}")
        return False

    def get_inbound_clients(self, inbound_id):
        try:
            resp = self.session.get(f"{self.base_url}/list", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    for inb in data.get("obj", []):
                        if inb.get("id") == inbound_id:
                            settings = json.loads(inb.get("settings", "{}"))
                            return settings.get("clients", [])
            logger.error("Failed to list inbounds")
        except Exception as e:
            logger.error(f"Get clients error: {e}")
        return []

    def add_client_to_backup(self, client):
        # Modify email for backup
        backup_client = client.copy()
        original_email = client.get("email")
        backup_email = f"{original_email}_ozon"
        backup_client["email"] = backup_email
        backup_client["totalGB"] = 0 # Unlimited for backup
        
        # Reset Main Client to Unlimited too
        client["totalGB"] = 0
        try:
             # Update Main
             payload_main = {
                "id": INBOUND_MAIN,
                "settings": json.dumps({"clients": [client]})
             }
             self.session.post(f"{self.base_url}/updateClient/{client['id']}", json=payload_main, timeout=10)
             logger.info(f"OK: Reset limit for main: {original_email}")
        except Exception as e:
             logger.warning(f"Failed to reset main limit: {e}")

        payload = {
            "id": INBOUND_BACKUP,
            "settings": json.dumps({"clients": [backup_client]})
        }
        
        try:
            resp = self.session.post(f"{self.base_url}/addClient", json=payload, timeout=10)
            if resp.status_code == 200 and resp.json().get("success"):
                logger.info(f"OK: Synced: {original_email} -> {backup_email}")
                return True
            else:
                logger.warning(f"FAIL: Failed to sync {original_email}: {resp.text}")
        except Exception as e:
            logger.error(f"Add client error: {e}")
        return False

    def run(self):
        if not self.login():
            return

        logger.info(f"Fetching clients from Main Inbound {INBOUND_MAIN}...")
        main_clients = self.get_inbound_clients(INBOUND_MAIN)
        logger.info(f"Found {len(main_clients)} clients on Main.")

        logger.info(f"Fetching clients from Backup Inbound {INBOUND_BACKUP}...")
        backup_clients = self.get_inbound_clients(INBOUND_BACKUP)
        backup_emails = {c.get("email") for c in backup_clients}
        
        logger.info("Starting Sync...")
        synced_count = 0
        for client in main_clients:
            email = client.get("email")
            target_email = f"{email}_ozon"
            
            if target_email in backup_emails:
                logger.info(f"Skipping {email} (already exists)")
                continue
                
            logger.info(f"Syncing {email}...")
            if self.add_client_to_backup(client):
                synced_count += 1
            
            time.sleep(0.5) # Be gentle
            
        logger.info(f"Sync complete. Added {synced_count} clients.")

if __name__ == "__main__":
    syncer = PanelSync()
    syncer.run()
