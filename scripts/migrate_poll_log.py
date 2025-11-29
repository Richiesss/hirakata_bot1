#!/usr/bin/env python3
"""データベースマイグレーション: PollDeliveryLogテーブル作成"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import engine, Base, PollDeliveryLog

def migrate():
    """テーブル作成"""
    print("Creating PollDeliveryLog table...")
    PollDeliveryLog.__table__.create(bind=engine)
    print("Done.")

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Error: {e}")
