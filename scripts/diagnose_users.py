#!/usr/bin/env python3
"""詳細なユーザー登録診断"""

import sys
sys.path.insert(0, '/home/hirakata_bot1')

from database.db_manager import get_db, User, ChatSession, Opinion, PollResponse
from datetime import datetime

def detailed_user_diagnosis():
    """詳細なユーザー診断"""
    print("="*60)
    print("ユーザー登録診断レポート")
    print("="*60)
    
    with get_db() as db:
        users = db.query(User).order_by(User.created_at).all()
        
        print(f"\n【データベースのユーザー数】: {len(users)}")
        print(f"【LINE公式アカウントの友だち数】: 9人")
        print(f"【差分】: {9 - len(users)}人が未登録\n")
        
        print("="*60)
        print("登録済みユーザーの詳細")
        print("="*60)
        
        for i, user in enumerate(users, 1):
            print(f"\n【ユーザー {i}】")
            print(f"  DB ID: {user.id}")
            print(f"  LINE User ID: {user.line_user_id}")
            print(f"  LINE User ID Hash: {user.line_user_id_hash[:20]}...")
            print(f"  Display Name: {user.display_name}")
            print(f"  Total Points: {user.total_points}")
            print(f"  Notification Enabled: {user.notification_enabled}")
            print(f"  Created At: {user.created_at}")
            print(f"  Updated At: {user.updated_at}")
            
            # ユーザーのアクティビティ
            chat_sessions = db.query(ChatSession).filter(
                ChatSession.user_id == user.id
            ).count()
            opinions = db.query(Opinion).filter(
                Opinion.user_id == user.id
            ).count()
            poll_responses = db.query(PollResponse).filter(
                PollResponse.user_id == user.id
            ).count()
            
            print(f"\n  【アクティビティ】")
            print(f"    - 対話セッション: {chat_sessions}件")
            print(f"    - 意見投稿: {opinions}件")
            print(f"    - 投票回答: {poll_responses}件")
        
        print("\n" + "="*60)
        print("問題の可能性")
        print("="*60)
        print("""
1. 友だち追加イベントが処理されていない
   → Webhookが正しく設定されていない可能性
   → アプリケーションが起動していなかった期間がある

2. データベース接続の問題
   → 複数のデータベースファイルが存在する可能性
   → PostgreSQLとSQLiteが混在している可能性

3. 友だち追加前にアプリケーションが起動していなかった
   → 過去に追加された友だちのイベントは再送されない
        """)

if __name__ == "__main__":
    detailed_user_diagnosis()
