
import sqlite3
import json

try:
    # 3x-ui standard DB path
    db_path = "/etc/x-ui/x-ui.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    inbound_id = 6
    print(f"Fetching Inbound {inbound_id} from {db_path}...")
    c.execute("SELECT port, protocol, settings, stream_settings, remark FROM inbounds WHERE id=?", (inbound_id,))
    row = c.fetchone()
    
    if row:
        port, protocol, settings, stream_settings, remark = row
        print(f"ID: {inbound_id}")
        print(f"Remark: {remark}")
        print(f"Port: {port}")
        print(f"Protocol: {protocol}")
        
        # Parse JSON to find Keys
        try:
            stream_json = json.loads(stream_settings)
            print("\n--- Stream Settings ---")
            reality = stream_json.get('realitySettings', {})
            print(f"Security: {stream_json.get('security')}")
            print(f"Network: {stream_json.get('network')}")
            
            if stream_json.get('security') == 'reality':
                print(f"ShortIds: {reality.get('shortIds')}")
                # Private key is hidden typically? No, in DB it's there usually for server.
                # But we need PUBLIC key for client. Public key might not be stored if only Private is stored?
                # Usually logic derives Public from Private, or stores both.
                # Let's print keys if present
                settings_obj = reality.get('settings', {}) # structure varies
                print(f"ServerNames: {reality.get('serverNames')}")
                print(f"Dest: {reality.get('dest')}")
                print(f"PrivateKey: {reality.get('privateKey')}")
                # We need Public Key for the client link! 
                # If only Private Key is in DB, we'd need to calculate Public, OR user must provide it.
                # Wait, X-UI stores generated settings.
                
        except Exception as e:
            print(f"JSON Error: {e}")
            print(f"Raw Stream: {stream_settings}")

    else:
        print(f"Inbound {inbound_id} NOT found!")
        
    conn.close()
    
except Exception as e:
    print(f"DB Error: {e}")
