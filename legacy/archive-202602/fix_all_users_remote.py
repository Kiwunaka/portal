
import sqlite3
import sys

try:
    conn = sqlite3.connect('/root/portal_bot/portal.db')
    c = conn.cursor()

    print("Scanning all users...")
    c.execute("SELECT tg_id, username, total_gb, sub_type FROM users")
    users = c.fetchall()
    
    updated_count = 0
    skipped_trial = 0
    already_unlimited = 0
    
    for u in users:
        tg_id, username, total_gb, sub_type = u
        sub_type_str = str(sub_type).upper() if sub_type else ""
        
        if 'TRIAL' in sub_type_str:
            skipped_trial += 1
            continue
            
        if total_gb != 0:
            print(f"Fixing User: ID={tg_id}, Name={username}, Type={sub_type}, GB={total_gb} -> 0")
            c.execute("UPDATE users SET total_gb = 0 WHERE tg_id = ?", (tg_id,))
            updated_count += 1
        else:
            already_unlimited += 1
            
    conn.commit()
    print("-" * 30)
    print(f"Summary:")
    print(f"Updated to Unlimited: {updated_count}")
    print(f"Skipped (Trial): {skipped_trial}")
    print(f"Already Unlimited: {already_unlimited}")
    print(f"Total Users: {len(users)}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
