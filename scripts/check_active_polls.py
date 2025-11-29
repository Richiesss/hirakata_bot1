#!/usr/bin/env python3
"""公開中の投票を確認"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, Poll

def check_active_polls():
    print("=== 公開中の投票確認 ===\n")
    
    with get_db() as db:
        polls = db.query(Poll).filter(Poll.status == 'published').all()
        
        if not polls:
            print("❌ 公開中の投票はありません")
            # 全ての投票を表示
            all_polls = db.query(Poll).all()
            print(f"\n全投票数: {len(all_polls)}")
            for p in all_polls:
                print(f"  ID: {p.id}, Status: {p.status}, Title: {p.title}")
        else:
            print(f"✅ 公開中の投票: {len(polls)}件")
            for p in polls:
                print(f"  ID: {p.id}, Title: {p.title}")

if __name__ == "__main__":
    check_active_polls()
