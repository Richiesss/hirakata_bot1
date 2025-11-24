#!/usr/bin/env python3
"""ユーザーデータを確認するスクリプト"""

import sys
import os

# パスを追加
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, User, Poll

def check_users():
    """ユーザーデータを確認"""
    print("=== ユーザーデータ確認 ===\n")
    
    with get_db() as db:
        users = db.query(User).all()
        
        print(f"総ユーザー数: {len(users)}\n")
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"  line_user_id: {user.line_user_id}")
            print(f"  line_user_id_hash: {user.line_user_id_hash[:16]}...")
            print(f"  notification_enabled: {user.notification_enabled}")
            print(f"  display_name: {user.display_name}")
            print(f"  total_points: {user.total_points}")
            print(f"  created_at: {user.created_at}")
            print()
        
        # notification_enabled = Trueでline_user_idがあるユーザー
        notifiable_users = db.query(User).filter(
            User.notification_enabled == True,
            User.line_user_id != None
        ).all()
        
        print(f"\n通知可能ユーザー数: {len(notifiable_users)}")
        
        # 投票データも確認
        polls = db.query(Poll).all()
        print(f"\n総投票数: {len(polls)}")
        for poll in polls:
            print(f"  - Poll ID: {poll.id}, Title: {poll.title}, Status: {poll.status}")

if __name__ == "__main__":
    try:
        check_users()
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
