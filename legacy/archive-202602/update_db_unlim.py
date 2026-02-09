
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from portal_bot.bot import User, Base

DATABASE_URL = "sqlite:///portal.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Set all users to 0 GB (Unlimited) if they are not specifically limited/trial
# Actually, let's just set ALL to 0 for now as we pivoted to Unlimited.
# Even trials might be simply time-limited?
# But Trial plan says "30GB".
# Let's update all EXCEPT 'trial' in sub_type
# Check current values
users = session.query(User).all()
count_updated = 0
for u in users:
    if u.sub_type and 'TRIAL' in u.sub_type.upper():
        continue # Skip trials
    if u.total_gb != 0:
        print(f"Updating {u.tg_id} ({u.sub_type}): {u.total_gb} -> 0 GB")
        u.total_gb = 0
        count_updated += 1

session.commit()
print(f"Updated {count_updated} users to Unlimited (0 GB).")
session.close()
