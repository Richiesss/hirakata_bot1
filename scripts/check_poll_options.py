#!/usr/bin/env python3
"""投票選択肢を確認"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, Poll, PollOption

def check_poll_options():
    print("=== 投票選択肢確認 ===\n")
    
    with get_db() as db:
        # 最新の公開投票を取得
        poll = db.query(Poll).filter(
            Poll.status == 'published'
        ).order_by(Poll.created_at.desc()).first()
        
        if not poll:
            print("❌ 公開中の投票はありません")
            return
            
        print(f"最新の公開投票: ID {poll.id} - {poll.title}")
        
        options = db.query(PollOption).filter(
            PollOption.poll_id == poll.id
        ).order_by(PollOption.option_order).all()
        
        print(f"選択肢数: {len(options)}")
        for opt in options:
            print(f"  Order: {opt.option_order}, ID: {opt.id}, Text: {opt.option_text}")

if __name__ == "__main__":
    check_poll_options()
