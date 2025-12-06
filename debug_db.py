import sys
import os
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from database.db_manager import get_db, Poll
from features.poll_manager import create_poll

print(f"Testing DB connection at {datetime.now()}...")

try:
    with get_db() as db:
        # Simple query
        count = db.query(Poll).count()
        print(f"Current poll count: {count}")
        
    print("DB connection successful.")
    
    print("Testing create_poll...")
    poll_id = create_poll(
        question="Debug Poll",
        choices=["A", "B", "C", "D"],
        description="Created by debug script"
    )
    print(f"Poll created successfully: {poll_id}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
