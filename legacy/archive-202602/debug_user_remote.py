
import sqlite3
import sys

try:
    conn = sqlite3.connect('/root/portal_bot/portal.db')
    c = conn.cursor()

    # Find user by part of token
    token_part = "gGnZE"
    print(f"Searching for user with token part: {token_part}")
    c.execute("SELECT tg_id, username, total_gb, sub_type, sub_token FROM users WHERE sub_token LIKE ?", (token_part + '%',))
    user = c.fetchone()

    if user:
        print(f"Found user: ID={user[0]}, Name={user[1]}, TotalGB={user[2]}, SubType={user[3]}")
        if user[2] != 0:
            print("User has non-zero limit! Fixing to 0...")
            c.execute("UPDATE users SET total_gb = 0 WHERE tg_id = ?", (user[0],))
            conn.commit()
            print("Fixed.")
        else:
            print("User already has TotalGB=0.")
    else:
        print("User not found.")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
